"""The UTP app: chat, files, Labs, courses and every engine tool, served on this machine.

  python3 utp/app/server.py [--port 8765] [--open] [--language vulcan] [--page lab|course]
  python3 utp/utp.py app                       the same
  desktop/  (Electron)                         the same, in its own window

Standard library only, so it runs anywhere Python 3.8+ runs, with or without internet.
It listens on 127.0.0.1 only. The model is whatever utp.py config (or the Settings
screen) chose: Anthropic, an OpenAI-compatible server, or Ollama.
"""
import argparse
import csv
import json
import mimetypes
import os
import pathlib
import re
import subprocess
import sys
import threading
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

from utp.core import expand as X  # noqa: E402
from utp.core import interlingua as I  # noqa: E402
from utp.core import learn, llm, models as M, newlang  # noqa: E402
from utp.core.pack import LANGUAGES, Pack, available  # noqa: E402

UI = HERE / "ui"
HIDDEN = {".git", "__pycache__", "node_modules", ".DS_Store", "dist", "out"}
EDITABLE = {".md", ".csv", ".json", ".txt"}
MAX_READ = 2_000_000
RUNNABLE = {"build", "new", "expand", "apply", "sentences", "topics", "lab", "course", "card", "stats", "packs",
            "derive", "root", "tree", "profile", "context", "render", "parse", "models", "export", "propose", "curate"}
OUTSIDE = LANGUAGES.resolve() != (REPO / "languages").resolve()      # languages kept outside the repository


def resolve(rel):
    """A path the app may show: inside the repository, or inside the languages folder."""
    rel = (rel or "").strip("/")
    if rel == "languages" or rel.startswith("languages/"):
        base, rest = LANGUAGES.resolve(), rel[len("languages"):].strip("/")
    else:
        base, rest = REPO, rel
    p = (base / rest).resolve()
    if p != base and base not in p.parents:
        raise PermissionError("outside the project")
    return p


def relpath(p):
    p = pathlib.Path(p).resolve()
    lang = LANGUAGES.resolve()
    if p == lang or lang in p.parents:
        return "languages/" + str(p.relative_to(lang)).replace(os.sep, "/") if p != lang else "languages"
    return str(p.relative_to(REPO)).replace(os.sep, "/")


def language_of(path):
    """The language whose folder holds this file, if any."""
    path = pathlib.Path(path).resolve()
    for name in available():
        try:
            home = Pack(name).home
        except Exception:
            continue
        if path == home or home in path.parents:
            return name
    return None


def ensure_pages(p):
    """Build a language's Lab and course if they are missing (a fresh clone keeps only their sources)."""
    try:
        if p.buildable and p.path("lexicon").exists():
            if not (p.learning("lab") and p.learning("lab").exists()) or not (p.learning("course") and p.learning("course").exists()):
                learn.build_all(p)
        elif "expand" in p.meta:
            if p.learning("utp_lab") and not p.learning("utp_lab").exists():
                learn.build_lab(p)
            cwd = (p.root / p.meta["expand"]["cwd"]).resolve()
            for key, tool in (("lab", "build_lab.py"), ("course", "build_course.py")):
                f = p.learning(key)
                if f and not f.exists() and (cwd / "tools" / tool).exists():
                    subprocess.run([sys.executable, f"tools/{tool}"], cwd=cwd, capture_output=True)
    except Exception:
        traceback.print_exc()


def languages():
    out = []
    for name in available():
        try:
            p = Pack(name)
        except Exception as e:
            out.append({"id": name, "error": str(e)})
            continue
        ensure_pages(p)
        pages = {}
        for key in ("lab", "course", "utp_lab"):
            f = p.learning(key)
            if f and f.exists():
                pages[key] = relpath(f)
        if "utp_lab" not in pages and "lab" in pages and p.buildable:
            pages["utp_lab"] = pages["lab"]
        try:
            n = sum(1 for _ in open(p.path("lexicon"))) - 1
        except OSError:
            n = 0
        out.append({"id": name, "language": p.meta.get("language", p.name), "name": p.name, "buildable": p.buildable,
                    "expandable": p.buildable or "expand" in p.meta, "home": relpath(p.home), "pages": pages,
                    "entries": n, "branches": p.meta["derivation"]["branches"], "fixture": name == "sample"})
    return out


