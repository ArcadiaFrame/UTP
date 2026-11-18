/* Settings: model connections and what each one does, speech, folders, startup, and where everything lives.
   The same page in the browser and in the desktop window; everything is saved in one file on this computer. */
let SET = null, EDIT = null;           // the settings as last loaded; the connection being edited (or "new")

function openSettings() {
  if (!S.tabs.some(t => t.id === "settings")) S.tabs.push({id: "settings", title: "Settings"});
  activate("settings");
}

async function renderSettings() {
  const v = $("#settings-view");
  try { [SET, ABOUT] = await Promise.all([api("/api/settings"), api("/api/about")]); }
  catch (e) { v.innerHTML = `<div class="settings"><p class="note">${esc(e.message)}</p></div>`; return; }
  const P = SET.providers, roleOf = id => Object.entries(SET.roles).filter(([, v]) => v === id).map(([r]) => r);
  const conns = SET.connections.map(c => EDIT === c.id ? connForm(c) : `
    <div class="conn" data-id="${esc(c.id)}">
      <div class="conn-head"><b>${esc(c.name)}</b><span class="badge">${esc(P[c.provider].label)}</span>
        ${roleOf(c.id).map(r => `<span class="badge role">${r === "chat" ? "chats" : "builds"}</span>`).join("")}
        ${c.key_set ? `<span class="badge ok">key saved</span>` : c.needs_key ? `<span class="badge bad">needs a key</span>` : ""}
        <span class="result" data-result></span></div>
      <div class="meta">${esc(c.model)} · ${esc(c.url)}</div>
      <div class="acts">
        <button data-test>Test</button><button data-edit>Edit</button>
        ${roleOf(c.id).includes("chat") ? "" : `<button data-role="chat">Use for chat</button>`}
        ${roleOf(c.id).includes("build") ? "" : `<button data-role="build">Use for building</button>`}
        ${SET.connections.length > 1 ? `<button data-delete>Delete</button>` : ""}
      </div>
    </div>`).join("");
  const opts = sel => SET.connections.map(c => `<option value="${esc(c.id)}" ${c.id === sel ? "selected" : ""}>${esc(c.name)}</option>`).join("");
  const env = SET.env_overrides.length ? `<p class="warn">These are set in the environment and override the page: <span class="mono">${esc(SET.env_overrides.join(", "))}</span>.</p>` : "";
  v.innerHTML = `<div class="settings">
    <div><h1>Settings</h1><p class="lead">Saved only on this computer, in <span class="mono">${esc(SET.config_path)}</span>. API keys never leave it except to the service they belong to.</p></div>
    ${env}
    <section>
      <div><h2>Models</h2><p class="lead">Add as many connections as you like: Ollama or LM Studio on this or another machine, OpenAI, or Anthropic's Claude. Pick which one chats and which one builds (expand, sentences, topics); they can differ, for example a local model to chat and Claude to build.</p></div>
      ${conns}
      ${EDIT === "new" ? connForm({provider: "ollama", name: "", url: P.ollama.url, model: P.ollama.model}) : `<div><button data-add>+ Add a connection</button></div>`}
      <div class="row"><label class="row">Chat uses <select id="role-chat">${opts(SET.roles.chat)}</select></label>
        <label class="row">Building uses <select id="role-build">${opts(SET.roles.build)}</select></label></div>
    </section>
    <section>
      <div><h2>Speech</h2><p class="lead">Kokoro-FastAPI, for hearing words in the tutor and <span class="mono">utp.py say</span>. Optional.</p></div>
      <div class="form"><div class="grid2">
        <label>Kokoro address <input id="sp-url" value="${esc(SET.speech.url)}"></label>
        <label>Voice (blank: each language's own) <input id="sp-voice" value="${esc(SET.speech.voice || "")}" placeholder="bm_george"></label></div>
        <div class="row"><button data-sp-test>Test</button><button class="primary" data-sp-save>Save</button><span class="result" id="sp-result"></span></div></div>
    </section>
    <section>
      <div><h2>Folders</h2><p class="lead">Where new languages are made, and other folders to show in the file list (your writing, research, exports). Changing the languages folder does not move existing languages.</p></div>
      <div class="form">
        <label>Languages folder <input id="p-lang" value="${esc(SET.paths.languages || "")}" placeholder="${esc(SET.languages_dir)}"></label>
        <div class="row"><button data-p-check>Check</button><button class="primary" data-p-save>Save</button><span class="result" id="p-result">Now: <span class="mono">${esc(SET.languages_dir)}</span></span></div>
      </div>
      <div class="form">
        <b style="font-size:14px">Extra folders in the file list</b>
        ${SET.paths.workspaces.map((w, i) => `<div class="row"><span>${esc(w.name || "")}</span><span class="mono">${esc(w.path)}</span><button data-ws-del="${i}">Remove</button></div>`).join("") || '<span class="muted">None yet.</span>'}
        <div class="grid2"><label>Name <input id="ws-name" placeholder="Writing"></label><label>Folder <input id="ws-path" placeholder="/home/you/Writing"></label></div>
        <div class="row"><button class="primary" data-ws-add>Add folder</button><span class="result" id="ws-result"></span></div>
      </div>
    </section>
    <section>
      <div><h2>Startup</h2><p class="lead">What double-clicking <b>Start UTP</b> (or a language's <b>Open …</b> file, or the shortcut) opens.</p></div>
      <div class="form"><div class="grid2">
        <label>Open in <select id="ap-open">
          ${[["auto", "The desktop window if installed, else the browser"], ["desktop", "The desktop window (installs it the first time)"], ["browser", "The browser"]].map(([k, t]) => `<option value="${k}" ${SET.app.open === k ? "selected" : ""}>${t}</option>`).join("")}
        </select></label>
        <label>Port <input id="ap-port" type="number" min="1024" max="65535" value="${esc(SET.app.port)}"></label>
        <label>Python for the desktop window (blank: find it) <input id="ap-python" value="${esc(SET.desktop.python || "")}" placeholder="${esc(ABOUT.python)}"></label>
        <label>Desktop window <input disabled value="${ABOUT.desktop_installed ? "installed" : "not installed (cd desktop && npm install)"}"></label></div>
        <div class="row"><button class="primary" data-ap-save>Save</button><button data-shortcut>Make desktop and menu shortcuts</button><span class="result" id="ap-result"></span></div>
      </div>
    </section>
    <section>
      <div><h2>About this copy</h2></div>
      <dl class="kv"><dt>Repository</dt><dd>${esc(ABOUT.repo)}</dd><dt>Settings file</dt><dd>${esc(SET.config_path)}</dd>
        <dt>Languages</dt><dd>${esc(SET.languages_dir)}</dd><dt>Python</dt><dd>${esc(ABOUT.python)} (${esc(ABOUT.python_version)})</dd>
        <dt>Running as</dt><dd>${esc(ABOUT.mode)}</dd><dt>Address</dt><dd>${esc(location.origin)}</dd></dl>
    </section>
  </div>`;
  bindSettings();
}

