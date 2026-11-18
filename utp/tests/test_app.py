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
     "era": "Old", "kind": "compound", "parts": "{star}-{river}", "basis": "Japanese ama-no-gawa 'heaven's river'"},
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


def reply_for(text):
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
