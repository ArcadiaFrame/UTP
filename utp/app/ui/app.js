/* UTP app: languages and files on the left, chat and opened files on the right. Talks only to the local server. */
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const md = text => DOMPurify.sanitize(marked.parse(text || "", {gfm: true, breaks: false}));

const S = {langs: [], lang: "", mode: "assistant", history: [], attached: [], tabs: [{id: "chat", title: "Chat"}], active: "chat", files: {}};

async function api(path, body) {
  const r = await fetch(path, body === undefined ? {} : {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  const j = await r.json().catch(() => ({error: r.statusText}));
  if (!r.ok || j.error) throw new Error(j.error || r.statusText);
  return j;
}
async function stream(path, body, on) {
  const r = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.error || r.statusText); }
  const reader = r.body.getReader(), dec = new TextDecoder(); let buf = "";
  for (;;) {
    const {done, value} = await reader.read(); if (done) break;
    buf += dec.decode(value, {stream: true});
    let i; while ((i = buf.indexOf("\n\n")) >= 0) {
      const line = buf.slice(0, i).split("\n").find(l => l.startsWith("data:")); buf = buf.slice(i + 2);
      if (!line) continue;
      const ev = JSON.parse(line.slice(5));
      if (ev.error) throw new Error(ev.error);
      on(ev);
    }
  }
}

/* ---------- languages ---------- */
async function loadLanguages() {
  try { S.langs = (await api("/api/languages")).languages; } catch (e) { S.langs = []; }
  const visible = S.langs.filter(l => !l.fixture || S.langs.length === 1);
  $("#langs").innerHTML = visible.map(l => {
    const p = l.pages || {}, acts = [];
    if (p.utp_lab) acts.push(`<a href="#" data-open="${esc(p.utp_lab)}">Lab</a>`);
    if (p.lab && p.lab !== p.utp_lab) acts.push(`<a href="#" data-open="${esc(p.lab)}">${l.id === "vulcan" ? "Vuhlkansu Lab" : "Lab (own)"}</a>`);
    if (p.course) acts.push(`<a href="#" data-open="${esc(p.course)}">Course</a>`);
    if (l.expandable && p.utp_lab) acts.push(`<a href="#" data-open="${esc(p.utp_lab)}" data-hash="grow">Grow</a>`);
    acts.push(`<a href="#" data-folder="${esc(l.home)}">Folder</a>`);
    if (l.expandable) acts.push(`<a href="#" data-rebuild="${esc(l.id)}">Rebuild</a>`);
    return `<li class="lang ${S.lang === l.id ? "active" : ""}" data-lang="${esc(l.id)}">
      <div class="name"><span>${esc(l.language || l.id)}</span><span class="count">${(l.entries || 0).toLocaleString()}</span></div>
      <div class="acts">${acts.join("")}</div></li>`;
  }).join("") || '<li class="muted">No languages yet.</li>';
  $("#chat-lang").innerHTML = '<option value="">None</option>' + visible.map(l => `<option value="${esc(l.id)}">${esc(l.language || l.id)}</option>`).join("");
  $("#chat-lang").value = S.lang;
}
function selectLanguage(id) {
  S.lang = id; $("#chat-lang").value = id;
  document.querySelectorAll(".lang").forEach(li => li.classList.toggle("active", li.dataset.lang === id));
}
$("#langs").addEventListener("click", async e => {
  const a = e.target.closest("a"); const li = e.target.closest(".lang");
  if (a) {
    e.preventDefault();
    if (a.dataset.open) openFile(a.dataset.open, a.dataset.hash);
    if (a.dataset.folder) revealFolder(a.dataset.folder);
    if (a.dataset.rebuild) runCommand(`/build ${a.dataset.rebuild}`);
    return;
  }
  if (li) selectLanguage(li.dataset.lang);
});
$("#chat-lang").onchange = e => selectLanguage(e.target.value);
$("#chat-mode").onchange = e => { S.mode = e.target.value; };