function connForm(c) {
  const P = SET.providers, isNew = !c.id;
  return `<div class="form" id="conn-form" data-id="${esc(c.id || "")}">
    <b style="font-size:15px">${isNew ? "New connection" : "Edit " + esc(c.name)}</b>
    <div class="grid2">
      <label>Name <input id="cf-name" value="${esc(c.name)}" placeholder="e.g. Ollama on my desktop, Claude, LM Studio"></label>
      <label>Provider <select id="cf-provider">${Object.entries(P).map(([k, d]) => `<option value="${k}" ${k === c.provider ? "selected" : ""}>${esc(d.label)}</option>`).join("")}</select></label>
      <label>Server address <input id="cf-url" value="${esc(c.url)}"></label>
      <label>Model <span class="row"><input id="cf-model" list="cf-models" value="${esc(c.model)}" style="flex:1"><button type="button" data-cf-load>List models</button></span><datalist id="cf-models"></datalist></label>
      <label id="cf-key-row">API key <input id="cf-key" type="password" autocomplete="off" placeholder="${c.key_set ? "saved: leave blank to keep" : "paste the key"}"></label>
      ${c.key_set ? `<label class="row" style="align-self:end"><input type="checkbox" id="cf-key-clear"> Remove the saved key</label>` : "<span></span>"}
    </div>
    <p class="lead" id="cf-hint"></p>
    <div class="row"><button data-cf-test>Test</button><span class="spacer"></span><button data-cf-cancel>Cancel</button><button class="primary" data-cf-save>Save</button></div>
    <span class="result" id="cf-result"></span>
  </div>`;
}

