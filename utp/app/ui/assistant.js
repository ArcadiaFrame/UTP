/* The tutor panel the UTP app adds to any Lab or course page it serves.
   Select text on the page and press "Explain", or ask anything; every answer is checked against the language's dictionary. */
(() => {
  if (window.__utpAssistant || document.getElementById("p-tutor")) return;     // the UTP Lab has its own Tutor tab
  window.__utpAssistant = true;
  const lang = window.UTP_LANGUAGE || null;
  const css = `
  #utp-a-btn{position:fixed;right:18px;bottom:18px;z-index:2147483000;background:#a3401e;color:#fff;border:0;border-radius:999px;padding:10px 16px;font:600 14px system-ui,sans-serif;box-shadow:0 4px 14px rgba(0,0,0,.25);cursor:pointer}
  #utp-a{position:fixed;right:18px;bottom:68px;z-index:2147483000;width:min(400px,calc(100vw - 36px));height:min(560px,calc(100vh - 100px));display:none;flex-direction:column;background:#fff;color:#1e1c1a;border:1px solid #d9d5cf;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.25);font:14px/1.45 system-ui,sans-serif}
  #utp-a.open{display:flex}
  #utp-a header{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #d9d5cf;font-weight:600}
  #utp-a header select{margin-left:auto;font:13px system-ui;border:1px solid #d9d5cf;border-radius:6px;padding:2px 4px;background:#fff;color:#1e1c1a}
  #utp-a .m{flex:1;overflow:auto;padding:10px 12px;display:flex;flex-direction:column;gap:8px}
  #utp-a .u{align-self:flex-end;background:#f6e6df;border-radius:10px;padding:6px 10px;max-width:85%;white-space:pre-wrap}
  #utp-a .r{white-space:pre-wrap}
  #utp-a form{display:flex;gap:6px;padding:8px;border-top:1px solid #d9d5cf}
  #utp-a textarea{flex:1;resize:none;height:56px;border:1px solid #d9d5cf;border-radius:8px;padding:6px 8px;font:inherit;background:#fff;color:#1e1c1a}
  #utp-a button{border:1px solid #d9d5cf;background:#fff;color:#1e1c1a;border-radius:7px;padding:5px 10px;cursor:pointer;font:inherit}
  #utp-a button.p{background:#a3401e;border-color:#a3401e;color:#fff}
  @media (prefers-color-scheme: dark){:root:not([data-theme="light"]) #utp-a,:root:not([data-theme="light"]) #utp-a textarea,:root:not([data-theme="light"]) #utp-a button:not(.p),:root:not([data-theme="light"]) #utp-a header select{background:#22201e;color:#ece7e1;border-color:#37322e}:root:not([data-theme="light"]) #utp-a .u{background:#3a231a}}:root[data-theme="dark"] #utp-a,:root[data-theme="dark"] #utp-a textarea,:root[data-theme="dark"] #utp-a button:not(.p),:root[data-theme="dark"] #utp-a header select{background:#22201e;color:#ece7e1;border-color:#37322e}:root[data-theme="dark"] #utp-a .u{background:#3a231a}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  const btn = document.createElement("button"); btn.id = "utp-a-btn"; btn.textContent = "Tutor";
  const box = document.createElement("div"); box.id = "utp-a"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Tutor");
  box.innerHTML = `<header>Tutor<select aria-label="Mode"><option value="tutor">Tutor</option><option value="assistant">Assistant</option><option value="translator">Translator</option></select><button type="button" data-x aria-label="Close">×</button></header>
    <div class="m"><div class="r">Ask about anything on this page. Select a word or line first and press Explain to ask about it.</div></div>
    <form><textarea placeholder="Ask in English or in the language" aria-label="Message"></textarea><div style="display:grid;gap:6px"><button class="p" type="submit">Send</button><button type="button" data-explain>Explain</button></div></form>`;
  document.body.append(btn, box);
  const m = box.querySelector(".m"), ta = box.querySelector("textarea"), mode = box.querySelector("select");
  const history = [];
  btn.onclick = () => { box.classList.toggle("open"); if (box.classList.contains("open")) ta.focus(); };
  box.querySelector("[data-x]").onclick = () => box.classList.remove("open");
  const add = (cls, text) => { const d = document.createElement("div"); d.className = cls; d.textContent = text; m.appendChild(d); m.scrollTop = 1e9; return d; };
  async function send(text) {
    if (!text.trim()) return;
    add("u", text); history.push({role: "user", content: text});
    const d = add("r", "…"); let reply = "";
    try {
      const r = await fetch("/api/chat", {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({language: lang, mode: mode.value, messages: history})});
      if (!r.ok) throw new Error(r.statusText);
      const rd = r.body.getReader(), dec = new TextDecoder(); let buf = "";
      for (;;) {
        const {done, value} = await rd.read(); if (done) break; buf += dec.decode(value, {stream: true});
        let i; while ((i = buf.indexOf("\n\n")) >= 0) {
          const line = buf.slice(0, i).split("\n").find(l => l.startsWith("data:")); buf = buf.slice(i + 2);
          if (!line) continue; const ev = JSON.parse(line.slice(5));
          if (ev.error) throw new Error(ev.error);
          if (ev.text) { reply += ev.text; d.textContent = reply; m.scrollTop = 1e9; }
        }
      }
      history.push({role: "assistant", content: reply});
    } catch (e) { d.textContent = "The model did not answer: " + e.message + ". Set it in the UTP app (Model, bottom left)."; }
  }
  box.querySelector("form").onsubmit = e => { e.preventDefault(); const t = ta.value; ta.value = ""; send(t); };
  ta.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); box.querySelector("form").requestSubmit(); } });
  box.querySelector("[data-explain]").onclick = () => {
    const sel = String(window.getSelection() || "").trim();
    send(sel ? `Explain this, word by word, with each word's dictionary meaning and its endings: ${sel}` : "Explain what is on this page and how to practise it.");
  };
})();