/* ---------- files ---------- */
const ICON = {md: "md", csv: "csv", json: "{}", py: "py", html: "web", js: "js", css: "css", txt: "txt", pdf: "pdf"};
async function loadTree(path, el) {
  const r = await api(`/api/tree?path=${encodeURIComponent(path)}`);
  el.innerHTML = r.entries.map(n => `<div class="item" data-path="${esc(n.path)}" data-dir="${n.dir}">
    <div class="node" role="treeitem" tabindex="0"><span class="tw">${n.dir ? "▸" : ""}</span><span class="ic">${n.dir ? "" : esc(ICON[n.name.split(".").pop()] || "")}</span><span>${esc(n.name)}</span></div>
    ${n.dir ? '<div class="kids" hidden></div>' : ""}</div>`).join("");
}
async function toggle(item, open) {
  const kids = item.querySelector(":scope > .kids"); if (!kids) return;
  const show = open ?? kids.hidden;
  if (show && !kids.dataset.loaded) { await loadTree(item.dataset.path, kids); kids.dataset.loaded = "1"; }
  kids.hidden = !show; item.querySelector(".tw").textContent = show ? "▾" : "▸";
}
$("#tree").addEventListener("click", e => {
  const item = e.target.closest(".item"); if (!item) return;
  if (item.dataset.dir === "true") toggle(item); else openFile(item.dataset.path);
});
$("#tree").addEventListener("keydown", e => { if (e.key === "Enter") e.target.click(); });
async function revealFolder(path) {
  const parts = path.split("/"); let el = $("#tree");
  for (let i = 1; i <= parts.length; i++) {
    const item = [...el.querySelectorAll(":scope > .item")].find(x => x.dataset.path === parts.slice(0, i).join("/"));
    if (!item) return;
    await toggle(item, true); el = item.querySelector(":scope > .kids");
    if (i === parts.length) item.scrollIntoView({block: "nearest"});
  }
}
$("#refresh").onclick = () => { loadTree("", $("#tree")); loadLanguages(); };

/* ---------- tabs ---------- */
function drawTabs() {
  $("#tabs").innerHTML = S.tabs.map(t => `<div class="tab" role="tab" data-tab="${esc(t.id)}" aria-selected="${t.id === S.active}" title="${esc(t.id)}">
    <span>${esc(t.title)}</span>${t.id === "chat" ? "" : `<button class="x" data-close="${esc(t.id)}" aria-label="Close">×</button>`}</div>`).join("");
}
function activate(id) {
  S.active = id; drawTabs();
  $("#chat-view").hidden = id !== "chat"; $("#file-view").hidden = id === "chat" || id === "settings";
  $("#settings-view").hidden = id !== "settings";
  if (id === "settings") renderSettings(); else if (id !== "chat") renderFile(id);
}
$("#tabs").addEventListener("click", e => {
  const c = e.target.closest("[data-close]");
  if (c) { S.tabs = S.tabs.filter(t => t.id !== c.dataset.close); delete S.files[c.dataset.close]; activate(S.active === c.dataset.close ? "chat" : S.active); return; }
  const t = e.target.closest("[data-tab]"); if (t) activate(t.dataset.tab);
});
function openFile(path, hash) {
  if (!S.tabs.some(t => t.id === path)) S.tabs.push({id: path, title: path.split("/").pop()});
  S.files[path] = {...(S.files[path] || {}), hash: hash || ""};
  activate(path);
}

