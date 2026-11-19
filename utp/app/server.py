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
from utp.core import config as C  # noqa: E402
from utp.core import learn, llm, models as M, newlang  # noqa: E402
from utp.core.pack import Pack, available, languages_dir  # noqa: E402

UI = HERE / "ui"
HIDDEN = {".git", "__pycache__", "node_modules", ".DS_Store", "dist", "out"}
EDITABLE = {".md", ".csv", ".json", ".txt"}
MAX_READ = 2_000_000
RUNNABLE = {"build", "new", "expand", "apply", "sentences", "topics", "lab", "course", "card", "stats", "packs",
            "derive", "root", "tree", "profile", "context", "render", "parse", "models", "export", "propose", "curate",
            "sources", "audit", "sounds"}


def roots():
    """The folders the app may show: the repository, the languages folder, and your workspaces.
    Paths the page sees: "<repo path>", "languages/<…>", "ws/<name>/<…>"."""
    r = {"": REPO, "languages": languages_dir().resolve()}
    for w in C.workspaces():
        r["ws/" + w["name"]] = w["path"].resolve()
    return r


def resolve(rel):
    """A path the app may show, from the page's form of it; anything else is refused."""
    rel = (rel or "").replace("\\", "/").strip("/")
    base, rest = REPO, rel
    for prefix, folder in sorted(roots().items(), key=lambda kv: -len(kv[0])):
        if prefix and (rel == prefix or rel.startswith(prefix + "/")):
            base, rest = folder, rel[len(prefix):].strip("/")
            break
    p = (base / rest).resolve()
    if p != base and base not in p.parents:
        raise PermissionError("outside the folders this app may show")
    return p


def relpath(p):
    p = pathlib.Path(p).resolve()
    for prefix, folder in sorted(roots().items(), key=lambda kv: -len(kv[0])):
        if prefix and (p == folder or folder in p.parents):
            rest = str(p.relative_to(folder)).replace(os.sep, "/")
            return prefix if rest == "." else f"{prefix}/{rest}"
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