# ---------- chat ----------
def system_prompt(language, mode, messages, files):
    parts = []
    if language:
        pack = Pack(language)
        lang = pack.meta.get("language", pack.name)
        if mode == "tutor":
            parts.append(llm.section("Tutor").replace("{LANGUAGE}", lang).replace("{LEVEL}", "beginner"))
        elif mode == "translator":
            parts.append(llm.section("Translator and writer"))
        else:
            parts.append(llm.section("Assistant in the app"))
        recent = " ".join(m["content"] for m in messages[-4:] if m["role"] == "user")
        parts.append(llm.context(pack, recent, limit=40))
        notes = X.design_notes(pack, 2500)
        if notes and mode != "tutor":
            parts.append("Design notes for this language:\n" + notes)
    else:
        parts.append("You are the assistant in the UTP app, a toolkit for building constructed languages "
                     "(sound laws, roots, derivation, dictionaries, grammar frames, Labs and courses). "
                     "Help the person design, build, learn and write in their languages. When they ask for new "
                     "vocabulary, suggest the Grow tool or `utp.py expand` rather than inventing words.")
        readme = REPO / "README.md"
        if readme.exists():
            parts.append(readme.read_text()[:3000])
    for rel in files or []:
        try:
            p = resolve(rel)
            parts.append(f"File {rel}:\n```\n{p.read_text(errors='replace')[:20000]}\n```")
        except Exception as e:
            parts.append(f"(could not read {rel}: {e})")
    return "\n\n".join(parts)


ASSISTANT_TAG = '<script>window.UTP_LANGUAGE={lang};</script><script src="/ui/assistant.js" defer></script>'


