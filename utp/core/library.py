"""A language's sources library: the material a language is built from, searchable, citable, kept private.

  <language>/sources/library.sqlite   the library (SQLite, full-text search; not in git)
  <language>/sources/files/           copies of the files you added (not in git)
  <language>/sources/public/          files published with the language (in git); indexed automatically
  ~/.utp/library.sqlite               a shared library every language searches too (real-world science,
                                      general references), when you add with shared=True

Every source has a tier (see utp/METHOD.md): author, canon, licensed, fan, science. Text is split into
passages; each passage has an id a prompt can cite and the code can check: S<doc>.<n> in the language's
library, G<doc>.<n> in the shared one.

Search is SQLite full-text search (BM25). If Settings names an embedding model, passages also get vectors and
search blends both rankings, so "cold" finds "ice" too. Everything works offline.
"""
import datetime
import hashlib
import html.parser
import json
import math
import pathlib
import re
import shutil
import sqlite3
import struct
import zipfile

TIERS = {
    "author": {"label": "Your decisions and notes", "rank": 5},
    "canon": {"label": "Canon (on screen, scripts, official reference)", "rank": 4},
    "licensed": {"label": "Licensed (novels, games, sourcebooks)", "rank": 3},
    "fan": {"label": "Fan work (fan dictionaries, wikis, conlangs)", "rank": 2},
    "science": {"label": "Real-world science (linguistics, anthropology, biology)", "rank": 1},
}
TEXT_TYPES = {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".srt", ".vtt", ".html", ".htm", ".xhtml",
              ".pdf", ".docx", ".epub", ".rst", ".org", ".tex", ".yaml", ".yml"}
CHUNK = 1100
CITE = re.compile(r"\b([SG])(\d+)\.(\d+)\b")

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, title TEXT, tier TEXT, kind TEXT, file TEXT, url TEXT,
  note TEXT, added TEXT, chars INTEGER, sha TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS passages (doc INTEGER, n INTEGER, text TEXT, PRIMARY KEY (doc, n));
CREATE VIRTUAL TABLE IF NOT EXISTS passages_fts USING fts5(text, title, doc UNINDEXED, n UNINDEXED,
  tokenize = "unicode61 remove_diacritics 2 tokenchars ''''");
