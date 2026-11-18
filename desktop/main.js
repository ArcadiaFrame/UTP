/* UTP desktop shell: starts the UTP server (Python, standard library only) and shows it in a window.
   The window is the same app the browser shows; closing the window stops the server. */
const { app, BrowserWindow, shell, dialog, Menu } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

// The repository: next to this folder when run from source, or bundled as "repo" in a packaged app.
const REPO = [path.join(process.resourcesPath || "", "repo"), path.resolve(__dirname, "..")]
  .find(p => fs.existsSync(path.join(p, "utp", "app", "server.py")));
const PYTHONS = process.env.UTP_PYTHON ? [process.env.UTP_PYTHON] : process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"];
const args = process.argv.slice(app.isPackaged ? 1 : 2);
const pick = name => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
let server = null, win = null;

function startServer() {
  return new Promise((resolve, reject) => {
    const extra = [];
    if (pick("--language")) extra.push("--language", pick("--language"));
    const tryNext = i => {
      if (i >= PYTHONS.length) return reject(new Error("Python 3 was not found. Install Python 3.8 or newer, or set UTP_PYTHON to its path."));
      const p = spawn(PYTHONS[i], [path.join(REPO, "utp", "app", "server.py"), "--port", "0", "--print-port", ...extra],
                      { cwd: REPO, env: { ...process.env, PYTHONUNBUFFERED: "1" } });
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
  let port;
  try { port = await startServer(); }
  catch (e) { dialog.showErrorBox("UTP could not start", e.message); app.quit(); return; }
  win = new BrowserWindow({
    width: 1360, height: 880, minWidth: 900, minHeight: 600, title: "UTP", backgroundColor: "#f6f5f2",
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  const lang = pick("--language"), page = pick("--page");
  let url = `http://127.0.0.1:${port}/` + (lang ? `#lang=${encodeURIComponent(lang)}` : "");
  win.loadURL(url);
  // links to other sites open in the normal browser; the app's own pages stay in the window
  win.webContents.setWindowOpenHandler(({ url: u }) => {
    if (u.startsWith(`http://127.0.0.1:${port}/`)) return { action: "allow" };
    shell.openExternal(u); return { action: "deny" };
  });
  win.webContents.on("will-navigate", (e, u) => { if (!u.startsWith(`http://127.0.0.1:${port}/`)) { e.preventDefault(); shell.openExternal(u); } });
  if (page && lang) win.webContents.once("did-finish-load", () =>
    win.webContents.executeJavaScript(`setTimeout(() => runCommand("/${page === "course" ? "course" : "lab"} ${lang}"), 600)`));
}

Menu.setApplicationMenu(Menu.buildFromTemplate([
  ...(process.platform === "darwin" ? [{ role: "appMenu" }] : []),
  { role: "fileMenu" }, { role: "editMenu" }, { role: "viewMenu" }, { role: "windowMenu" },
]));
app.whenReady().then(createWindow);
app.on("window-all-closed", () => app.quit());
app.on("quit", () => { if (server) server.kill(); });
app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