/* ---------- file view ---------- */
function parseCSV(text) {
  const rows = []; let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n") { row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows;
}
async function renderFile(path) {
  const v = $("#file-view"), ext = path.split(".").pop().toLowerCase(), f = S.files[path] || {};
  const bar = actions => `<div class="file-bar"><span class="path">${esc(path)}</span>${actions}</div>`;
  const common = `<button data-act="attach">Attach to chat</button><button data-act="window">Open in browser</button>`;
  if (ext === "html" || ext === "htm") {
    v.innerHTML = bar(common + `<button data-act="reload">Reload</button>`) + `<div class="file-body flush"><iframe src="/files/${encodeURI(path)}${f.hash ? "#" + f.hash : ""}" title="${esc(path)}"></iframe></div>`;
    return bindBar(path);
  }
  let r;
  try { r = await api(`/api/file?path=${encodeURIComponent(path)}`); } catch (e) { v.innerHTML = bar("") + `<div class="file-body"><p class="note">${esc(e.message)}</p></div>`; return; }
  if (r.binary) { v.innerHTML = bar(common) + `<div class="file-body"><p class="note">Not a text file (${r.size.toLocaleString()} bytes). Open it in the browser.</p></div>`; return bindBar(path); }
  const trunc = r.truncated ? `<p class="note">Large file: the first 2 MB are shown.</p>` : "";
  const edit = r.editable ? `<button data-act="edit">Edit</button>` : "";
  let body;
  if (f.editing) {
    body = `<div class="file-body"><textarea class="editor" id="editor">${esc(r.text)}</textarea></div>`;
    v.innerHTML = bar(`<button data-act="cancel">Cancel</button><button class="primary" data-act="save">Save</button>`) + body;
    return bindBar(path, r);
  }
  if (ext === "md") body = `<div class="md">${md(r.text)}</div>`;
  else if (ext === "csv") body = csvTable(path, r.text);
  else if (ext === "json") { let t = r.text; try { t = JSON.stringify(JSON.parse(r.text), null, 2); } catch (e) {} body = `<pre class="code">${esc(t)}</pre>`; }
  else body = `<pre class="code">${esc(r.text)}</pre>`;
  const batch = isBatch(r.text) ? `<button data-act="tick">Tick all valid</button><button class="primary" data-act="apply">Add ticked words and rebuild</button>` : "";
  v.innerHTML = bar(batch + common + edit) + `<div class="file-body">${trunc}${body}<div class="log" id="file-log" hidden></div></div>`;
  bindBar(path, r);
}
const isBatch = text => /^key,gloss,pos,field,era,register,kind,parts,basis,status,why,approve/.test(text);
function csvTable(path, text) {
  const rows = parseCSV(text.trim()); if (!rows.length) return '<p class="muted">Empty.</p>';
  const head = rows[0], batch = isBatch(text), si = head.indexOf("status"), ai = head.indexOf("approve"), ki = head.indexOf("key");
  const max = 2000, note = rows.length - 1 > max ? `<p class="note">${(rows.length - 1).toLocaleString()} rows; the first ${max} are shown.</p>` : "";
  const intro = batch ? `<p class="note">A batch proposed by a model. Tick the words to keep; <b>Add ticked words and rebuild</b> adds them to the language and rebuilds its dictionary, Lab and course. Rejected rows say why.</p>` : "";
  return intro + note + `<table class="csv"><thead><tr>${batch ? "<th>Add</th>" : ""}${head.map(h => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${
    rows.slice(1, max + 1).map(r => `<tr class="${batch && r[si] === "rejected" ? "rejected" : ""}">${batch ? `<td>${r[si] === "proposed" ? `<input type="checkbox" data-key="${esc(r[ki])}" ${/^(y|yes|1|true|x)$/i.test(r[ai]) ? "checked" : ""} aria-label="add ${esc(r[ki])}">` : esc(r[si])}</td>` : ""}${r.map(c => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
function bindBar(path, r) {
  $("#file-view").querySelectorAll("[data-act]").forEach(b => b.onclick = async () => {
    const act = b.dataset.act;
    if (act === "attach") { if (!S.attached.includes(path)) S.attached.push(path); drawAttached(); activate("chat"); }
    if (act === "window") window.open(`/files/${encodeURI(path)}`, "_blank");
    if (act === "reload") renderFile(path);
    if (act === "edit") { S.files[path].editing = true; renderFile(path); }
    if (act === "cancel") { S.files[path].editing = false; renderFile(path); }
    if (act === "save") { await api("/api/file", {path, text: $("#editor").value}); S.files[path].editing = false; renderFile(path); }
    if (act === "tick") $("#file-view").querySelectorAll("input[data-key]").forEach(c => c.checked = true);
    if (act === "apply") {
      const keys = [...$("#file-view").querySelectorAll("input[data-key]:checked")].map(c => c.dataset.key);
      const lang = r && r.language || S.lang; const log = $("#file-log");
      if (!keys.length) return;
      log.hidden = false; log.textContent = `Adding ${keys.length} words to ${lang}…\n`; b.disabled = true;
      try { await stream("/api/apply", {language: lang, path, keys}, ev => { if (ev.line) log.textContent += ev.line + "\n"; if (ev.done) log.textContent += `\nAdded ${ev.added}; ${ev.errors} build errors.`; }); }
      catch (e) { log.textContent += "\n" + e.message; }
      b.disabled = false; loadLanguages();
    }
  });
}

/* ---------- chat ---------- */
function drawAttached() {
  $("#attached").innerHTML = S.attached.map(p => `<span class="chip" title="${esc(p)}">${esc(p.split("/").pop())}<button data-unattach="${esc(p)}" aria-label="Remove">×</button></span>`).join("");
}
$("#attached").onclick = e => { const b = e.target.closest("[data-unattach]"); if (b) { S.attached = S.attached.filter(p => p !== b.dataset.unattach); drawAttached(); } };
function addMsg(role, html, cls = "") {
  $("#empty") && $("#empty").remove();
  const d = document.createElement("div"); d.className = `msg ${role} ${cls}`; d.innerHTML = html;
  $("#messages").appendChild(d); $("#messages").scrollTop = 1e9; return d;
}
async function sendChat(text) {
  addMsg("user", esc(text)); S.history.push({role: "user", content: text});
  const d = addMsg("assistant", '<div class="md cursor"></div>'), box = d.querySelector(".md"); let reply = "";
  try {
    await stream("/api/chat", {messages: S.history, language: S.lang || null, mode: S.mode, files: S.attached, connection: S.connection || null}, ev => {
      if (ev.text) { reply += ev.text; box.innerHTML = md(reply); box.classList.add("cursor"); $("#messages").scrollTop = 1e9; }
    });
  } catch (e) { box.innerHTML = `<p class="note">The model did not answer: ${esc(e.message)}. Check <b>Model</b> at the bottom left.</p>`; }
  box.classList.remove("cursor");
  if (reply) S.history.push({role: "assistant", content: reply});
}
const HELP = `**Commands** (the language defaults to the one selected):

| Type | Does |
|---|---|
| \`/new\` | create a language: folder, settings, first dictionary, Lab and course |
| \`/expand <language> <topic>\` | a model proposes a checked batch of new words; it opens for review |
| \`/sentences <language> <topic>\` | course sentences, rendered by the grammar and checked by a round trip |
| \`/topics <language>\` | what to grow next |
| \`/build <language>\` | rebuild dictionary, docs, Lab and course |
| \`/lab <language>\`, \`/course <language>\` | open them here |
| \`/run <utp.py arguments>\` | any engine command, e.g. \`/run derive vulcan *sehaik\` |

Files you open can be **attached** to the chat, so the model reads them with your question.`;
function langArg(words) {
  if (words[0] && S.langs.some(l => l.id === words[0])) return [words[0], words.slice(1)];
  return [S.lang, words];
}
async function runCommand(text) {
  const [cmd, ...rest] = text.slice(1).trim().split(/\s+/);
  const [lang, args] = langArg(rest);
  const need = () => { if (!lang) { addMsg("assistant", `<p class="note">Choose a language first (left), or name it: <code>/${esc(cmd)} vulcan …</code></p>`); return true; } };
  if (cmd === "help" || !cmd) return addMsg("assistant", `<div class="md">${md(HELP)}</div>`);
  if (cmd === "new") return openNewLanguage();
  if (cmd === "lab" || cmd === "course") {
    if (need()) return; const l = S.langs.find(x => x.id === lang), p = l && (cmd === "lab" ? (l.pages.utp_lab || l.pages.lab) : l.pages.course);
    return p ? openFile(p) : addMsg("assistant", `<p class="note">${esc(lang)} has no ${cmd} yet: run /build ${esc(lang)}.</p>`);
  }
  const box = addMsg("assistant", `<div class="log">/${esc(cmd)} ${esc([lang, ...args].filter(Boolean).join(" "))}\n</div>`, "tool").querySelector(".log");
  const log = s => { box.textContent += s + "\n"; $("#messages").scrollTop = 1e9; };
  try {
    if (cmd === "build") { if (need()) return; await stream("/api/rebuild", {language: lang}, ev => { if (ev.line) log(ev.line); if (ev.done) log(`done, ${ev.errors} errors`); }); loadLanguages(); }
    else if (cmd === "expand") {
      if (need()) return; const topic = args.join(" "); if (!topic) return log("Name a topic: /expand vulcan weather and the sky");
      log("Asking the model for a batch…");
      const b = await api("/api/expand", {language: lang, topic, n: 30});
      const ok = b.rows.filter(r => r.status === "proposed").length;
      log(`${ok} proposals to review, ${b.rows.length - ok} rejected with reasons -> ${b.path}`); openFile(b.path);
    } else if (cmd === "sentences") {
      if (need()) return; const topic = args.join(" ") || "greetings";
      log("Asking the model for sentences…");
      const r = await api("/api/sentences", {language: lang, topic, n: 8});
      r.ok.forEach(s => log(`✓ ${s.v}   ${s.en}`)); r.bad.forEach(s => log(`✗ ${s.en}: ${s.why}`));
      if (r.ok.length) { const a = await api("/api/sentences/add", {language: lang, sentences: r.ok}); log(`${a.added} added to the course (${a.path}).`); }
    } else if (cmd === "topics") {
      if (need()) return; log("Thinking…"); (await api("/api/topics", {language: lang, ai: true})).topics.forEach(t => log("• " + t));
    } else if (cmd === "run") {
      await stream("/api/run", {args: rest}, ev => { if (ev.line !== undefined) log(ev.line); if (ev.done) log(`(exit ${ev.code})`); });
    } else log(`Unknown command. Type /help.`);
  } catch (e) { log("Error: " + e.message); }
}
$("#composer").onsubmit = e => {
  e.preventDefault(); const text = $("#input").value.trim(); if (!text) return;
  $("#input").value = ""; autosize();
  text.startsWith("/") ? runCommand(text) : sendChat(text);
};
const autosize = () => { const t = $("#input"); t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 220) + "px"; };
$("#input").addEventListener("input", autosize);
$("#input").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#composer").requestSubmit(); } });
document.addEventListener("click", e => { const b = e.target.closest("[data-cmd]"); if (b) runCommand(b.dataset.cmd); });
$("#new-chat").onclick = () => { S.history = []; $("#messages").innerHTML = ""; activate("chat"); $("#input").focus(); };

/* ---------- model status (the Settings page itself is in settings.js) ---------- */
async function refreshModel() {
  try {
    const h = await api("/api/health"); $("#model-label").textContent = h.model;
    const m = await api("/api/models"); $("#model-dot").className = "dot " + (m.error ? "bad" : "ok");
    $("#model-dot").title = m.error || "connected";
  } catch (e) { $("#model-dot").className = "dot bad"; }
  loadConnections();
}
async function loadConnections() {
  try {
    const s = await api("/api/settings");
    const chat = s.roles.chat;
    $("#chat-conn").innerHTML = s.connections.map(c => `<option value="${esc(c.id)}" ${c.id === (S.connection || chat) ? "selected" : ""}>${esc(c.name)}${c.id === chat ? " (default)" : ""}</option>`).join("");
  } catch (e) { }
}
$("#chat-conn").onchange = e => { S.connection = e.target.value; };
$("#settings-btn").onclick = () => openSettings();

/* ---------- new language ---------- */
function openNewLanguage() { $("#newlang-log").hidden = true; $("#newlang").showModal(); }
$("#new-lang").onclick = openNewLanguage;
$("#newlang-go").onclick = async () => {
  const f = $("#newlang-form"); if (!f.reportValidity()) return;
  const body = Object.fromEntries(new FormData(f)); const log = $("#newlang-log");
  log.hidden = false; log.textContent = "Creating…\n"; $("#newlang-go").disabled = true;
  try {
    await stream("/api/new", body, async ev => {
      if (ev.line) log.textContent += ev.line + "\n";
      if (ev.done) { await loadLanguages(); await loadTree("", $("#tree")); selectLanguage(ev.id); $("#newlang").close(); openFile(`${ev.home}/README.md`); revealFolder(ev.home); }
    });
  } catch (e) { log.textContent += "Error: " + e.message; }
  $("#newlang-go").disabled = false;
};

/* ---------- start ---------- */
(async () => {
  drawTabs();
  await Promise.all([loadLanguages(), loadTree("", $("#tree"))]);
  refreshModel();
  const m = location.hash.match(/lang=([\w-]+)/);
  if (m) {
    selectLanguage(m[1]); const l = S.langs.find(x => x.id === m[1]); if (l) revealFolder(l.home);
    const pg = location.hash.match(/page=(lab|course)/); if (pg) runCommand(`/${pg[1]} ${m[1]}`);
  }
  if (/settings/.test(location.hash)) openSettings();
  $("#input").focus();
})();
