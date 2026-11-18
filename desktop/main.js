/* UTP desktop shell: starts the UTP server (Python, standard library only) and shows it in a window.
   The window is the same app the browser shows; closing the window stops the server. */
const { app, BrowserWindow, shell, dialog, Menu, nativeTheme } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

// The repository: next to this folder when run from source, or bundled as "repo" in a packaged app.
const REPO = [path.join(process.resourcesPath || "", "repo"), path.resolve(__dirname, "..")]
  .find(p => fs.existsSync(path.join(p, "utp", "app", "server.py")));
// Settings live in ~/.utp/config.json (or $UTP_HOME/config.json); the Settings page can name the Python to use.
const CONFIG = path.join(process.env.UTP_HOME || path.join(require("os").homedir(), ".utp"), "config.json");
function saved() { try { return JSON.parse(fs.readFileSync(CONFIG, "utf8")); } catch (e) { return {}; } }
function savedPython() { return (saved().desktop || {}).python || null; }
function syncTheme() { const t = (saved().app || {}).theme; nativeTheme.themeSource = ["light", "dark"].includes(t) ? t : "system"; }
const PYTHONS = [process.env.UTP_PYTHON, savedPython(), ...(process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"])].filter(Boolean);
const args = process.argv.slice(app.isPackaged ? 1 : 2);
const pick = name => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
let server = null, win = null;

function startServer() {
  return new Promise((resolve, reject) => {
    const extra = [];
    const tryNext = i => {
      if (i >= PYTHONS.length) return reject(new Error("Python 3 was not found. Install Python 3.8 or newer, or put its path in Settings > Startup (saved in " + CONFIG + ")."));
      const p = spawn(PYTHONS[i], [path.join(REPO, "utp", "app", "server.py"), "--port", "0", "--print-port", ...extra],
                      { cwd: REPO, env: { ...process.env, PYTHONUNBUFFERED: "1", UTP_MODE: "desktop window" } });
      let out = "", done = false;
      p.on("error", () => { if (!done) { done = true; tryNext(i + 1); } });
      p.stdout.on("data", d => {
        out += d.toString();
        const m = out.match(/UTP_PORT=(\d+)/);
        if (m && !done) { done = true; server = p; resolve(Number(m[1])); }
      });
      p.stderr.on("data", d => process.stderr.write(d));
      p.on("exit", code => { if (!done) { done = true; code === 9009 || code === 127 ? tryNext(i + 1) : reject(new Error(`the UTP server stopped (exit ${code})`)); } });
    };
    tryNext(0);
  });
}

async function createWindow() {
  syncTheme();
  let port;
  try { port = await startServer(); }
  catch (e) { dialog.showErrorBox("UTP could not start", e.message); app.quit(); return; }
  win = new BrowserWindow({
    width: 1360, height: 880, minWidth: 900, minHeight: 600, title: "UTP", backgroundColor: nativeTheme.shouldUseDarkColors ? "#171514" : "#f6f5f2",
    icon: path.join(__dirname, "icon.png"),
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  const lang = pick("--language"), page = pick("--page");
  const hash = [lang && `lang=${encodeURIComponent(lang)}`, lang && page && `page=${page === "course" ? "course" : "lab"}`].filter(Boolean).join("&");
  try { fs.watch(path.dirname(CONFIG), () => syncTheme()); } catch (e) { }
  win.loadURL(`http://127.0.0.1:${port}/` + (args.includes("--settings") ? "#settings" : hash ? "#" + hash : ""));
  // links to other sites open in the normal browser; the app's own pages stay in the window
  win.webContents.setWindowOpenHandler(({ url: u }) => {
    if (u.startsWith(`http://127.0.0.1:${port}/`)) return { action: "allow" };
    shell.openExternal(u); return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, u) => { if (!u.startsWith(`http://127.0.0.1:${port}/`)) { e.preventDefault(); shell.openExternal(u); } });
}

const openSettings = () => { if (win) win.webContents.executeJavaScript("openSettings()"); };
const settingsItem = { label: "Settings…", accelerator: "CmdOrCtrl+,", click: openSettings };
Menu.setApplicationMenu(Menu.buildFromTemplate([
  ...(process.platform === "darwin" ? [{ label: app.name, submenu: [{ role: "about" }, { type: "separator" }, settingsItem,
    { type: "separator" }, { role: "hide" }, { role: "hideOthers" }, { role: "unhide" }, { type: "separator" }, { role: "quit" }] }] : []),
  { label: "File", submenu: [...(process.platform === "darwin" ? [] : [settingsItem, { type: "separator" }]),
    { label: "Open in browser", click: () => win && shell.openExternal(win.webContents.getURL()) }, { type: "separator" },
    process.platform === "darwin" ? { role: "close" } : { role: "quit" }] },
  { role: "editMenu" }, { role: "viewMenu" }, { role: "windowMenu" },
]));
app.whenReady().then(createWindow);
app.on("window-all-closed", () => app.quit());
app.on("quit", () => { if (server) server.kill(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
