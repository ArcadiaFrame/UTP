/* The workshop: a language's sources, attested words, design decisions and sound laws (utp/METHOD.md, steps 2-5).
   Each pane works from nothing and gets better with sources. Nothing reaches the dictionary without you. */
const W = {lang: null, pane: "sources", data: {}};
const TIER_ORDER = ["author", "canon", "licensed", "fan", "science"];

function openWorkshop(lang, pane) {
  const id = "workshop:" + lang, l = S.langs.find(x => x.id === lang);
  if (!S.tabs.some(t => t.id === id)) S.tabs.push({id, title: `${l ? l.language : lang}: workshop`});
  if (pane) W.pane = pane;
  selectLanguage(lang); activate(id);
}

async function renderWorkshop(lang) {
  W.lang = lang;
  const v = $("#workshop-view"), l = S.langs.find(x => x.id === lang) || {id: lang, language: lang};
  const [src, att, des, snd] = await Promise.all([
    api(`/api/sources?language=${lang}`), api(`/api/attested?language=${lang}`),
    api(`/api/design?language=${lang}`), api(`/api/sounds?language=${lang}`)].map(p => p.catch(e => ({error: e.message}))));
  W.data = {src, att, des, snd};
  const n = {
    sources: src.docs ? `${src.docs.length}` : "!",
    attested: att.rows ? `${att.rows.filter(r => r.status === "attested").length}` : "!",
    design: des.questions ? `${des.questions.filter(q => q.status === "decided").length}/${des.questions.length}` : "!",
    sounds: snd.proposal ? `${snd.proposal.fits}/${snd.proposal.total}` : (snd.current && snd.current.length ? `${snd.current.filter(r => r.ok).length}/${snd.current.length}` : "—"),
  };
  const steps = [["sources", "Sources"], ["attested", "Attested words"], ["design", "Design"], ["sounds", "Sound laws"]];
  v.innerHTML = `<div class="workshop">
    <div class="ws-head"><div><h1>${esc(l.language || lang)} workshop</h1>
      <p class="lead">Gather sources, find the words they already use, decide the design question by question, then
      find sound laws that produce the attested words. Start anywhere; with no sources, Design asks you instead.
      <a href="#" data-method>How this works</a></p></div></div>
    <nav class="ws-steps" role="tablist">${steps.map(([k, t], i) => `<button role="tab" data-pane="${k}" aria-selected="${W.pane === k}">
      <span class="num">${i + 1}</span>${t}<span class="badge">${n[k]}</span></button>`).join("")}
      ${l.pages && l.pages.utp_lab ? `<button data-grow><span class="num">5</span>Grow words</button>` : ""}</nav>
    <section class="ws-pane" id="ws-pane"></section></div>`;
  v.querySelectorAll("[data-pane]").forEach(b => b.onclick = () => { W.pane = b.dataset.pane; renderWorkshop(lang); });
  v.querySelector("[data-grow]")?.addEventListener("click", () => openFile(l.pages.utp_lab, "grow"));
  v.querySelector("[data-method]").onclick = e => { e.preventDefault(); openFile("utp/METHOD.md"); };
  ({sources: paneSources, attested: paneAttested, design: paneDesign, sounds: paneSounds})[W.pane]();
}