class Handler(BaseHTTPRequestHandler):
    server_version = "UTP/1"

    def log_message(self, fmt, *args):
        if os.environ.get("UTP_LOG"):
            sys.stderr.write("%s\n" % (fmt % args))

    # ---------- plumbing ----------
    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        data = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        self._send(code, obj)

    def _error(self, msg, code=400):
        self._json({"error": str(msg)}, code)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def _sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _sse(self, obj):
        self.wfile.write(b"data: " + json.dumps(obj, ensure_ascii=False).encode() + b"\n\n")
        self.wfile.flush()

    def _same_origin(self):
        origin = self.headers.get("Origin")
        if not origin or origin == "null":
            return True
        host = urllib.parse.urlparse(origin)
        return host.hostname in ("127.0.0.1", "localhost") and str(host.port) == str(self.server.server_port)

    # ---------- routes ----------
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                return self._static(UI / "index.html")
            if u.path.startswith("/ui/"):
                return self._static(UI / u.path[4:])
            if u.path.startswith("/files/"):
                return self._file(urllib.parse.unquote(u.path[7:]))
            route = {"/api/health": self.health, "/api/languages": lambda q: self._json({"languages": languages()}),
                     "/api/tree": self.tree, "/api/file": self.read_file, "/api/config": self.get_config,
                     "/api/models": self.list_models, "/api/batches": self.batches, "/api/batch": self.batch}.get(u.path)
            if not route:
                return self._error("not found", 404)
            route(q)
        except PermissionError as e:
            self._error(e, 403)
        except FileNotFoundError as e:
            self._error(f"not found: {e}", 404)
        except Exception as e:
            traceback.print_exc()
            self._error(f"{type(e).__name__}: {e}", 500)

    def do_POST(self):
        if not self._same_origin():
            return self._error("cross-site request refused", 403)
        u = urllib.parse.urlparse(self.path)
        try:
            body = self._body()
            route = {"/api/chat": self.chat, "/api/config": self.set_config, "/api/file": self.write_file,
                     "/api/derive": self.derive, "/api/compound": self.compound, "/api/gloss": self.gloss,
                     "/api/render": self.render, "/api/expand": self.expand, "/api/apply": self.apply,
                     "/api/sentences": self.sentences, "/api/sentences/add": self.sentences_add,
                     "/api/topics": self.topics, "/api/new": self.new, "/api/run": self.run,
                     "/api/rebuild": self.rebuild}.get(u.path)
            if not route:
                return self._error("not found", 404)
            route(body)
        except M.ModelError as e:
            self._error(e, 502)
        except PermissionError as e:
            self._error(e, 403)
        except Exception as e:
            traceback.print_exc()
            self._error(f"{type(e).__name__}: {e}", 500)

    # ---------- files ----------
    def _static(self, p):
        p = p.resolve()
        if UI not in p.parents or not p.is_file():
            return self._error("not found", 404)
        self._send(200, p.read_bytes(), (mimetypes.guess_type(p.name)[0] or "application/octet-stream") +
                   ("; charset=utf-8" if p.suffix in (".html", ".js", ".css") else ""))

    def _file(self, rel):
        p = resolve(rel)
        if not p.is_file():
            return self._error("not found", 404)
        data = p.read_bytes()
        ctype = mimetypes.guess_type(p.name)[0] or "text/plain"
        if p.suffix in (".html", ".htm"):
            lang = language_of(p)
            tag = ASSISTANT_TAG.format(lang=json.dumps(lang)).encode()
            data = data.replace(b"</body>", tag + b"</body>", 1) if b"</body>" in data else data + tag
            ctype = "text/html; charset=utf-8"
        elif ctype.startswith("text/") or p.suffix in (".md", ".csv", ".json", ".py"):
            ctype = "text/plain; charset=utf-8"
        self._send(200, data, ctype)

    def tree(self, q):
        p = resolve(q.get("path", ""))
        entries = []
        if p.is_dir():
            kids = list(p.iterdir())
            if p == REPO and OUTSIDE:
                kids.append(LANGUAGES)
            for c in sorted(kids, key=lambda c: (not c.is_dir(), c.name.lower())):
                if c.name in HIDDEN or (c.name.startswith(".") and c.name not in (".gitignore",)):
                    continue
                if not c.exists():
                    continue
                entries.append({"name": c.name if c != LANGUAGES else "languages", "path": relpath(c),
                                "dir": c.is_dir(), "size": c.stat().st_size if c.is_file() else None})
        self._json({"path": relpath(p) if p != REPO else "", "entries": entries})

    def read_file(self, q):
        p = resolve(q["path"])
        size = p.stat().st_size
        with open(p, "rb") as f:
            raw = f.read(MAX_READ)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return self._json({"path": q["path"], "binary": True, "size": size})
        self._json({"path": q["path"], "text": text, "size": size, "truncated": size > MAX_READ,
                    "editable": p.suffix in EDITABLE, "language": language_of(p)})

    def write_file(self, b):
        p = resolve(b["path"])
        if p.suffix not in EDITABLE:
            raise PermissionError(f"only {', '.join(sorted(EDITABLE))} files can be edited here")
        p.write_text(b["text"])
        self._json({"saved": b["path"]})

    # ---------- model ----------
    def health(self, q):
        m = M.Model()
        self._json({"ok": True, "provider": m.provider, "model": f"{m.model} ({m.provider})", "repo": str(REPO)})

    def get_config(self, q):
        self._json(M.public_config())

    def set_config(self, b):
        cfg = {k: b[k] for k in ("provider", "url", "model") if b.get(k) is not None}
        if b.get("key") is not None:
            cfg["keys"] = {b.get("provider") or M.Model().provider: b["key"]}
        M.save_config(cfg)
        self._json(M.public_config())

    def list_models(self, q):
        try:
            self._json({"models": M.Model(provider=q.get("provider") or None).models()})
        except M.ModelError as e:
            self._json({"models": [], "error": str(e)})

    def chat(self, b):
        messages = [m for m in b.get("messages", []) if m.get("role") in ("user", "assistant") and m.get("content")]
        system = system_prompt(b.get("language"), b.get("mode", "assistant"), messages, b.get("files"))
        model = M.Model()
        self._sse_start()
        try:
            for piece in model.stream([{"role": "system", "content": system}] + messages):
                self._sse({"text": piece})
            self._sse({"done": True})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            self._sse({"error": str(e)})

    # ---------- engine ----------
    def derive(self, b):
        pack = Pack(b["language"])
        proto = b["proto"].strip().lstrip("*")
        std = pack.meta["derivation"]["standard"]
        rows = []
        for br in pack.laws.branches:
            res, trace = pack.laws.apply(proto, br, trace=True)
            rows.append({"branch": br, "form": pack.spell(res) if br == std else res,
                         "trace": [" > ".join(t) for t in trace]})
        ok, why = pack.phonotactics.check(proto)
        self._json({"branches": rows, "legal": ok, "why": why})

    def compound(self, b):
        pack = Pack(b["language"])
        d = pack.deriver()
        self._json({"forms": {br: d._compound(b["parts"], br) for br in pack.meta["derivation"]["branches"]}})

    def gloss(self, b):
        pack = Pack(b["language"])
        rd = I.Reader(pack)
        gl = {r["key"]: r["gloss"] for r in pack.rows()}
        words = []
        for w in b["text"].split():
            core = w.strip(".,?!:;")
            t = rd.word(core) or {}
            key = t.get("key", "").split("+")[0]
            words.append({"w": w, "key": key or None, "name": t.get("name"), "gloss": gl.get(key, ""), "marks": t.get("marks", [])})
        try:
            frame = I.parse(pack, b["text"])
        except Exception:
            frame = None
        self._json({"words": words, "frame": frame})

    def render(self, b):
        pack = Pack(b["language"])
        t, text, why = X.check_frame(pack, b["frame"])
        self._json({"template": t, "text": text if text else why, "why": why})

    # ---------- growing a language ----------
    def expand(self, b):
        pack = Pack(b["language"])
        path, rows = X.propose_batch(pack, b["topic"], M.Model(), n=int(b.get("n", 30)), extra=b.get("extra", ""))
        self._json({"name": path.stem, "path": relpath(path), "rows": rows})

    def batches(self, q):
        pack = Pack(q["language"])
        out = []
        for p in sorted(X.batches_dir(pack).glob("*.csv"), reverse=True):
            rows = X.read_batch(p)
            out.append({"name": p.stem, "path": relpath(p), "proposed": sum(r.get("status") == "proposed" for r in rows),
                        "applied": sum(r.get("status") == "applied" for r in rows)})
        self._json({"batches": out})

    def batch(self, q):
        p = resolve(q["path"])
        self._json({"name": p.stem, "path": q["path"], "rows": X.read_batch(p)})

    def apply(self, b):
        pack = Pack(b["language"])
        path = resolve(b["path"])
        if "keys" in b:                                    # the ticks from the Lab or the app
            rows = X.read_batch(path)
            for r in rows:
                if r.get("status") == "proposed":
                    r["approve"] = "yes" if r["key"] in b["keys"] else ""
            with open(path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=X.FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
        self._sse_start()
        try:
            added, errors = X.apply_batch(pack, path, log=lambda line: self._sse({"line": line}))
            for e in errors[:20]:
                self._sse({"line": "error: " + " ".join(map(str, e))[:500]})
            self._sse({"done": True, "added": added, "errors": len(errors)})
        except Exception as e:
            self._sse({"error": f"{type(e).__name__}: {e}"})

    def rebuild(self, b):
        pack = Pack(b["language"])
        self._sse_start()
        try:
            errors = X.rebuild(pack, log=lambda line: self._sse({"line": line}))
            self._sse({"done": True, "errors": len(errors)})
        except Exception as e:
            self._sse({"error": f"{type(e).__name__}: {e}"})

    def sentences(self, b):
        pack = Pack(b["language"])
        ok, bad = X.propose_sentences(pack, b["topic"], M.Model(), n=int(b.get("n", 8)))
        self._json({"ok": ok, "bad": bad})

    def sentences_add(self, b):
        pack = Pack(b["language"])
        path, added = X.add_sentences(pack, b["sentences"])
        if pack.buildable:
            learn.build_course(pack)
        self._json({"added": added, "path": relpath(path)})

    def topics(self, b):
        pack = Pack(b["language"])
        self._json({"topics": X.suggest_topics(pack, M.Model() if b.get("ai") else None)})

    def new(self, b):
        self._sse_start()
        try:
            home = newlang.create(b["name"], language=b.get("language") or None, order=b.get("order", "SOV"),
                                  branches=str(b.get("branches") or "standard").split(","),
                                  eras=str(b.get("eras") or "Ancient,Old,Middle,Modern").split(","),
                                  consonants=b.get("consonants") or newlang.DEFAULT_CONSONANTS,
                                  vowels=b.get("vowels") or newlang.DEFAULT_VOWELS, about=b.get("about", ""))
            if b.get("design"):
                (home / "DESIGN.md").write_text((home / "DESIGN.md").read_text().replace(
                    "## Who speaks it\n", "## Who speaks it\n\n" + b["design"].strip() + "\n", 1))
            self._sse({"line": f"created {relpath(home)}"})
            rows, errors, warnings = newlang.first_build(home)
            self._sse({"line": f"first build: {len(rows)} entries, {len(errors)} errors; Lab and course written"})
            self._sse({"done": True, "id": home.name, "home": relpath(home)})
        except Exception as e:
            self._sse({"error": f"{type(e).__name__}: {e}"})

    def run(self, b):
        args = [str(a) for a in b.get("args", [])]
        if not args or args[0] not in RUNNABLE:
            return self._error(f"not a UTP command (one of: {', '.join(sorted(RUNNABLE))})")
        self._sse_start()
        proc = subprocess.Popen([sys.executable, str(REPO / "utp" / "utp.py"), *args], cwd=REPO, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            self._sse({"line": line.rstrip("\n")})
        self._sse({"done": True, "code": proc.wait()})


def serve(port=8765, host="127.0.0.1"):
    for p in ([port, 0] if port else [0]):
        try:
            return ThreadingHTTPServer((host, p), Handler)
        except OSError:
            continue
    raise OSError("no free port")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true", help="open the app in the browser")
    ap.add_argument("--language")
    ap.add_argument("--page", choices=["lab", "course"])
    ap.add_argument("--print-port", action="store_true", help="print UTP_PORT=<port> (for the desktop shell)")
    a = ap.parse_args(argv)
    srv = serve(a.port)
    port = srv.server_port
    url = f"http://127.0.0.1:{port}/"
    if a.language and a.page:
        page = next((l["pages"].get("utp_lab" if a.page == "lab" else "course") or l["pages"].get(a.page)
                     for l in languages() if l["id"] == a.language), None)
        url += f"files/{page}" if page else f"#lang={a.language}"
    elif a.language:
        url += f"#lang={a.language}"
    if a.print_port:
        print(f"UTP_PORT={port}", flush=True)
    print(f"UTP app: {url}   (Ctrl+C to stop)", flush=True)
    if a.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