def theme_tag():
    t = C.load().get("app", {}).get("theme", "system")
    t = t if t in ("system", "light", "dark") else "system"
    return (f'<script>window.UTP_THEME={json.dumps(t)};'
            f'if(UTP_THEME!=="system")document.documentElement.dataset.theme=UTP_THEME;</script>').encode()


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
                     "/api/settings": lambda q: self._json(C.public()), "/api/about": self.about,
                     "/api/tree": self.tree, "/api/file": self.read_file, "/api/config": self.get_config,
                     "/api/models": self.list_models, "/api/batches": self.batches, "/api/batch": self.batch,
                     "/api/sources": self.sources, "/api/sources/search": self.sources_search,
                     "/api/sources/passage": self.sources_passage, "/api/attested": self.attested,
                     "/api/design": self.design, "/api/sounds": self.sounds}.get(u.path)
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
                     "/api/rebuild": self.rebuild, "/api/settings": self.set_settings,
                     "/api/connections": self.save_connection, "/api/connections/delete": self.delete_connection,
                     "/api/connections/test": self.test_connection, "/api/speech/test": self.test_speech,
                     "/api/paths/check": self.check_path, "/api/shortcut": self.shortcut,
                     "/api/sources/add": self.sources_add, "/api/sources/remove": self.sources_remove,
                     "/api/audit": self.audit, "/api/attested/set": self.attested_set,
                     "/api/design/draft": self.design_draft, "/api/design/decide": self.design_decide,
                     "/api/design/ask": self.design_ask, "/api/sounds/propose": self.sounds_propose,
                     "/api/sounds/accept": self.sounds_accept}.get(u.path)
            if not route:
                return self._error("not found", 404)
            route(body)
        except M.ModelError as e:
            self._error(e, 502)
        except (ValueError, KeyError) as e:
            self._error(e, 400)
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
        data = p.read_bytes()
        if p.suffix == ".html":
            data = re.sub(rb"(<head[^>]*>)", lambda m: m.group(1) + theme_tag(), data, count=1)
        self._send(200, data, (mimetypes.guess_type(p.name)[0] or "application/octet-stream") +
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
            data = theme_tag() + data if not data.lstrip().lower().startswith(b"<!doctype") else \
                re.sub(rb"(<head[^>]*>)", lambda m: m.group(1) + theme_tag(), data, count=1)
            ctype = "text/html; charset=utf-8"
        elif ctype.startswith("text/") or p.suffix in (".md", ".csv", ".json", ".py"):
            ctype = "text/plain; charset=utf-8"
        self._send(200, data, ctype)

    def tree(self, q):
        rel = q.get("path", "")
        p = resolve(rel)
        entries = []
        if p.is_dir():
            kids = [(c, None) for c in p.iterdir()]
            if not rel:                                   # the top: the repository, plus folders that live elsewhere
                lang = languages_dir().resolve()
                if lang.parent != REPO:
                    kids.append((lang, "languages"))
                for w in C.workspaces():
                    kids.append((w["path"], w["label"]))
            for c, label in sorted(kids, key=lambda k: (k[1] is not None, not k[0].is_dir(), k[0].name.lower())):
                if c.name in HIDDEN or (c.name.startswith(".") and c.name != ".gitignore" and label is None):
                    continue
                if not c.exists():
                    continue
                entries.append({"name": label or c.name, "path": relpath(c), "dir": c.is_dir(),
                                "size": c.stat().st_size if c.is_file() else None, "root": label is not None})
        self._json({"path": rel, "entries": entries})

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
        b = M.Model(role="build")
        self._json({"ok": True, "provider": m.provider, "model": f"{m.model} ({m.provider})", "connection": m.connection,
                    "build": f"{b.model} ({b.provider})", "repo": str(REPO), "config": str(C.path())})

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
            self._json({"models": M.Model(connection=q.get("connection") or None,
                                          role=q.get("role") or "chat").models()})
        except M.ModelError as e:
            self._json({"models": [], "error": str(e)})

    # ---------- settings ----------
    def set_settings(self, b):
        if "paths" in b:
            for w in b["paths"].get("workspaces", []):
                if not pathlib.Path(w.get("path", "")).expanduser().is_dir():
                    raise ValueError(f"not a folder: {w.get('path')}")
            lang = b["paths"].get("languages")
            if lang:
                pathlib.Path(lang).expanduser().mkdir(parents=True, exist_ok=True)
        C.update(b)
        self._json(C.public())

    def save_connection(self, b):
        cid = C.upsert_connection(b["connection"], key=b.get("key"))
        if b.get("roles"):
            C.update({"roles": {r: cid for r in b["roles"] if r in C.ROLES}})
        self._json({"id": cid, "settings": C.public()})

    def delete_connection(self, b):
        C.delete_connection(b["id"])
        self._json(C.public())

    def test_connection(self, b):
        """Test a saved connection, or a draft from the form (its key, or the saved one if blank)."""
        d = b.get("connection") or {}
        saved = C.connection(d.get("id")) if d.get("id") else {}
        key = b.get("key") or (saved.get("key") if saved.get("provider") == d.get("provider") else "") or None
        try:
            m = M.Model(provider=d.get("provider"), url=d.get("url") or None, model=d.get("model") or None, key=key,
                        connection=d.get("id"), timeout=15)
            if m.needs_key() and not m.key:
                return self._json({"ok": False, "problem": "this server needs an API key"})
            names = m.models()
            self._json({"ok": True, "models": names, "model_found": m.model in names})
        except Exception as e:
            self._json({"ok": False, "problem": str(e)})

    def test_speech(self, b):
        from utp.core.speech import Kokoro
        k = Kokoro(b.get("url") or None)
        self._json({"ok": k.available(), "url": k.url})

    # ---------- the workshop: sources, attested words, design, sound laws ----------
    def _src(self, lang):
        from utp.core.library import Sources
        return Sources(Pack(lang).home)

    def sources(self, q):
        from utp.core.library import TIERS, embedder
        src = self._src(q["language"])
        try:
            self._json({"docs": src.docs(), "passages": src.count(), "tiers": TIERS,
                        "embeddings": bool(embedder()[1]), "folder": relpath(src.dir)})
        finally:
            src.close()

    def sources_search(self, q):
        src = self._src(q["language"])
        try:
            tiers = [t for t in (q.get("tiers") or "").split(",") if t] or None
            self._json({"hits": src.search(q.get("q", ""), k=int(q.get("k", 12)), tiers=tiers)})
        finally:
            src.close()

    def sources_passage(self, q):
        src = self._src(q["language"])
        try:
            p = src.passage(q.get("id", ""))
            self._json(p) if p else self._error("no such passage", 404)
        finally:
            src.close()

    def sources_add(self, b):
        import base64
        import tempfile
        src = self._src(b["language"])
        try:
            lib, tier, out = src.lib(bool(b.get("shared"))), b.get("tier") or "canon", []
            for f in b.get("files", []):
                name = pathlib.Path(f["name"]).name
                with tempfile.TemporaryDirectory() as tmp:
                    path = pathlib.Path(tmp) / name
                    path.write_bytes(base64.b64decode(f["data"]))
                    try:
                        doc, n = lib.add_file(path, tier, b.get("title") if len(b["files"]) == 1 else None,
                                              url=b.get("url", ""))
                        out.append({"name": name, "id": f"{lib.prefix}{doc}", "passages": n})
                    except ValueError as e:
                        out.append({"name": name, "problem": str(e)})
            if (b.get("text") or "").strip():
                doc, n = lib.add_text(b["text"], b.get("title") or "Pasted text", tier, url=b.get("url", ""))
                out.append({"name": b.get("title") or "Pasted text", "id": f"{lib.prefix}{doc}", "passages": n})
            self._json({"added": out})
        finally:
            src.close()

    def sources_remove(self, b):
        src = self._src(b["language"])
        try:
            cid = str(b["id"])
            src.libs["G" if cid.upper().startswith("G") else "S"].remove(int(cid.lstrip("SGsg")))
            self._json({"ok": True})
        finally:
            src.close()

    def audit(self, b):
        from utp.core import workshop as W
        pack = Pack(b["language"])
        self._sse_start()
        try:
            added, rejected = W.audit(pack, M.Model(role="build"), query=b.get("query") or None,
                                      max_passages=int(b.get("max") or 240), log=lambda line: self._sse({"line": line}))
            for r in rejected[:40]:
                self._sse({"line": f"rejected {r['form']}: {r['why']}"})
            self._sse({"done": True, "added": added, "rejected": len(rejected)})
        except Exception as e:
            self._sse({"error": f"{type(e).__name__}: {e}"})

    def attested(self, q):
        from utp.core import workshop as W
        pack = Pack(q["language"])
        self._json({"rows": W.read_attested(pack), "problems": dict(W.check_attested(pack)),
                    "branches": pack.meta["derivation"]["branches"]})

    def attested_set(self, b):
        """Change a row's status (attested, doubtful, rejected), or add a row by hand (checked against its source)."""
        from utp.core import workshop as W
        pack = Pack(b["language"])
        rows = W.read_attested(pack)
        if b.get("add"):
            row = {k: "" for k in W.ATTESTED}
            row.update({k: str(v) for k, v in b["add"].items() if k in W.ATTESTED})
            row["status"], row["kind"] = "attested", row["kind"] or "word"
            row["branch"] = row["branch"] or pack.meta["derivation"]["standard"]
            if row["cite"]:
                src = self._src(b["language"])
                try:
                    why = W.check_word(src, row)
                    p = src.passage(row["cite"].split()[0])
                    if p:
                        row["tier"], row["source"] = row["tier"] or p["tier"], p["title"]
                finally:
                    src.close()
                if why:
                    return self._error(why)
            W.merge_attested(rows, [row])
        else:
            for r in rows:
                if r["form"] == b["form"] and r["kind"] == b.get("kind", r["kind"]):
                    r.update({k: str(b[k]) for k in ("status", "gloss", "pos", "branch", "key", "notes") if k in b})
        W.write_attested(pack, rows)
        self._json({"rows": W.read_attested(pack)})

    def design(self, q):
        from utp.core import workshop as W
        pack = Pack(q["language"])
        self._json({**W.read_decisions(pack), "design": relpath(pack.home / "DESIGN.md")})

    def design_draft(self, b):
        from utp.core import workshop as W
        pack = Pack(b["language"])
        self._sse_start()
        try:
            done = W.draft(pack, M.Model(role="build"), ids=b.get("ids") or None, n=int(b.get("n") or 3),
                           log=lambda line: self._sse({"line": line}))
            self._sse({"done": True, "drafted": [q["id"] for q in done]})
        except Exception as e:
            self._sse({"error": f"{type(e).__name__}: {e}"})

    def design_decide(self, b):
        from utp.core import workshop as W
        q = W.decide(Pack(b["language"]), b["id"], b.get("choice", ""), b.get("reason", ""))
        self._json({"question": q})

    def design_ask(self, b):
        from utp.core import workshop as W
        self._json({"question": W.ask(Pack(b["language"]), b["question"], b.get("angles") or ("canon", "society"))})

    def sounds(self, q):
        from utp.core import workshop as W
        pack = Pack(q["language"])
        p = W.proposal_path(pack)
        self._json({"proposal": json.loads(p.read_text()) if p.exists() else None, "current": W.check_sounds(pack),
                    "buildable": pack.buildable, "approved_words": pack.buildable and W.has_approved_words(pack)})

    def sounds_propose(self, b):
        from utp.core import workshop as W
        self._json({"proposal": W.propose_sounds(Pack(b["language"]), M.Model(role="build"))})

    def sounds_accept(self, b):
        from utp.core import workshop as W
        pack = Pack(b["language"])
        self._sse_start()
        try:
            words, tests = W.accept_sounds(pack, only_fitting=b.get("only_fitting", True), fresh=b.get("fresh"))
            self._sse({"line": f"sound_laws.json updated: {tests} tests; {words} attested words joined meanings.csv"})
            errors = X.rebuild(Pack(b["language"]), log=lambda line: self._sse({"line": line}))
            for e in errors[:20]:
                self._sse({"line": "error: " + " ".join(map(str, e))[:300]})
            self._sse({"done": True, "errors": len(errors)})
        except Exception as e:
            self._sse({"error": f"{type(e).__name__}: {e}"})

    def about(self, q):
        from utp.app.launch import electron
        self._json({"repo": str(REPO), "python": sys.executable, "python_version": sys.version.split()[0],
                    "desktop_installed": bool(electron()), "mode": os.environ.get("UTP_MODE", "browser"),
                    "port": self.server.server_port})

    def shortcut(self, b):
        from utp.app.launch import install_shortcuts
        self._json({"made": install_shortcuts()})

    def check_path(self, b):
        p = pathlib.Path(b.get("path", "")).expanduser()
        self._json({"path": str(p), "exists": p.exists(), "dir": p.is_dir(),
                    "writable": os.access(p if p.exists() else p.parent, os.W_OK),
                    "languages": sorted(x.parent.name for x in p.glob("*/pack.json")) if p.is_dir() else []})

    def chat(self, b):
        messages = [m for m in b.get("messages", []) if m.get("role") in ("user", "assistant") and m.get("content")]
        system = system_prompt(b.get("language"), b.get("mode", "assistant"), messages, b.get("files"))
        model = M.Model(connection=b.get("connection") or None, role="chat")
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
        path, rows = X.propose_batch(pack, b["topic"], M.Model(role="build"), n=int(b.get("n", 30)), extra=b.get("extra", ""))
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
        ok, bad = X.propose_sentences(pack, b["topic"], M.Model(role="build"), n=int(b.get("n", 8)))
        self._json({"ok": ok, "bad": bad})

    def sentences_add(self, b):
        pack = Pack(b["language"])
        path, added = X.add_sentences(pack, b["sentences"])
        if pack.buildable:
            learn.build_course(pack)
        self._json({"added": added, "path": relpath(path)})

    def topics(self, b):
        pack = Pack(b["language"])
        self._json({"topics": X.suggest_topics(pack, M.Model(role="build") if b.get("ai") else None)})

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