const P = () => $("#ws-pane");
function tierBadge(t) { return `<span class="badge tier-${esc(t)}">${esc(t)}</span>`; }
function citeChips(text) {
  return (String(text || "").match(/\b[SG]\d+\.\d+\b/g) || []).map(c => `<button class="cite" data-cite="${c}">${c}</button>`).join(" ");
}
function wsLog(el) { el.hidden = false; el.textContent = ""; return line => { el.textContent += line + "\n"; el.scrollTop = el.scrollHeight; }; }
function mark(text, q) {
  const words = (q || "").toLowerCase().match(/[\w']{2,}/g) || [];
  let h = esc(text);
  words.forEach(w => { h = h.replace(new RegExp(`(${w.replace(/[^\w']/g, "")}[\\w']*)`, "gi"), "<mark>$1</mark>"); });
  return h;
}

/* ---------- 1. sources ---------- */
function paneSources() {
  const d = W.data.src;
  if (d.error) return P().innerHTML = `<p class="note">${esc(d.error)}</p>`;
  const tiers = Object.entries(d.tiers).sort((a, b) => TIER_ORDER.indexOf(a[0]) - TIER_ORDER.indexOf(b[0]));
  P().innerHTML = `
    <div class="form">
      <b>Add sources</b>
      <p class="lead">Scripts, subtitles, wiki pages saved as HTML, novels (EPUB), papers (PDF), Word files, your notes.
      They stay on this computer and are not published. Files in <span class="mono">${esc(d.folder)}/public/</span> are
      published with the language.</p>
      <div class="drop" id="ws-drop" tabindex="0">Drop files here, or <label class="linklike">choose files<input type="file" id="ws-files" multiple hidden></label></div>
      <div class="grid2">
        <label>Tier <select id="ws-tier">${tiers.map(([k, t]) => `<option value="${k}" ${k === "canon" ? "selected" : ""}>${esc(t.label)}</option>`).join("")}</select></label>
        <label>Title (optional) <input id="ws-title" placeholder="e.g. Enterprise 1x07, The Andorian Incident"></label>
      </div>
      <label>Or paste text <textarea id="ws-text" rows="4" placeholder="Paste a scene, a wiki entry, your own notes…"></textarea></label>
      <div class="row"><label class="row"><input type="checkbox" id="ws-shared"> Shared with every language (general references, real-world science)</label>
        <span class="spacer"></span><button class="primary" id="ws-add">Add</button></div>
      <span class="result" id="ws-add-result"></span>
    </div>
    <div class="form">
      <b>Search</b>
      <div class="row"><input id="ws-q" placeholder="ice, duel, antennae, family…" style="flex:1">
        <select id="ws-qtier"><option value="">All tiers</option>${tiers.map(([k]) => `<option>${k}</option>`).join("")}</select>
        <button id="ws-search">Search</button></div>
      <p class="lead">${d.embeddings ? "Searching by words and by meaning." : "Searching by words. For search by meaning too, set an embedding model in Settings."}</p>
      <div id="ws-hits"></div>
    </div>
    <div><b>${d.docs.length} sources, ${d.passages.toLocaleString()} passages</b>
    ${d.docs.length ? `<table class="csv ws-table"><thead><tr><th>Id</th><th>Tier</th><th>Title</th><th>Passages</th><th>Added</th><th></th></tr></thead><tbody>
      ${d.docs.map(x => `<tr><td class="mono">${x.cite}</td><td>${tierBadge(x.tier)}</td><td>${esc(x.title)}${x.library === "G" ? ' <span class="muted">(shared)</span>' : ""}${x.kind === "decision" ? ' <span class="muted">(design decision)</span>' : ""}</td>
        <td>${x.passages}</td><td>${esc(x.added)}</td><td>${x.kind === "decision" ? "" : x.kind === "public" ? '<span class="muted" title="Published with the language: remove the file from sources/public/">published</span>' : `<button data-rm="${x.cite}">Remove</button>`}</td></tr>`).join("")}</tbody></table>`
      : '<p class="muted">None yet. A language can start from nothing: go to Design, and it asks you instead of citing.</p>'}</div>`;
  const files = [];
  const pick = list => { files.push(...list); $("#ws-drop").textContent = files.map(f => f.name).join(", ") || "Drop files here"; };
  $("#ws-files").onchange = e => pick([...e.target.files]);
  const drop = $("#ws-drop");
  drop.ondragover = e => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove("over"); pick([...e.dataTransfer.files]); };
  $("#ws-add").onclick = async () => {
    const out = $("#ws-add-result"); say(out, true, "Reading…");
    const enc = f => new Promise((ok, bad) => { const r = new FileReader(); r.onload = () => ok({name: f.name, data: r.result.split(",")[1]}); r.onerror = bad; r.readAsDataURL(f); });
    try {
      const res = await api("/api/sources/add", {language: W.lang, tier: $("#ws-tier").value, title: $("#ws-title").value.trim(),
        shared: $("#ws-shared").checked, text: $("#ws-text").value, files: await Promise.all(files.map(enc))});
      const bad = res.added.filter(a => a.problem);
      say(out, !bad.length, res.added.map(a => a.problem ? `${a.name}: ${a.problem}` : a.passages ? `${a.id}: ${a.passages} passages` : `${a.name}: already there (${a.id})`).join(" · ") || "Nothing to add.");
      if (res.added.some(a => a.passages)) setTimeout(() => renderWorkshop(W.lang), 900);
    } catch (e) { say(out, false, e.message); }
  };
  const search = async () => {
    const q = $("#ws-q").value.trim(); if (!q) return;
    const r = await api(`/api/sources/search?language=${W.lang}&q=${encodeURIComponent(q)}&tiers=${$("#ws-qtier").value}`);
    $("#ws-hits").innerHTML = r.hits.map(h => `<div class="hit"><div class="hit-head"><span class="mono">${h.id}</span>${tierBadge(h.tier)}<b>${esc(h.title)}</b></div>
      <div class="hit-text">${mark(h.text.slice(0, 700), q)}${h.text.length > 700 ? "…" : ""}</div></div>`).join("") || '<p class="muted">Nothing found.</p>';
  };
  $("#ws-search").onclick = search; $("#ws-q").onkeydown = e => { if (e.key === "Enter") search(); };
  P().querySelectorAll("[data-rm]").forEach(b => b.onclick = async () => {
    if (!confirm(`Remove source ${b.dataset.rm} and its passages from the library?`)) return;
    await api("/api/sources/remove", {language: W.lang, id: b.dataset.rm}); renderWorkshop(W.lang);
  });
}

/* ---------- 2. attested words ---------- */
function paneAttested() {
  const d = W.data.att;
  if (d.error) return P().innerHTML = `<p class="note">${esc(d.error)}</p>`;
  const rows = d.rows, probs = d.problems || {};
  P().innerHTML = `
    <div class="form">
      <b>Find the words your sources already use</b>
      <p class="lead">A model reads the canon, licensed and fan sources and lists every word, name and title in the
      language. Each must appear in the passage it cites, or it is rejected. These words are fixed: the sound laws must
      produce them and no new word may take their meanings.</p>
      <div class="row"><input id="au-q" placeholder="Optional: only passages about… (e.g. Andorian words)" style="flex:1">
        <button class="primary" id="au-run" ${W.data.src.passages ? "" : "disabled"}>Find attested words</button></div>
      ${W.data.src.passages ? "" : '<p class="muted">Add sources first, or add words by hand below.</p>'}
      <pre class="log" id="au-log" hidden></pre>
    </div>
    <div><b>${rows.filter(r => r.status === "attested").length} attested</b>${rows.length ? ` · ${rows.filter(r => r.status !== "attested").length} set aside` : ""}
    ${rows.length ? `<table class="csv ws-table"><thead><tr><th>Form</th><th>Meaning</th><th>Kind</th><th>Branch</th><th>Source</th><th>Evidence</th><th>Proto</th><th>Status</th></tr></thead><tbody>
      ${rows.map((r, i) => `<tr class="${r.status !== "attested" ? "rejected" : ""}${probs[r.form] ? " problem" : ""}">
        <td class="mono"><b>${esc(r.form)}</b></td><td>${esc(r.gloss)}${r.pos ? ` <span class="muted">${esc(r.pos)}</span>` : ""}</td><td>${esc(r.kind)}</td><td>${esc(r.branch)}</td>
        <td>${r.tier ? tierBadge(r.tier) : ""} ${citeChips(r.cite)}<div class="muted">${esc(r.source)}</div></td>
        <td class="tag">${esc(r.evidence)}${probs[r.form] ? `<div class="bad">${esc(probs[r.form])}</div>` : ""}</td><td class="mono">${esc(r.proto)}</td>
        <td><select data-row="${i}">${["attested", "doubtful", "rejected"].map(s => `<option ${r.status === s ? "selected" : ""}>${s}</option>`).join("")}</select></td></tr>`).join("")}</tbody></table>` : ""}</div>
    <div class="form">
      <b>Add a word by hand</b>
      <div class="grid3"><label>Form <input id="at-form" placeholder="ushaan"></label><label>Meaning <input id="at-gloss" placeholder="a duel to the death"></label>
        <label>Source passage <input id="at-cite" placeholder="S1.3 (optional)"></label>
        <label>Kind <select id="at-kind">${["word", "phrase", "name", "place", "title"].map(k => `<option>${k}</option>`).join("")}</select></label>
        <label>Branch <select id="at-branch">${(d.branches || []).map(b => `<option>${esc(b)}</option>`).join("")}</select></label>
        <label>Part of speech <input id="at-pos" placeholder="noun"></label></div>
      <div class="row"><button class="primary" id="at-add">Add</button><span class="result" id="at-result"></span></div>
    </div>`;
  $("#au-run").onclick = async () => {
    const log = wsLog($("#au-log"));
    try {
      await stream("/api/audit", {language: W.lang, query: $("#au-q").value.trim()}, ev => {
        if (ev.line) log(ev.line);
        if (ev.done) { log(`Done: ${ev.added} new attested words, ${ev.rejected} rejected.`); setTimeout(() => renderWorkshop(W.lang), 1200); }
      });
    } catch (e) { log("Stopped: " + e.message); }
  };
  P().querySelectorAll("[data-row]").forEach(s => s.onchange = async () => {
    const r = rows[+s.dataset.row];
    await api("/api/attested/set", {language: W.lang, form: r.form, kind: r.kind, status: s.value}); renderWorkshop(W.lang);
  });
  $("#at-add").onclick = async () => {
    const add = {form: $("#at-form").value.trim(), gloss: $("#at-gloss").value.trim(), cite: $("#at-cite").value.trim(),
                 kind: $("#at-kind").value, branch: $("#at-branch").value, pos: $("#at-pos").value.trim()};
    if (!add.form) return;
    try { await api("/api/attested/set", {language: W.lang, add}); renderWorkshop(W.lang); }
    catch (e) { say($("#at-result"), false, e.message); }
  };
}

/* ---------- 3. design ---------- */
function paneDesign() {
  const d = W.data.des;
  if (d.error) return P().innerHTML = `<p class="note">${esc(d.error)}</p>`;
  const open = d.questions.filter(q => q.status === "open"), undrafted = open.filter(q => !q.options.length);
  const card = q => {
    const decided = q.status === "decided" && !q._editing, chosen = (q.options || []).find(o => o.id === q.chosen);
    return `<div class="qcard ${q.status}" data-q="${esc(q.id)}">
      <div class="conn-head"><b>${esc(q.question)}</b>${(q.angles || []).map(a => `<span class="badge">${esc(a)}</span>`).join("")}
        <span class="badge ${q.status === "decided" ? "ok" : ""}">${q.status}</span></div>
      ${decided ? `<p><b>${esc(q.answer)}.</b> ${esc(chosen ? chosen.argument : "")}</p>${q.reason ? `<p class="muted">Why: ${esc(q.reason)}</p>` : ""}
        <div class="acts"><button data-reopen>Change</button></div>`
      : q.status === "skipped" ? `<div class="acts"><button data-reopen>Reopen</button></div>`
      : q.options.length ? `${q.settled ? '<p class="note">The sources already settle this; option A is what they say.</p>' : ""}
        ${q.options.map(o => `<label class="opt"><input type="radio" name="q-${esc(q.id)}" value="${o.id}" ${o.id === (q.chosen || q.recommended) ? "checked" : ""}>
          <div><b>${o.id}. ${esc(o.label)}</b>${o.id === q.recommended ? ' <span class="badge role">recommended</span>' : ""}
          ${o.invention ? ' <span class="badge">invention</span>' : ""}${(o.angles || []).map(a => ` <span class="badge">${esc(a)}</span>`).join("")}
          <div>${esc(o.argument)}</div>${o.cost ? `<div class="muted">Cost: ${esc(o.cost)}</div>` : ""}
          ${o.cites.length ? `<div>${citeChips(o.cites.join(" "))}</div>` : ""}</div></label>`).join("")}
        <label class="opt"><input type="radio" name="q-${esc(q.id)}" value="own"><div><b>My own answer</b><input data-own placeholder="Write it here"></div></label>
        <label>Why (optional, goes into DESIGN.md) <input data-reason value="${esc(q.reason || "")}"></label>
        <div class="acts"><button class="primary" data-decide>Decide</button><button data-redraft>Draft again</button><button data-skip>Skip</button></div>`
      : `<div class="acts"><button data-draft>Draft options</button><button data-skip>Skip</button></div>`}
    </div>`;
  };
  P().innerHTML = `
    <div class="form">
      <b>Decide the design, one question at a time</b>
      <p class="lead">For each question a model offers options argued from the angles (canon, body, world, society,
      history, sound, use) and cites your sources; with no sources, the options are marked invention. Your answers go
      into <a href="#" data-designmd>DESIGN.md</a>, which every later prompt reads, and into the library as your own
      decisions, which outrank every other source.</p>
      <div class="row"><button class="primary" id="ds-next" ${undrafted.length ? "" : "disabled"}>Draft the next 3 questions</button>
        <input id="ds-ask" placeholder="Or ask your own: Is there a separate military register?" style="flex:1"><button id="ds-add">Add question</button></div>
      <pre class="log" id="ds-log" hidden></pre>
    </div>
    ${d.questions.map(card).join("")}`;
  P().querySelector("[data-designmd]").onclick = e => { e.preventDefault(); openFile(d.design); };
  const draft = async ids => {
    const log = wsLog($("#ds-log"));
    try {
      await stream("/api/design/draft", {language: W.lang, ids, n: 3}, ev => {
        if (ev.line) log(ev.line); if (ev.done) renderWorkshop(W.lang);
      });
    } catch (e) { log("Stopped: " + e.message); }
  };
  $("#ds-next").onclick = () => draft(null);
  $("#ds-add").onclick = async () => {
    const q = $("#ds-ask").value.trim(); if (!q) return;
    await api("/api/design/ask", {language: W.lang, question: q}); renderWorkshop(W.lang);
  };
  P().querySelectorAll(".qcard").forEach(c => {
    const id = c.dataset.q, q = d.questions.find(x => x.id === id);
    c.querySelector("[data-draft]")?.addEventListener("click", () => draft([id]));
    c.querySelector("[data-redraft]")?.addEventListener("click", () => draft([id]));
    c.querySelector("[data-skip]")?.addEventListener("click", async () => { await api("/api/design/decide", {language: W.lang, id, choice: "skip"}); renderWorkshop(W.lang); });
    c.querySelector("[data-reopen]")?.addEventListener("click", () => { q._editing = true; q.status = "open"; paneDesign(); });
    c.querySelector("[data-decide]")?.addEventListener("click", async () => {
      const pickd = c.querySelector("input[type=radio]:checked"); if (!pickd) return;
      const choice = pickd.value === "own" ? c.querySelector("[data-own]").value.trim() : pickd.value;
      if (!choice) return;
      await api("/api/design/decide", {language: W.lang, id, choice, reason: c.querySelector("[data-reason]").value.trim()});
      renderWorkshop(W.lang);
    });
  });
}

/* ---------- 4. sound laws ---------- */
function fitTable(rows) {
  return `<table class="csv ws-table"><thead><tr><th></th><th>Attested</th><th>Branch</th><th>Proto-form</th><th>The laws give</th><th></th></tr></thead><tbody>
    ${rows.map(r => `<tr class="${r.ok ? "" : "problem"}"><td>${r.ok ? '<span class="good">✓</span>' : '<span class="bad">✗</span>'}</td>
      <td class="mono"><b>${esc(r.form)}</b></td><td>${esc(r.branch)}</td><td class="mono">${esc(r.proto)}</td><td class="mono">${esc(r.got)}</td>
      <td class="tag">${esc(r.ok ? "" : r.why)}</td></tr>`).join("")}</tbody></table>`;
}
function paneSounds() {
  const d = W.data.snd, att = (W.data.att.rows || []).filter(r => r.status === "attested");
  if (d.error) return P().innerHTML = `<p class="note">${esc(d.error)}</p>`;
  const p = d.proposal;
  P().innerHTML = `
    <div class="form">
      <b>Sound laws that produce the attested words</b>
      <p class="lead">A model reconstructs a proto-language and writes each branch's sound laws; then the engine runs
      them on every attested word and shows which come out exactly right. Accepting makes them the language's laws,
      locks the attested words into the dictionary with their proto-forms, and rebuilds. From then on every build
      checks them (E6).</p>
      <div class="row"><button class="primary" id="sd-run">${p ? "Propose again" : "Propose sound laws"}</button>
        <span class="muted">${att.length} attested words to explain${att.length ? "" : " (none yet: the laws are then free, shaped by the Design answers)"}</span></div>
      <span class="result" id="sd-result"></span>
      <pre class="log" id="sd-log" hidden></pre>
    </div>
    ${d.current && d.current.length ? `<div><b>The current laws: ${d.current.filter(r => r.ok).length} of ${d.current.length} attested words come out right</b>${fitTable(d.current)}</div>` : ""}
    ${p ? `<div class="form">
      <b>Proposal of ${esc(p.date)}: ${p.fits} of ${p.total} attested words come out right</b>
      ${p.notes ? `<p>${esc(p.notes)}</p>` : ""}
      <dl class="kv"><dt>Sounds</dt><dd>${esc((p.laws.proto.units || []).join(" "))}</dd><dt>Vowels</dt><dd>${esc((p.laws.proto.vowels || []).join(" "))}</dd>
        <dt>Onset clusters</dt><dd>${esc((p.laws.proto.onset_clusters || []).join(" ") || "none")}</dd><dt>Finals</dt><dd>${esc((p.laws.proto.finals || []).join(" "))}</dd></dl>
      ${Object.entries(p.laws.branches).map(([b, spec]) => `<div><b>${esc(spec.label || b)}</b>${spec.inherits ? ` <span class="muted">after ${esc(spec.inherits)}</span>` : ""}
        <table class="csv ws-table"><thead><tr><th>Law</th><th>Pattern</th><th>Becomes</th><th>What and why</th></tr></thead><tbody>
        ${spec.rules.map(r => `<tr><td class="mono">${esc(r.id)}</td><td class="mono">${esc(r.pattern)}</td><td class="mono">${esc(r.replace)}</td><td class="tag">${esc(r.note || "")}</td></tr>`).join("") || '<tr><td colspan="4" class="muted">No changes: this branch keeps the proto-forms.</td></tr>'}</tbody></table></div>`).join("")}
      ${fitTable(p.fit)}
      ${d.buildable ? `<label class="row"><input type="checkbox" id="sd-fresh" ${d.approved_words ? "" : "checked"}> Give every generated word a new form from these laws
        <span class="muted">(${d.approved_words ? "off: words have been approved, so only forms the new laws cannot say are remade" : "recommended: no words approved yet, so the first dictionary was only a placeholder"})</span></label>
        <div class="row"><button class="primary" id="sd-accept">Accept${p.fits < p.total ? ` (the ${p.fits} that fit)` : ""} and rebuild</button>
        <span class="muted">Words the laws miss stay attested, without a proto-form, until a later proposal explains them.</span></div>` :
        '<p class="note">This language keeps its own sound laws (Vulcan: vulcan-conlang/tools). Use the proposal as a reference.</p>'}
    </div>` : ""}`;
  $("#sd-run").onclick = async () => {
    say($("#sd-result"), true, "Asking the model… (this can take a minute)");
    try { await api("/api/sounds/propose", {language: W.lang}); renderWorkshop(W.lang); }
    catch (e) { say($("#sd-result"), false, e.message); }
  };
  $("#sd-accept")?.addEventListener("click", async () => {
    const log = wsLog($("#sd-log"));
    try {
      await stream("/api/sounds/accept", {language: W.lang, fresh: $("#sd-fresh").checked}, ev => {
        if (ev.line) log(ev.line);
        if (ev.done) { log(`Done: ${ev.errors} build errors.`); loadLanguages(); setTimeout(() => renderWorkshop(W.lang), 1200); }
      });
    } catch (e) { log("Stopped: " + e.message); }
  });
}

/* ---------- citations anywhere in the app ---------- */
function langOfPath(path) {
  const l = S.langs.find(x => x.home && (path === x.home || path.startsWith(x.home + "/")));
  return l ? l.id : S.lang;
}
async function showCite(lang, id) {
  const dlg = $("#cite-pop");
  dlg.innerHTML = `<p class="muted">Loading ${esc(id)}…</p>`; if (!dlg.open) dlg.showModal();
  try {
    const p = await api(`/api/sources/passage?language=${lang}&id=${encodeURIComponent(id)}`);
    dlg.innerHTML = `<div class="conn-head"><span class="mono">${esc(p.id)}</span>${tierBadge(p.tier)}<b>${esc(p.title)}</b>
      <span class="spacer"></span><button data-close aria-label="Close">×</button></div>
      <div class="hit-text">${esc(p.text)}</div>${p.url ? `<p><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.url)}</a></p>` : ""}`;
  } catch (e) { dlg.innerHTML = `<p class="bad">${esc(id)}: ${esc(e.message)}</p><button data-close>Close</button>`; }
}
document.addEventListener("click", e => {
  const c = e.target.closest(".cite");
  if (c) { e.preventDefault(); showCite((S.active.startsWith("workshop:") ? S.active.slice(9) : langOfPath(S.active)), c.dataset.cite); return; }
  if (e.target.closest("#cite-pop [data-close]")) $("#cite-pop").close();
});
$("#cite-pop").addEventListener("click", e => { if (e.target === e.currentTarget) e.currentTarget.close(); });
