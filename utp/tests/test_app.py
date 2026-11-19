"""The model connection, new languages, model-assisted growth, and the app server.

  python3 utp/tests/test_app.py

Runs against a mock server that answers like the Anthropic Messages API, an
OpenAI-compatible server and Ollama, streaming and not. Uses only localhost and
temporary folders: no real model, no key, and nothing in the repository changes.
1. Model: all three providers chat, stream and list models; Anthropic gets its headers.
2. utp.py new: a language folder with settings, a first dictionary (0 errors), Lab and course.
3. expand: a model batch is checked (bad parts, duplicates and self-reference rejected with
   reasons); apply adds only approved rows and rebuilds the dictionary, Lab and course.
4. sentences: frames render in the new grammar, read back, and join the course.
5. The app server: languages, files, the tutor injected into Lab pages, chat streaming,
   expand and apply over HTTP, new language over HTTP, engine commands, and its guards.
6. Vulcan: a batch applied to a copy of the repository runs Vulcan's own pipeline cleanly.
"""
import csv
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

UTP = pathlib.Path(__file__).resolve().parent.parent
REPO = UTP.parent
TMP = pathlib.Path(tempfile.mkdtemp())
os.environ.update(UTP_LANGUAGES=str(TMP / "languages"), UTP_HOME=str(TMP / "home"))
for k in ("UTP_LLM_PROVIDER", "UTP_LLM_URL", "UTP_LLM_MODEL", "UTP_LLM_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
    os.environ.pop(k, None)
sys.path.insert(0, str(REPO))
CALLS = []

ENTRIES = [
    {"key": "star-river", "gloss": "the band of stars across the night sky", "pos": "noun", "field": "the-physical-world",
     "era": "Old", "kind": "compound", "parts": "{star}-{river}", "basis": "Japanese ama-no-gawa 'heaven's river'",
     "sources": ["S1.1", "S42.1"]},
    {"key": "rain-house", "gloss": "shelter from rain", "pos": "noun", "field": "the-house", "era": "Ancient",
     "kind": "compound", "parts": "{rain-precipitation}-{house}", "basis": "a plain descriptive compound"},
    {"key": "glimmerfrost", "gloss": "frost that glitters at dawn", "pos": "noun", "field": "the-physical-world",
     "era": "Middle", "kind": "root", "parts": "", "basis": "a meaning this culture names on its own"},
    {"key": "bad-one", "gloss": "a thing of nothing", "pos": "noun", "field": "x", "era": "Old", "kind": "compound",
     "parts": "{no-such-word}-{house}", "basis": "unknown part"},
    {"key": "water-again", "gloss": "water", "pos": "noun", "field": "x", "era": "Old", "kind": "compound",
     "parts": "{water}-{water}", "basis": "duplicate meaning"},
    {"key": "loop", "gloss": "a loop word", "pos": "noun", "field": "x", "era": "Old", "kind": "compound",
     "parts": "{loop}-{house}", "basis": "names itself"},
]
FRAMES = [
    {"en": "I want water.", "frame": {"subject": {"pron": "1sg"}, "object": {"head": "water"}, "verb": "want"}},
    {"en": "Where are you going?", "frame": {"type": "wh", "wh": {"word": "where", "role": "location"},
                                            "subject": {"pron": "2sg"}, "verb": "go", "aspect": "ongoing"}},
    {"en": "Bad frame", "frame": {"subject": {"head": "zzz-not-a-word"}, "verb": "go"}},
]


AUDIT = {"words": [
    {"form": "kethra", "gloss": "ice", "pos": "noun", "kind": "word", "branch": "north", "cite": "S1.1", "evidence": "call ice kethra"},
    {"form": "sora", "gloss": "dawn", "pos": "noun", "kind": "word", "branch": "south", "cite": "S1.1"},
    {"form": "velan", "gloss": "sled", "pos": "noun", "kind": "word", "branch": "north", "cite": "S1.1"},
    {"form": "zzfake", "gloss": "made up", "kind": "word", "cite": "S1.1"},
    {"form": "Varo", "kind": "name", "cite": "S9.9"}]}
DRAFT = {"options": [{"label": "Ice people", "argument": "the sources say so", "angles": ["world"], "cites": ["S1.1", "S99.1"]},
                     {"label": "Sky people", "argument": "invention", "angles": ["world"], "cites": []}], "recommended": "A"}
SOUNDS = {"proto": {"units": ["th", "p", "t", "k", "m", "n", "s", "l", "r", "v", "h", "y", "w", "a", "e", "i", "o", "u"],
                    "vowels": ["a", "e", "i", "o", "u"], "finals": ["n", "m", "s", "r", "l", "k", "t", "th"]},
          "branches": {"south": {"rules": [{"id": "S1", "pattern": "u", "replace": "o", "note": "u lowers to o"}]}},
          "words": [{"form": "kethra", "branch": "north", "proto": "*kethra"}, {"form": "sora", "branch": "south", "proto": "*sura"},
                    {"form": "velan", "branch": "north", "proto": "*velam"}], "notes": "mock laws"}


def reply_for(text):
    if "auditing sources" in text:
        return json.dumps(AUDIT)
    if "Design question:" in text:
        return json.dumps(DRAFT)
    if "Reconstruct the proto-language" in text:
        return json.dumps(SOUNDS)
    if "Topic for this batch" in text:
        return json.dumps({"entries": ENTRIES})
    if "Frame format" in text:
        return json.dumps({"sentences": FRAMES})
    if "Suggest the" in text:
        return json.dumps({"topics": ["weather", "the household"]})
    return "Hello from the mock model."


class Mock(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        CALLS.append(("GET", self.path, dict(self.headers), None))
        base = f"http://127.0.0.1:{self.server.server_port}"
        path = urllib.parse.urlparse(self.path)
        if path.path == "/search":                                         # SearXNG
            q = urllib.parse.parse_qs(path.query)
            return self._send({"query": q["q"][0], "results": [
                {"title": "Ice hare", "url": f"{base}/wiki/Ice_hare", "content": "The ice hare of the north", "engine": "mock"},
                {"title": "Snow notes", "url": f"{base}/notes.html", "content": "notes on snow", "engines": ["a", "b"]},
                {"title": "Ice hare again", "url": f"{base}/wiki/Ice_hare", "content": "duplicate"}]})
        if path.path == "/nojson/search":
            return self._send(b"<html>SearXNG</html>", "text/html")
        if path.path == "/api.php":                                        # a MediaWiki site
            return self._send({"parse": {"title": "Ice hare", "text": {"*": '<div class="navbox">Menu Home Random</div>'
                               "<p>The ice hare is called thraal in the north. It turns white in winter and lives under the snow crust.</p>"}}})
        if path.path == "/notes.html":
            return self._send(b"<html><head><title>Snow notes</title></head><body><nav>menu</nav><main><p>" + b"Snow lies deep. " * 60
                              + b"</p></main><footer>foot</footer></body></html>", "text/html; charset=utf-8")
        if path.path == "/blocked":
            self.send_response(403)
            self.end_headers()
            return
        self._send({"data": [{"id": "mock-a"}, {"id": "mock-b"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append(("POST", self.path, dict(self.headers), body))
        if self.path == "/v1/messages":                                   # Anthropic
            text = reply_for(body.get("system", "") + json.dumps(body["messages"]))
            if body.get("stream"):
                events = [{"type": "message_start"}, {"type": "content_block_start", "index": 0}]
                events += [{"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text[i:i + 7]}}
                           for i in range(0, len(text), 7)]
                events += [{"type": "content_block_stop", "index": 0}, {"type": "message_stop"}]
                self._send("".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode(), "text/event-stream")
            else:
                self._send({"content": [{"type": "text", "text": text}]})
        else:                                                             # OpenAI-compatible / Ollama
            text = reply_for(json.dumps(body["messages"]))
            if body.get("stream"):
                chunks = [f"data: {json.dumps({'choices': [{'delta': {'content': p}}]})}\n\n" for p in
                          ["<think>plan", "ning</think>"] + [text[i:i + 5] for i in range(0, len(text), 5)]]
                self._send(("".join(chunks) + "data: [DONE]\n\n").encode(), "text/event-stream")
            else:
                self._send({"choices": [{"message": {"content": "<think>x</think>" + text}}]})


def main():
    mock = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock)
    threading.Thread(target=mock.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{mock.server_port}"
    from utp.core import models as M
    report, fails = [], 0

    def check(ok, text):
        nonlocal fails
        fails += not ok
        report.append(f"[{'PASS' if ok else 'FAIL'}] {text}")

    # 1. the model connection
    msgs = [{"role": "system", "content": "be brief"}, {"role": "user", "content": "hi"}]
    for prov, url in (("anthropic", base), ("openai", base + "/v1"), ("ollama", base + "/v1")):
        m = M.Model(provider=prov, url=url, key="k-test" if prov != "ollama" else None, model="mock-a")
        got, streamed, names = m.chat(msgs), "".join(m.stream(msgs)), m.models()
        check(got == streamed == "Hello from the mock model." and names == ["mock-a", "mock-b"],
              f"{prov}: chat, streaming and model list ({got!r})")
    sent = [c for c in CALLS if c[1] == "/v1/messages"][-1]
    hdr = {k.lower(): v for k, v in sent[2].items()}
    check(hdr.get("x-api-key") == "k-test" and hdr.get("anthropic-version") == M.ANTHROPIC_VERSION
          and sent[3]["system"] == "be brief" and sent[3]["messages"] == [{"role": "user", "content": "hi"}],
          "anthropic: x-api-key and anthropic-version headers, system prompt moved to the top level")
    M.save_config({"provider": "anthropic", "url": base, "model": "mock-a", "keys": {"anthropic": "sk-secret"}})
    from utp.core import config as C
    pub = M.public_config()
    chat = [c for c in pub["connections"] if c["id"] == pub["roles"]["chat"]][0]
    check(M.Model().provider == "anthropic" and chat["key_set"] is True and "sk-secret" not in json.dumps(pub)
          and oct(os.stat(C.path()).st_mode)[-3:] == "600" and str(C.path()).startswith(str(TMP)),
          "settings file: provider and key saved (owner-only, in UTP_HOME), the key never shown")
    local = C.upsert_connection({"name": "Home box", "provider": "openai", "url": base + "/v1", "model": "mock-b"})
    C.update({"roles": {"build": local}})
    check(M.Model(role="build").model == "mock-b" and M.Model(role="chat").provider == "anthropic"
          and M.Model(connection=local).models() == ["mock-a", "mock-b"] and not C.needs_key("openai", base)
          and C.needs_key("openai", "https://api.openai.com/v1"),
          "settings: several connections, one to chat and another to build; a home server needs no key")
    C.update({"roles": {"build": pub["roles"]["chat"]}})
    C.delete_connection(local)
    v1 = TMP / "home-v1"
    v1.mkdir()
    (v1 / "config.json").write_text(json.dumps({"provider": "openai", "url": "http://x:1/v1", "model": "m1", "keys": {"openai": "k1"}}))
    os.environ["UTP_HOME"] = str(v1)
    old = C.load()
    os.environ["UTP_HOME"] = str(TMP / "home")
    check(old["version"] == 2 and old["connections"][0]["model"] == "m1" and list(old["secrets"].values()) == ["k1"],
          "settings: an old (version 1) settings file is carried over")

    # 2. a new language
    from utp.core import Pack, expand as X, newlang
    home = newlang.create("testlang", language="Testlang", order="SOV", branches=["high", "low"],
                          consonants="p t k m n s l r w y h sh")
    rows, errors, _ = newlang.first_build(home)
    want = ["pack.json", "sound_laws.json", "meanings.csv", "DESIGN.md", "README.md", "open.py",
            "build/lexicon.csv", "build/dictionary.md", "docs/grammar-card.md", "lab/index.html", "course/index.html"]
    missing = [w for w in want if not (home / w).exists()]
    check(not missing and not errors and len(rows) > 8000,
          f"new: {len(rows)} entries, {len(errors)} errors, missing {missing}")

    # 3. expand -> review -> apply
    pack = Pack("testlang")
    model = M.Model()
    path, batch = X.propose_batch(pack, "the night sky", model, n=10)
    status = {r["key"]: (r["status"], r["why"]) for r in batch}
    check(status["star-river"][0] == "proposed" and status["glimmerfrost"][0] == "proposed" and status["rain-house"][0] == "proposed"
          and "unknown part" in status["bad-one"][1] and "meaning already exists" in status["water-again"][1]
          and "names itself" in status["loop"][1],
          f"expand: 3 valid proposals kept, 3 rejected with reasons -> {path.name}")
    rows_b = X.read_batch(path)
    for r in rows_b:
        r["approve"] = "yes" if r["key"] in ("star-river", "glimmerfrost") else r["approve"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=X.FIELDS)
        w.writeheader()
        w.writerows(rows_b)
    lab_before = (home / "lab" / "index.html").stat().st_mtime_ns
    added, errs = X.apply_batch(pack, path, log=lambda s: None)
    lex = {r["key"]: r for r in Pack("testlang").rows()}
    check(added == 2 and not errs and lex["star-river"]["high"] and lex["glimmerfrost"]["kind"] == "root"
          and "rain-house" not in lex and (home / "lab" / "index.html").stat().st_mtime_ns > lab_before
          and all(r["status"] == "applied" for r in X.read_batch(path) if r["key"] in ("star-river", "glimmerfrost")),
          f"apply: only the 2 approved words joined ({lex.get('star-river', {}).get('high')}), Lab rebuilt, batch marked")

    # 4. sentences
    ok, bad = X.propose_sentences(Pack("testlang"), "basics", model, n=3)
    spath, n_added = X.add_sentences(Pack("testlang"), ok)
    from utp.core import learn
    learn.build_course(Pack("testlang"))
    course = (home / "course" / "index.html").read_text()
    check(len(ok) == 2 and len(bad) == 1 and "unknown keys" in bad[0]["why"] and n_added == 2 and ok[0]["v"] in course,
          f"sentences: 2 rendered and read back ({ok[0]['v']}), 1 rejected, both in the course")

    # 4b. the workshop: sources, audit, design, sound laws (utp/METHOD.md)
    from utp.core import workshop as W
    from utp.core.library import Sources
    whome = newlang.create("worklang", language="Worklang", order="SOV", branches=["north", "south"],
                           consonants="p t k m n s l r v th h y w")
    newlang.first_build(whome)
    wp = Pack("worklang")
    src = Sources(whome)
    note = TMP / "field-notes.md"
    note.write_text("# Field notes\n\nIn the north they call ice kethra. The southern word for dawn is sora. A velan is a sled.")
    doc, n = src.own.add_file(note, "canon")
    again = src.own.add_file(note, "canon")
    (whome / "sources" / "public").mkdir(parents=True, exist_ok=True)
    (whome / "sources" / "public" / "science-cold.md").write_text("# Cold\n\nIce forms when water freezes.")
    src.close()
    src = Sources(whome)
    hits = src.search("ice", k=5)
    check(doc == 1 and n == 1 and again == (1, 0) and {h["tier"] for h in hits} == {"canon", "science"}
          and src.passage("S1.1")["title"] == "field notes" and src.check_cites("S1.1 S7.7") == (["S1.1"], ["S7.7"])
          and (whome / "sources" / "files" / "field-notes.md").exists() and "library.sqlite" in (whome / "sources" / ".gitignore").read_text(),
          "library: files indexed once, searchable across tiers, public/ indexed automatically, citations checked")
    src.close()
    added, rejected = W.audit(wp, model, log=lambda s: None)
    att = {r["form"]: r for r in W.read_attested(wp)}
    why = {r["form"]: r["why"] for r in rejected}
    check(added == 3 and set(att) == {"kethra", "sora", "velan"} and att["sora"]["branch"] == "south"
          and att["kethra"]["tier"] == "canon" and "does not appear" in why.get("zzfake", "") and "not one of the passages" in why.get("Varo", ""),
          f"audit: words kept only if they appear in the passage they cite {why}")
    W.draft(wp, model, n=2, log=lambda s: None)
    q = W.read_decisions(wp)["questions"][0]
    check(len(q["options"]) == 2 and q["options"][0]["cites"] == ["S1.1"] and q["options"][0]["dropped_cites"] == ["S99.1"]
          and q["options"][1]["invention"] and len(W.question_bank()) >= 10,
          "design: options drafted from METHOD.md's questions; invented citations dropped, uncited options marked invention")
    W.decide(wp, q["id"], "A", "the field notes say so")
    design = (whome / "DESIGN.md").read_text()
    src = Sources(whome)
    top = src.search("Ice people", k=3)
    src.close()
    check("**Ice people.**" in design and "Why: the field notes say so" in design and "Sky people" in design
          and design.count(W.MARK) == 1 and top and top[0]["tier"] == "author",
          "design: a decision goes into DESIGN.md and into the library as an author source")
    prop = W.propose_sounds(wp, model)
    fits = {r["form"]: r["ok"] for r in prop["fit"]}
    check(prop["fits"] == 2 and fits == {"kethra": True, "sora": True, "velan": False},
          f"sounds: the engine runs the proposed laws on every attested word ({fits})")
    words, tests = W.accept_sounds(wp, fresh=False)
    from utp.core.builder import Builder
    rows_w, errs_w, _ = Builder(Pack("worklang")).build()
    keys = {r["form"]: r["key"] for r in W.read_attested(Pack("worklang"))}
    by = {r["key"]: r for r in rows_w}
    check(words == 2 and tests == 2 and by[keys["kethra"]]["north"] == "kethra" and by[keys["sora"]]["south"] == "sora"
          and by[keys["sora"]]["north"] == "sura" and not [e for e in errs_w if e[1] in ("E1", "E6")],
          f"sounds: accepted laws lock the attested words into the dictionary, checked by every build {[e for e in errs_w if e[1] in ('E1', 'E6')][:3]}")
    bpath, brows = X.propose_batch(Pack("worklang"), "the sky", model, n=5)
    star = next(r for r in brows if r["key"] == "star-river")
    check(star["sources"] == "S1.1" and "S42.1" in star["basis"] and "S1.1" in json.dumps(CALLS[-1][3]),
          "expand: prompts carry the language's sources; cited ids are checked and kept in the batch")

    # 5. the app server
    from utp.app import server as S
    srv = S.serve(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{srv.server_port}"

    def get(p):
        with urllib.request.urlopen(app + p) as r:
            return r.read().decode()

    def post(p, body, headers=None):
        req = urllib.request.Request(app + p, json.dumps(body).encode(), {"Content-Type": "application/json", **(headers or {})})
        with urllib.request.urlopen(req) as r:
            return r.read().decode()

    def events(text):
        return [json.loads(l[5:]) for l in text.split("\n") if l.startswith("data:")]

    langs = {l["id"]: l for l in json.loads(get("/api/languages"))["languages"]}
    check({"testlang", "vulcan"} <= set(langs) and langs["testlang"]["pages"].get("lab") == "languages/testlang/lab/index.html",
          "server: languages listed with their Lab and course pages")
    page = get("/files/languages/testlang/lab/index.html")
    check('window.UTP_LANGUAGE="testlang"' in page and "/ui/assistant.js" in page and "<html" in get("/"),
          "server: app page served; Lab pages get the tutor panel and know their language")
    tree = json.loads(get("/api/tree?path=languages/testlang"))
    check(any(e["name"] == "batches" for e in tree["entries"]), "server: file tree")
    chat = events(post("/api/chat", {"language": "testlang", "mode": "tutor", "messages": [{"role": "user", "content": "water?"}]}))
    sys_prompt = [c for c in CALLS if c[1] == "/v1/messages"][-1][3]["system"]
    check("".join(e.get("text", "") for e in chat) == "Hello from the mock model." and chat[-1].get("done")
          and "Dictionary entries for this request" in sys_prompt and "tutor of Testlang" in sys_prompt,
          "server: chat streams through Anthropic with the tutor prompt and dictionary entries")
    b = json.loads(post("/api/expand", {"language": "testlang", "topic": "rain", "n": 5}))
    ap = events(post("/api/apply", {"language": "testlang", "path": b["path"], "keys": ["rain-house"]}))
    check(b["path"].startswith("languages/testlang/batches/") and ap and ap[-1].get("done") and ap[-1].get("added") == 1
          and "rain-house" in {r["key"] for r in Pack("testlang").rows()},
          f"server: expand then apply the ticked word over HTTP {ap[-1:] if ap else ap}")
    nw = events(post("/api/new", {"name": "webmade", "order": "SVO", "consonants": "p t k m n s l r w y h"}))
    check(nw[-1].get("done") and (TMP / "languages" / "webmade" / "lab" / "index.html").exists(),
          "server: a new language created over HTTP, with Lab and course")
    run = events(post("/api/run", {"args": ["derive", "vulcan", "*sehaik"]}))
    check(any("rihann" in e.get("line", "") for e in run) and run[-1].get("code") == 0, "server: engine commands run")
    guards = []
    for fn in (lambda: get("/api/file?path=../../etc/passwd"),
               lambda: post("/api/run", {"args": ["rm", "-rf"]}),
               lambda: post("/api/config", {"model": "x"}, {"Origin": "https://evil.example"})):
        try:
            fn()
            guards.append(False)
        except urllib.error.HTTPError as e:
            guards.append(e.code in (400, 403))
    check(all(guards), f"server guards: paths outside the project, non-UTP commands and cross-site posts refused {guards}")
    origin = {"Origin": app}
    made = json.loads(post("/api/connections", {"connection": {"name": "Spare", "provider": "openai", "url": base + "/v1", "model": "mock-a"},
                                                "key": "sk-spare"}, origin))
    tested = json.loads(post("/api/connections/test", {"connection": {"id": made["id"], "provider": "openai", "url": base + "/v1", "model": "mock-a"}}, origin))
    shown = get("/api/settings")
    post("/api/connections/delete", {"id": made["id"]}, origin)
    ws = TMP / "writing"
    ws.mkdir()
    (ws / "notes.md").write_text("hello")
    post("/api/settings", {"paths": {"workspaces": [{"name": "Writing", "path": str(ws)}]}}, origin)
    roots = [e["path"] for e in json.loads(get("/api/tree"))["entries"] if e["root"]]
    note = json.loads(get("/api/file?path=ws/writing/notes.md"))
    chk = json.loads(post("/api/paths/check", {"path": str(ws)}, origin))
    try:
        get("/api/file?path=ws/writing/../../../etc/passwd")
        fenced = False
    except urllib.error.HTTPError as e:
        fenced = e.code in (400, 403)
    check(made["id"] == "spare" and tested["ok"] and tested["model_found"] and "sk-spare" not in shown and '"key_set": true' in shown
          and made["id"] not in get("/api/settings") and "ws/writing" in roots and note["text"] == "hello" and chk["writable"] and fenced,
          "server settings: connections added, tested and deleted, keys never shown; extra folders listed and fenced in")
    post("/api/settings", {"app": {"theme": "dark"}}, origin)
    lab_page, app_page = get("/files/languages/testlang/lab/index.html"), get("/")
    check('window.UTP_THEME="dark"' in lab_page and 'id="theme-toggle"' in lab_page and 'window.UTP_THEME="dark"' in app_page
          and lab_page.index("UTP_THEME") < lab_page.index("<style"),
          "theme: the saved light/dark choice reaches the app and every Lab and course before they paint")
    post("/api/settings", {"app": {"theme": "terminal", "layout": "padd", "year": 2375, "palette": "blue", "shape": "rounded"}}, origin)
    term_page = get("/files/languages/testlang/lab/index.html")
    check('window.UTP_THEME="terminal"' in term_page and '"layout": "padd"' in term_page and '"year": 2375' in term_page
          and ':root[data-theme="terminal"]' in term_page and "/ui/look.js" in get("/") and '"palette": "blue"' in term_page
          and '"shape": "rounded"' in term_page and "courier-prime.css" in term_page and "Courier Prime" in get("/ui/vendor/fonts/courier-prime.css"),
          "terminal: the Terminal theme, colour scheme, control shape, PADD layout, stardate year and font reach every page")
    import base64
    up = json.loads(post("/api/sources/add", {"language": "worklang", "tier": "licensed", "files": [
        {"name": "glossary.html", "data": base64.b64encode(b"<html><body><nav>x</nav><p>A thraal is a snow hare.</p></body></html>").decode()}]}, origin))
    found = json.loads(get("/api/sources/search?language=worklang&q=hare"))["hits"]
    shown_p = json.loads(get(f"/api/sources/passage?language=worklang&id={found[0]['id']}"))
    try:
        post("/api/attested/set", {"language": "worklang", "add": {"form": "nothere", "cite": found[0]["id"]}}, origin)
        refused = False
    except urllib.error.HTTPError as e:
        refused = e.code == 400
    post("/api/attested/set", {"language": "worklang", "add": {"form": "thraal", "gloss": "snow hare", "cite": found[0]["id"]}}, origin)
    att_http = json.loads(get("/api/attested?language=worklang"))
    des_http = json.loads(get("/api/design?language=worklang"))
    snd_http = json.loads(get("/api/sounds?language=worklang"))
    check(up["added"][0]["passages"] == 1 and found and found[0]["tier"] == "licensed" and "snow hare" in shown_p["text"]
          and "x" not in shown_p["text"].split() and refused and any(r["form"] == "thraal" and r["tier"] == "licensed" for r in att_http["rows"])
          and des_http["questions"][0]["status"] == "decided" and snd_http["proposal"]["fits"] == 2,
          "server workshop: sources uploaded and searched, attested words checked against their passage, design and sounds served")
    # web search through SearXNG, pages into the private library
    from utp.core import websearch as WS
    C.update({"search": {"searxng": base}})
    res = WS.search("ice hare")
    lib_w = Sources(whome)
    cid, n_w, title_w = WS.add_url(lib_w.own, res[0]["url"], "science")
    wiki_text = lib_w.passage(cid + ".1")["text"]
    try:
        WS.fetch(base + "/blocked")
        blocked = ""
    except WS.SearchError as e:
        blocked = str(e)
    lib_w.close()
    nojson = WS.test(base + "/nojson")
    check(len(res) == 2 and res[0]["engine"] == "mock" and res[1]["engine"] == "a, b" and title_w == "Ice hare" and n_w == 1
          and "thraal" in wiki_text and "Menu" not in wiki_text and "save the page" in blocked and not nojson["ok"]
          and "json" in nojson["problem"] and WS.suggest_tier("https://memory-alpha.fandom.com/wiki/Aenar") == "canon"
          and WS.suggest_tier("https://memory-beta.fandom.com/wiki/Andorii") == "licensed",
          "web search: SearXNG results, wiki pages read through their API, blocked sites and JSON-off explained")
    web = json.loads(get("/api/search?language=worklang&q=ice"))
    got = json.loads(post("/api/sources/url", {"language": "worklang", "urls": [{"url": base + "/notes.html", "tier": "fan"},
                                                                              {"url": base + "/blocked"}]}, origin))
    page_src = json.loads(get("/api/sources?language=worklang"))
    check(web["results"][0]["have"] and not web["results"][1]["have"] and got["added"][0]["passages"] >= 1
          and got["added"][0]["title"] == "Snow notes" and "403" in got["added"][1]["problem"] and page_src["web"]
          and any(d["url"] == base + "/notes.html" and d["tier"] == "fan" for d in page_src["docs"])
          and json.loads(post("/api/search/test", {}, origin))["ok"],
          "server web search: results marked when already in the library; ticked pages fetched with their tier")
    about = json.loads(get("/api/about"))
    check(about["repo"] == str(S.REPO) and about["python"], "server: the About section")
    srv.shutdown()

    # 5b. double-click launchers in each language folder
    from utp.app import launch
    bat = (TMP / "languages" / "webmade" / "Open Webmade.bat").read_bytes()
    cmd = TMP / "languages" / "webmade" / "Open Webmade.command"
    check(b'set "REPO=' in bat and b"\r\n" in bat and os.access(cmd, os.X_OK) and (TMP / "languages" / "webmade" / "open.py").exists()
          and not launch.running(1),
          "launchers: each language folder gets Open <Language>.command / .bat and open.py")

    # 6. Vulcan's own pipeline, on a copy of the repository
    copy = TMP / "repo"
    shutil.copytree(REPO, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "build",
                                                                   "vuhlkansu-lab.html", "vuhlkansu-course.html", "languages"))
    code = r'''
import sys, csv, json
sys.path.insert(0, ".")
from utp.core import Pack, expand as X
p = Pack("vulcan")
rows = X.validate(p, p.rows(), [
    {"key": "star-road", "gloss": "the path of the stars (galactic plane)", "pos": "noun", "field": "nature", "era": "Classical",
     "register": "everyday", "kind": "compound", "parts": "{star}-{road}", "basis": "test"},
    {"key": "dawnfrost", "gloss": "frost at dawn", "pos": "noun", "field": "nature", "era": "Classical", "kind": "root", "basis": "test"}], "test")
for r in rows: r["approve"] = "yes"
path = X.write_batch(p, "test", rows)
added, errs = X.apply_batch(p, path, log=lambda s: None)
lex = {r["key"]: r for r in Pack("vulcan").rows()}
print(json.dumps({"added": added, "errs": len(errs), "star": lex.get("star-road", {}).get("vulcan"), "dawn": lex.get("dawnfrost", {}).get("vulcan"),
                  "status": [r["status"] for r in rows]}))
'''
    res = subprocess.run([sys.executable, "-c", code], cwd=copy, capture_output=True, text=True,
                         env={**os.environ, "UTP_LANGUAGES": str(copy / "languages")})
    try:
        out = json.loads(res.stdout.strip().splitlines()[-1])
    except Exception:
        out = {"error": (res.stdout + res.stderr)[-800:]}
    check(out.get("added") == 2 and out.get("errs") == 0 and out.get("star") and out.get("dawn"),
          f"vulcan: a batch runs derivation.py, lexicon.py build, export and the Lab/course builders cleanly {out}")

    mock.shutdown()
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n".join(report))
    print("ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