const HINTS = {
  ollama: "Ollama: on this machine http://localhost:11434/v1; on another machine use its address, e.g. http://desktop.local:11434/v1. No key.",
  openai: "OpenAI-compatible: LM Studio http://localhost:1234/v1, llama.cpp http://localhost:8080/v1, vLLM, Open WebUI (…/api), or OpenAI itself https://api.openai.com/v1 (key needed).",
  anthropic: "Anthropic: https://api.anthropic.com with a key from console.anthropic.com. Models such as claude-sonnet-5-5, claude-opus-5-5, claude-haiku-5-5.",
};
function draftConn() {
  const f = $("#conn-form");
  return {id: f.dataset.id || null, name: $("#cf-name").value.trim(), provider: $("#cf-provider").value,
          url: $("#cf-url").value.trim(), model: $("#cf-model").value.trim()};
}
function say(el, ok, text) { el.className = "result " + (ok ? "ok" : "bad"); el.textContent = text; }

function bindSettings() {
  const v = $("#settings-view");
  const form = $("#conn-form");
  if (form) {
    const syncHint = () => { const p = $("#cf-provider").value; $("#cf-hint").textContent = HINTS[p]; $("#cf-key-row").hidden = p === "ollama"; };
    syncHint();
    $("#cf-provider").onchange = () => { const p = $("#cf-provider").value; $("#cf-url").value = SET.providers[p].url; $("#cf-model").value = SET.providers[p].model; syncHint(); };
    const test = async () => {
      say($("#cf-result"), true, "Testing…");
      const r = await api("/api/connections/test", {connection: draftConn(), key: $("#cf-key").value || null});
      if (r.ok) { $("#cf-models").innerHTML = r.models.map(m => `<option value="${esc(m)}">`).join("");
        say($("#cf-result"), true, `Connected: ${r.models.length} models offered${r.model_found ? ", including this one" : `; "${draftConn().model}" is not among them`}.`); }
      else say($("#cf-result"), false, "No connection: " + r.problem);
    };
    v.querySelector("[data-cf-test]").onclick = test;
    v.querySelector("[data-cf-load]").onclick = test;
    v.querySelector("[data-cf-cancel]").onclick = () => { EDIT = null; renderSettings(); };
    v.querySelector("[data-cf-save]").onclick = async () => {
      const d = draftConn(); if (!d.name) return say($("#cf-result"), false, "Give it a name.");
      const key = $("#cf-key-clear") && $("#cf-key-clear").checked ? "" : ($("#cf-key").value || null);
      await api("/api/connections", {connection: d, key});
      EDIT = null; renderSettings(); refreshModel();
    };
  }
  v.querySelector("[data-add]")?.addEventListener("click", () => { EDIT = "new"; renderSettings(); });
  v.querySelectorAll(".conn").forEach(card => {
    const id = card.dataset.id, res = card.querySelector("[data-result]");
    card.querySelector("[data-edit]").onclick = () => { EDIT = id; renderSettings(); };
    card.querySelector("[data-test]").onclick = async () => {
      say(res, true, "Testing…");
      const r = await api("/api/connections/test", {connection: SET.connections.find(c => c.id === id)});
      r.ok ? say(res, true, `connected · ${r.models.length} models${r.model_found ? "" : " · this model not offered"}`) : say(res, false, r.problem);
    };
    card.querySelectorAll("[data-role]").forEach(b => b.onclick = async () => { await api("/api/settings", {roles: {[b.dataset.role]: id}}); renderSettings(); refreshModel(); });
    card.querySelector("[data-delete]")?.addEventListener("click", async () => {
      if (!confirm(`Delete the connection "${SET.connections.find(c => c.id === id).name}" and its saved key?`)) return;
      await api("/api/connections/delete", {id}); renderSettings(); refreshModel();
    });
  });
  $("#role-chat").onchange = async e => { await api("/api/settings", {roles: {chat: e.target.value}}); renderSettings(); refreshModel(); };
  $("#role-build").onchange = async e => { await api("/api/settings", {roles: {build: e.target.value}}); renderSettings(); };

  v.querySelector("[data-sp-test]").onclick = async () => {
    const r = await api("/api/speech/test", {url: $("#sp-url").value.trim()});
    say($("#sp-result"), r.ok, r.ok ? `Kokoro answers at ${r.url}.` : `No answer at ${r.url}.`);
  };
  v.querySelector("[data-sp-save]").onclick = async () => {
    await api("/api/settings", {speech: {url: $("#sp-url").value.trim(), voice: $("#sp-voice").value.trim()}});
    say($("#sp-result"), true, "Saved.");
  };

  const checkPath = async (path, out) => {
    const r = await api("/api/paths/check", {path});
    say(out, r.dir || !r.exists, !r.exists ? `${r.path} does not exist yet; it will be made.` :
      !r.dir ? `${r.path} is a file, not a folder.` : `${r.path}: ${r.writable ? "writable" : "NOT writable"}${r.languages.length ? `, ${r.languages.length} languages (${r.languages.join(", ")})` : ""}.`);
    return r;
  };
  v.querySelector("[data-p-check]").onclick = () => checkPath($("#p-lang").value.trim() || SET.languages_dir, $("#p-result"));
  v.querySelector("[data-p-save]").onclick = async () => {
    try { await api("/api/settings", {paths: {languages: $("#p-lang").value.trim()}}); await renderSettings(); loadLanguages(); loadTree("", $("#tree")); say($("#p-result"), true, "Saved."); }
    catch (e) { say($("#p-result"), false, e.message); }
  };
  v.querySelector("[data-ws-add]").onclick = async () => {
    const path = $("#ws-path").value.trim(); if (!path) return;
    const r = await checkPath(path, $("#ws-result")); if (!r.dir) return;
    try { await api("/api/settings", {paths: {workspaces: [...SET.paths.workspaces, {name: $("#ws-name").value.trim(), path: r.path}]}}); renderSettings(); loadTree("", $("#tree")); }
    catch (e) { say($("#ws-result"), false, e.message); }
  };
  v.querySelectorAll("[data-ws-del]").forEach(b => b.onclick = async () => {
    const ws = SET.paths.workspaces.filter((_, i) => i !== +b.dataset.wsDel);
    await api("/api/settings", {paths: {workspaces: ws}}); renderSettings(); loadTree("", $("#tree"));
  });

  v.querySelector("[data-ap-save]").onclick = async () => {
    await api("/api/settings", {app: {open: $("#ap-open").value, port: +$("#ap-port").value || 8765}, desktop: {python: $("#ap-python").value.trim()}});
    say($("#ap-result"), true, "Saved. A new port takes effect the next time the app starts.");
  };
  v.querySelector("[data-shortcut]").onclick = async () => {
    const r = await api("/api/shortcut", {}); say($("#ap-result"), true, r.made.join(" · "));
  };
}
let ABOUT = null;