CREATE TABLE IF NOT EXISTS vectors (doc INTEGER, n INTEGER, model TEXT, vec BLOB, PRIMARY KEY (doc, n, model));
"""


# ---------- reading files ----------
class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "dd", "dt",
             "blockquote", "pre", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n\n" if tag in ("p", "div", "section", "article", "h1", "h2", "h3", "tr") else "\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_text(markup):
    p = _Text()
    p.feed(markup)
    return re.sub(r"[ \t]+", " ", "".join(p.out))


def _xml_text(xml):
    xml = re.sub(r"</w:p>", "\n\n", xml)
    return html_text(xml)


def read_text(path):
    """Plain text from a file. PDFs need pypdf (pip install pypdf) or the pdftotext program."""
    path = pathlib.Path(path)
    ext = path.suffix.lower()
    if ext in (".html", ".htm", ".xhtml"):
        return html_text(path.read_text(errors="replace"))
    if ext in (".srt", ".vtt"):
        lines = [l for l in path.read_text(errors="replace").splitlines()
                 if l.strip() and not re.match(r"^\d+$|^[\d:,.]+ --> |^WEBVTT", l.strip())]
        return "\n".join(re.sub(r"<[^>]+>", "", l) for l in lines)
    if ext == ".docx":
        with zipfile.ZipFile(path) as z:
            return _xml_text(z.read("word/document.xml").decode("utf8", "replace"))
    if ext == ".epub":
        with zipfile.ZipFile(path) as z:
            names = sorted(n for n in z.namelist() if n.endswith((".xhtml", ".html", ".htm")))
            return "\n\n".join(html_text(z.read(n).decode("utf8", "replace")) for n in names)
    if ext == ".pdf":
        try:
            import pypdf
            return "\n\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(path)).pages)
        except ImportError:
            import subprocess
            try:
                return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                                      check=True).stdout
            except (OSError, subprocess.CalledProcessError):
                raise ValueError("reading PDFs needs pypdf (pip install pypdf) or the pdftotext program") from None
    return path.read_text(errors="replace")


def split(text, size=CHUNK):
    """Passages of about `size` characters, on paragraph and then sentence boundaries."""
    text = re.sub(r"\r\n?", "\n", text)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, cur = [], ""
    for p in paras:
        pieces = [p] if len(p) <= size else re.split(r"(?<=[.!?])\s+", p)
        for piece in pieces:
            while len(piece) > size * 1.5:                 # a wall of text with no sentence ends
                out.append(piece[:size])
                piece = piece[size:]
            if cur and len(cur) + len(piece) + 1 > size:
                out.append(cur)
                cur = piece
            else:
                cur = f"{cur}\n{piece}" if cur else piece
    if cur:
        out.append(cur)
    return out


# ---------- vectors ----------
def _pack(v):
    return struct.pack(f"{len(v)}f", *v)


def _unpack(b):
    return struct.unpack(f"{len(b) // 4}f", b)


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1
    nb = math.sqrt(sum(y * y for y in b)) or 1
    return dot / (na * nb)


def fts_query(q):
    """Free text to an FTS5 query: every word, any of them, prefix-matched."""
    words = [re.sub(r"'s$", "", w).strip("'") for w in re.findall(r"[\w']+", q.lower())]
    words = [w for w in dict.fromkeys(words) if len(w) > 1]
    return " OR ".join(f'"{w}"*' for w in words[:24])


class Library:
    def __init__(self, path, prefix="S", files=None):
        self.path = pathlib.Path(path)
        self.prefix = prefix
        self.files = pathlib.Path(files) if files else self.path.parent / "files"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    def cite(self, doc, n):
        return f"{self.prefix}{doc}.{n}"

    # ---------- adding ----------
    def add_text(self, text, title, tier="canon", kind="paste", file="", url="", note=""):
        """Index text as one source. Returns (doc id, passages) or (existing id, 0) if the same text is there."""
        if tier not in TIERS:
            raise ValueError(f"tier: one of {', '.join(TIERS)}")
        text = text.strip()
        if not text:
            raise ValueError("no text in this source")
        sha = hashlib.sha256(text.encode()).hexdigest()
        old = self.db.execute("SELECT id FROM docs WHERE sha = ?", (sha,)).fetchone()
        if old:
            return old["id"], 0
        cur = self.db.execute("INSERT INTO docs (title, tier, kind, file, url, note, added, chars, sha) "
                              "VALUES (?,?,?,?,?,?,?,?,?)",
                              (title, tier, kind, file, url, note, datetime.date.today().isoformat(), len(text), sha))
        doc = cur.lastrowid
        parts = split(text)
        for n, p in enumerate(parts, 1):
            self.db.execute("INSERT INTO passages VALUES (?,?,?)", (doc, n, p))
            self.db.execute("INSERT INTO passages_fts (text, title, doc, n) VALUES (?,?,?,?)", (p, title, doc, n))
        self.db.commit()
        return doc, len(parts)

    def add_file(self, path, tier="canon", title=None, url="", note="", copy=True):
        path = pathlib.Path(path)
        if path.suffix.lower() not in TEXT_TYPES:
            raise ValueError(f"{path.name}: not a file type the library reads ({', '.join(sorted(TEXT_TYPES))})")
        text = read_text(path)
        kept = ""
        if copy:
            self.files.mkdir(parents=True, exist_ok=True)
            dest = self.files / path.name
            i = 2
            while dest.exists() and dest.read_bytes() != path.read_bytes():
                dest = self.files / f"{path.stem}-{i}{path.suffix}"
                i += 1
            if not dest.exists():
                shutil.copy2(path, dest)
            kept = dest.name
        return self.add_text(text, title or path.stem.replace("_", " ").replace("-", " "), tier, "file", kept, url, note)

    def remove(self, doc):
        row = self.db.execute("SELECT file FROM docs WHERE id = ?", (doc,)).fetchone()
        if not row:
            raise KeyError(f"no source {doc}")
        for t in ("passages", "vectors"):
            self.db.execute(f"DELETE FROM {t} WHERE doc = ?", (doc,))
        self.db.execute("DELETE FROM passages_fts WHERE doc = ?", (doc,))
        self.db.execute("DELETE FROM docs WHERE id = ?", (doc,))
        self.db.commit()
        if row["file"] and (self.files / row["file"]).exists() and not self.db.execute(
                "SELECT 1 FROM docs WHERE file = ?", (row["file"],)).fetchone():
            (self.files / row["file"]).unlink()

    # ---------- reading ----------
    def docs(self):
        rows = self.db.execute("SELECT d.*, (SELECT COUNT(*) FROM passages p WHERE p.doc = d.id) AS passages "
                               "FROM docs d ORDER BY id").fetchall()
        return [{**dict(r), "cite": f"{self.prefix}{r['id']}", "library": self.prefix} for r in rows]

    def passage(self, doc, n):
        r = self.db.execute("SELECT p.text, d.title, d.tier, d.url FROM passages p JOIN docs d ON d.id = p.doc "
                            "WHERE p.doc = ? AND p.n = ?", (doc, n)).fetchone()
        return {"id": self.cite(doc, n), "text": r["text"], "title": r["title"], "tier": r["tier"], "url": r["url"]} if r else None

    def passages(self, tiers=None):
        q = "SELECT p.doc, p.n, p.text, d.title, d.tier FROM passages p JOIN docs d ON d.id = p.doc"
        args = []
        if tiers:
            q += f" WHERE d.tier IN ({','.join('?' * len(tiers))})"
            args = list(tiers)
        for r in self.db.execute(q + " ORDER BY p.doc, p.n", args):
            yield {"id": self.cite(r["doc"], r["n"]), "text": r["text"], "title": r["title"], "tier": r["tier"]}

    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM passages").fetchone()[0]

    def search(self, query, k=8, tiers=None, model=None, embed_model=None):
        """The best passages for a query: [{id, text, title, tier, score}]."""
        fq = fts_query(query)
        ranked = {}
        if fq:
            sql = ("SELECT f.doc, f.n, bm25(passages_fts) AS s FROM passages_fts f JOIN docs d ON d.id = f.doc "
                   "WHERE passages_fts MATCH ?")
            args = [fq]
            if tiers:
                sql += f" AND d.tier IN ({','.join('?' * len(tiers))})"
                args += list(tiers)
            for i, r in enumerate(self.db.execute(sql + " ORDER BY s LIMIT ?", args + [k * 4])):
                ranked[(r["doc"], r["n"])] = 1 / (60 + i)
        if model and embed_model and self.db.execute("SELECT 1 FROM vectors WHERE model = ? LIMIT 1", (embed_model,)).fetchone():
            qv = model.embed([query], embed_model)[0]
            sql = "SELECT v.doc, v.n, v.vec FROM vectors v JOIN docs d ON d.id = v.doc WHERE v.model = ?"
            args = [embed_model]
            if tiers:
                sql += f" AND d.tier IN ({','.join('?' * len(tiers))})"
                args += list(tiers)
            sims = sorted(((_cos(qv, _unpack(r["vec"])), r["doc"], r["n"]) for r in self.db.execute(sql, args)), reverse=True)
            for i, (_, d, n) in enumerate(sims[: k * 4]):
                ranked[(d, n)] = ranked.get((d, n), 0) + 1 / (60 + i)
        out = []
        for (d, n), s in sorted(ranked.items(), key=lambda kv: -kv[1])[:k]:
            p = self.passage(d, n)
            out.append({**p, "score": round(s * 1000, 2)})
        return out

    def embed(self, model, embed_model, batch=32, log=print):
        """Vectors for every passage that has none for this embedding model."""
        todo = self.db.execute("SELECT p.doc, p.n, p.text FROM passages p WHERE NOT EXISTS (SELECT 1 FROM vectors v "
                               "WHERE v.doc = p.doc AND v.n = p.n AND v.model = ?)", (embed_model,)).fetchall()
        for i in range(0, len(todo), batch):
            part = todo[i:i + batch]
            vecs = model.embed([r["text"] for r in part], embed_model)
            for r, v in zip(part, vecs):
                self.db.execute("INSERT OR REPLACE INTO vectors VALUES (?,?,?,?)", (r["doc"], r["n"], embed_model, _pack(v)))
            self.db.commit()
            log(f"embedded {min(i + batch, len(todo))}/{len(todo)}")
        return len(todo)


# ---------- a language's libraries ----------
def shared():
    from . import config as C
    return Library(C.home() / "library.sqlite", "G", C.home() / "library-files")


class Sources:
    """A language's own library plus the shared one, searched and cited together."""

    def __init__(self, home, include_shared=True):
        self.home = pathlib.Path(home)
        self.dir = self.home / "sources"
        self.own = Library(self.dir / "library.sqlite", "S")
        self.libs = {"S": self.own}
        if include_shared:
            self.libs["G"] = shared()
        self.sync_public()

    def close(self):
        for lib in self.libs.values():
            lib.close()

    def sync_public(self):
        """Index files in sources/public/ (published with the language) that the library has not seen."""
        pub = self.dir / "public"
        if not pub.is_dir():
            return 0
        added = 0
        known = {r["file"] for r in self.own.docs() if r["kind"] == "public"}
        for f in sorted(pub.iterdir()):
            if f.suffix.lower() in TEXT_TYPES and f.name not in known:
                tier = "author"
                m = re.match(r"^(author|canon|licensed|fan|science)[-_ ]", f.name)
                if m:
                    tier = m.group(1)
                try:
                    text = read_text(f)
                    head = re.match(r"#\s+(.+)", text.lstrip())
                    title = (re.sub(r"\s*\((author|canon|licensed|fan|science)\)\s*$", "", head.group(1)).strip() if head else
                             re.sub(r"^(author|canon|licensed|fan|science)[-_ ]", "", f.stem).replace("-", " ").replace("_", " "))
                    doc, n = self.own.add_text(text, title, tier, "public", f.name)
                    added += bool(n)
                except ValueError:
                    pass
        return added

    def lib(self, shared_lib=False):
        return self.libs["G" if shared_lib else "S"]

    def docs(self):
        return [d for lib in self.libs.values() for d in lib.docs()]

    def search(self, query, k=8, tiers=None):
        model, embed_model = embedder()
        hits = []
        for lib in self.libs.values():
            try:
                hits += lib.search(query, k, tiers, model, embed_model)
            except Exception:
                hits += lib.search(query, k, tiers)
        rank = {t: v["rank"] for t, v in TIERS.items()}
        for h in hits:                       # a small lift by authority: of two equally good passages, cite the stronger
            h["score"] = round(h["score"] + 0.15 * rank.get(h["tier"], 0), 2)
        hits.sort(key=lambda h: (-h["score"], -rank.get(h["tier"], 0)))
        return hits[:k]

    def passage(self, cite):
        m = CITE.fullmatch(cite.strip())
        if not m or m.group(1) not in self.libs:
            return None
        return self.libs[m.group(1)].passage(int(m.group(2)), int(m.group(3)))

    def passages(self, tiers=None):
        for lib in self.libs.values():
            yield from lib.passages(tiers)

    def count(self):
        return sum(lib.count() for lib in self.libs.values())

    def check_cites(self, text):
        """(cited ids that exist, cited ids that do not)."""
        ok, bad = [], []
        for m in CITE.finditer(text or ""):
            (ok if self.passage(m.group(0)) else bad).append(m.group(0))
        return ok, bad


def embedder():
    """(Model, embedding model name) from Settings, or (None, None) when meaning-based search is off."""
    from . import config as C
    lib = C.load().get("library", {})
    if not lib.get("embed_model"):
        return None, None
    from .models import Model
    try:
        return Model(connection=lib.get("embed_connection") or None, role="build", timeout=60), lib["embed_model"]
    except Exception:
        return None, None


def format_passages(hits, limit=900):
    """Passages as a prompt shows them: id, tier, title, text."""
    return "\n\n".join(f"[{h['id']}] ({h['tier']}: {h['title']})\n{h['text'][:limit]}" for h in hits)
