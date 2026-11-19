"""Grow a language with a model, the way the Vulcan batches were grown by hand.

  propose_batch()      a model proposes new meanings on a topic: transparent compounds of older words
                       first, a new root only when nothing sensible can be built. Every proposal is
                       checked (no duplicate meaning, every part exists and is no newer than the word,
                       a known era and part of speech) and written to <language>/batches/*.csv.
  apply_batch()        the rows you marked approve = yes join the language, and everything is rebuilt:
                       dictionary, check report, docs, Lab and course. For Vulcan, approved words go
                       into vulcan-conlang/lexicon and its own pipeline runs (pack.json "expand").
  propose_sentences()  a model writes course sentences as meaning frames (dictionary keys only);
                       the language's own grammar renders them, the parser reads them back, and only
                       sentences that survive the round trip enter course/sentences.json.
  suggest_topics()     what to grow next: thin fields from the dictionary, or a model's suggestions.

Nothing a model writes reaches the dictionary until you approve it.
"""
import csv
import datetime
import json
import pathlib
import re
import subprocess
import sys

from . import interlingua as I
from .llm import grammar_card, lookup, section
from .pack import Pack

POS = {"noun", "verb", "adjective", "adverb", "particle", "pronoun", "number", "interjection", "phrase",
       "suffix", "prefix", "auxiliary", "conjunction", "determiner"}
FIELDS = ["key", "gloss", "pos", "field", "era", "register", "kind", "parts", "basis", "sources", "status", "why",
          "approve"]
TOKEN = re.compile(r"\{([^}]+)\}")
PARTS_OK = re.compile(r"^(\{[^}]+\}[ +\-]?)+$")


def slug(text):
    return re.sub(r"[^a-z0-9']+", "-", text.lower()).strip("-")[:48]


def _eras(pack):
    return [e for e in pack.meta.get("eras", [])]


def _rank(pack):
    return {e["id"]: e["rank"] for e in _eras(pack)}


def batches_dir(pack):
    rel = pack.meta.get("expand", {}).get("batches")
    d = (pack.home / rel) if rel else pack.home / "batches"
    d.mkdir(parents=True, exist_ok=True)
    return d


def design_notes(pack, limit=8000):
    for name in ("DESIGN.md", "README.md"):
        p = pack.home / name
        if p.exists():
            return p.read_text()[:limit]
    return ""


def _building_blocks(pack, rows, topic, limit=500):
    """The keys a model may build with: grammatical pieces, the oldest roots, and words near the topic."""
    std, rank = pack.meta["derivation"]["standard"], _rank(pack)
    near = lookup(rows, topic, std, limit=120)
    gram = [r for r in rows if r.get("field") == "grammar" or r.get("pos") in ("suffix", "prefix")]
    old = sorted((r for r in rows if r.get("kind") in ("root", "core", "anchor") and r.get(std)
                  and r.get("field") != "grammar"), key=lambda r: (rank.get(r.get("era"), 9), r.get("id", "")))
    seen, out = set(), []
    for r in gram + near + old:
        if r["key"] not in seen and r.get(std):
            seen.add(r["key"])
            out.append(r)
        if len(out) >= limit:
            break
    return out


def library_context(pack, query, k=8):
    """Passages from the language's sources for a prompt, and the attested words not yet in the dictionary."""
    from .library import Sources, format_passages
    from .workshop import read_attested
    hits = []
    if (pack.home / "sources").exists():
        src = Sources(pack.home)
        try:
            hits = src.search(f"{pack.meta.get('language', pack.name)} {query}", k=k)
        finally:
            src.close()
    attested = [r for r in read_attested(pack) if r["status"] == "attested" and r["kind"] == "word" and r["gloss"]]
    text = ""
    if hits:
        text += ("Sources for this topic (cite their ids in \"sources\" when a word rests on one):\n\n"
                 + format_passages(hits, limit=700) + "\n\n")
    if attested:
        text += ("Attested words (fixed: never propose another word for these meanings, never respell them):\n"
                 + "\n".join(f"- {r['form']}: {r['gloss']}" for r in attested[:150]) + "\n\n")
    return text, hits


def batch_prompt(pack, rows, topic, n, extra=""):
    from .workshop import method_rules
    std = pack.meta["derivation"]["standard"]
    context, _ = library_context(pack, topic)
    blocks = _building_blocks(pack, rows, topic)
    eras = ", ".join(f"{e['id']} ({e['rank']})" for e in _eras(pack) if not e.get("branch"))
    have = [r for r in lookup(rows, topic, std, limit=80)]
    msg = (f"Language: {pack.meta.get('language', pack.name)}\nEras, oldest first (rank): {eras}\n\n"
           f"Design notes:\n{design_notes(pack) or '(none yet)'}\n\n{grammar_card(pack)}\n\n{context}"
           f"Topic for this batch: {topic}\nPropose up to {n} meanings the language needs for this topic and does "
           f"not have yet.\n{extra}\n\n"
           "Meanings the dictionary already has near this topic (do not repeat them):\n"
           + "\n".join(f"- {r['key']}: {r['gloss']}" for r in have)
           + "\n\nBuilding blocks (key = meaning [part of speech, era]):\n"
           + "\n".join(f"{r['key']} = {r['gloss']} [{r.get('pos', '')}, {r.get('era', '')}]" for r in blocks)
           + '\n\nAnswer in JSON: {"entries": [{"key": "new-key", "gloss": "...", "pos": "noun", "field": "...", '
             '"era": "...", "register": "everyday", "kind": "compound", "parts": "{a}-{b}", "basis": "...", '
             '"sources": ["S1.2"]}]}')
    system = section("Builder: expanding a language") + "\n\n" + method_rules()
    return [{"role": "system", "content": system}, {"role": "user", "content": msg}]


def validate(pack, rows, entries, topic, src=None):
    """Check every proposal against the dictionary, the sources and the batch so far; never drop one silently."""
    from .workshop import read_attested
    rank = _rank(pack)
    attested = {r["gloss"].lower().strip(): r["form"] for r in read_attested(pack)
                if r["status"] == "attested" and r["kind"] == "word" and r["gloss"]}
    eras = [e["id"] for e in _eras(pack) if not e.get("branch")]
    keys = {r["key"]: r for r in rows}
    glosses = {(r.get("gloss", "").lower().strip(), r.get("pos", "")): r["key"] for r in rows}
    batch, out = {}, []
    for e in entries:
        cites = e.get("sources") or []
        cites = cites.split() if isinstance(cites, str) else [str(c) for c in cites if isinstance(c, (str, int))]
        r = {k: str(e.get(k, "") or "").strip() for k in FIELDS if k != "sources"}
        r["key"] = slug(r["key"] or r["gloss"])
        r["kind"] = "root" if r["kind"] in ("root", "core") else "compound"
        r["register"] = r["register"] or "everyday"
        r["field"] = slug(r["field"]) or slug(topic)
        why = []
        if not r["key"] or not r["gloss"]:
            why.append("no key or meaning")
        if r["key"] in keys:
            why.append(f"key already in the dictionary ({keys[r['key']].get('gloss', '')})")
        twin = glosses.get((r["gloss"].lower(), r["pos"]))
        if twin:
            why.append(f"meaning already exists as {twin}")
        if r["key"] in batch:
            why.append("listed twice in this batch")
        if r["gloss"].lower() in attested:
            why.append(f"already attested as '{attested[r['gloss'].lower()]}' (audit/attested.csv)")
        bad = [c for c in cites if not (src and src.passage(c))]
        if bad:
            r["basis"] = (r["basis"] + f" (cited {', '.join(bad)}, not in the library: removed)").strip()
        r["sources"] = " ".join(c for c in cites if c not in bad)
        if r["pos"] not in POS:
            why.append(f"unknown part of speech '{r['pos']}'")
        if r["era"] not in rank:
            r["era"] = eras[-1] if eras else ""
        if r["kind"] == "compound":
            names = TOKEN.findall(r["parts"])
            if not names or not PARTS_OK.match(r["parts"].replace(" ", "")):
                why.append("parts must be {key} pieces joined by - or +")
            unknown = [k for k in names if k not in keys and k not in batch]
            if unknown:
                why.append("unknown part: " + ", ".join(unknown))
            if r["key"] in names:
                why.append("names itself")
            part_ranks = [rank.get((keys.get(k) or batch.get(k) or {}).get("era"), 0) for k in names if k in keys or k in batch]
            if part_ranks and rank.get(r["era"], 0) < max(part_ranks):
                newest = max(part_ranks)
                r["era"] = next(e for e in eras if rank[e] == newest) if newest in rank.values() else r["era"]
                r["basis"] = (r["basis"] + " (era raised to its newest part)").strip()
        else:
            r["parts"] = ""
        r["status"] = "rejected" if why else "proposed"
        r["why"] = "; ".join(why)
        r["approve"] = "no" if why else ""
        if not why:
            batch[r["key"]] = r
        out.append(r)
    return out


def write_batch(pack, topic, rows):
    d = batches_dir(pack)
    stem = f"{datetime.date.today().isoformat()}-{slug(topic) or 'batch'}"
    path, i = d / f"{stem}.csv", 2
    while path.exists():
        path, i = d / f"{stem}-{i}.csv", i + 1
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def propose_batch(pack, topic, model, n=30, extra=""):
    from .library import Sources
    rows = pack.rows()
    answer = model.chat_json(batch_prompt(pack, rows, topic, n, extra))
    entries = answer.get("entries", []) if isinstance(answer, dict) else []
    src = Sources(pack.home) if (pack.home / "sources").exists() else None
    try:
        checked = validate(pack, rows, entries[: n * 2], topic, src)
    finally:
        if src:
            src.close()
    return write_batch(pack, topic, checked), checked


def read_batch(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _approved(r):
    return r.get("approve", "").strip().lower() in ("y", "yes", "1", "true", "x") and r.get("status") != "applied"


def apply_batch(pack, path, log=print):
    """Add the approved rows to the language and rebuild everything. Returns (added, errors)."""
    path = pathlib.Path(path)
    batch = read_batch(path)
    yes = [r for r in batch if _approved(r)]
    if not yes:
        log("Nothing approved: mark approve = yes on the rows to add.")
        return 0, []
    today = datetime.date.today().isoformat()
    if pack.buildable:
        mpath = pack.dir / pack.meta["build"].get("meanings", "meanings.csv")
        fields = ["key", "gloss", "pos", "field", "era", "kind", "parts", "notes"]
        new = not mpath.exists() or not mpath.read_text().strip()
        with open(mpath, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new:
                w.writeheader()
            for r in yes:
                note = ("Built: " if r["kind"] == "compound" else "Root: ") + r.get("basis", "")
                w.writerow({**r, "kind": "compound" if r["kind"] == "compound" else "root",
                            "notes": f"{note} (batch {path.stem})"})
        errors = rebuild(pack, log)
    else:
        cfg = pack.meta.get("expand")
        if not cfg:
            raise RuntimeError(f"{pack.id} cannot be expanded: it has no build or expand section")
        cwd = (pack.root / cfg["cwd"]).resolve()
        comp = [r for r in yes if r["kind"] == "compound"]
        roots = [r for r in yes if r["kind"] != "compound"]
        if comp:
            dpath = cwd / cfg["compounds"]
            with open(dpath, newline="") as f:
                dfields = next(csv.reader(f))
            with open(dpath, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=dfields, extrasaction="ignore")
                for r in comp:
                    w.writerow({**r, "basis": f"{r.get('basis', '')} (batch {path.stem})".strip()})
        if roots:
            mpath = cwd / cfg["roots"]
            with open(mpath, newline="") as f:
                mfields = next(csv.reader(f))
            with open(mpath, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=mfields, extrasaction="ignore")
                for r in roots:
                    w.writerow({"key": r["key"], "gloss": r["gloss"], "pos": r["pos"], "field": r["field"], "kind": "core",
                                "register": r.get("register") or "everyday", "era": r["era"],
                                "notes": f"Proposed root (batch {path.stem}, {today}): {r.get('basis', '')}"})
        errors = rebuild(pack, log)
    for r in batch:
        if _approved(r):
            r["status"] = "applied"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(batch)
    return len(yes), errors


def rebuild(pack, log=print):
    """The whole language from its sources: dictionary, check, docs, Lab, course. Returns the build errors."""
    from . import learn
    errors = []
    if pack.buildable:
        from .builder import Builder
        rows, errors, warnings = Builder(pack).build()
        log(f"dictionary: {len(rows)} entries, {len(errors)} errors, {len(warnings)} warnings")
        pack = Pack(pack.dir)
        (pack.home / "docs").mkdir(exist_ok=True)
        (pack.home / "docs" / "grammar-card.md").write_text(grammar_card(pack))
    else:
        cfg = pack.meta["expand"]
        cwd = (pack.root / cfg["cwd"]).resolve()
        for step in cfg["rebuild"]:
            res = subprocess.run([sys.executable, *step], cwd=cwd, capture_output=True, text=True)
            tail = (res.stdout.strip().splitlines() or [""])[-1]
            log(f"{' '.join(step)}: {'ok' if res.returncode == 0 else 'FAILED'} {tail}")
            if res.returncode != 0:
                errors.append((" ".join(step), (res.stdout + res.stderr)[-2000:]))
                break
        pack = Pack(pack.dir)
    for p in learn.build_all(pack):
        log(f"wrote {p}")
    return errors


# ---------- sentences for the course ----------
def sentence_prompt(pack, rows, topic, n):
    std = pack.meta["derivation"]["standard"]
    g = I.Grammar(pack)
    usable = lookup(rows, topic, std, limit=150)
    fixed = sorted(set(g.c["pronouns"].values()) | set(g.c["possessives"].values()) | set(g.c["wh"].values()))
    keys = "\n".join(f"{r['key']} = {r['gloss']} [{r.get('pos', '')}]" for r in usable)
    doc = I.__doc__.split('"""')[0]
    msg = (f"Language: {pack.meta.get('language', pack.name)}. Topic: {topic}.\nWrite {n} short, useful sentences a "
           "learner needs for this topic, as meaning frames.\n\nFrame format:\n" + doc +
           f"\nPronoun, possessive and question words are given by code (pron: 1sg, 2sg, 3sg, 1pl, 3pl; "
           f"poss: 1sg; wh word: what, who, where, when, why, how, how-many). Grammar keys already handled: "
           f"{', '.join(fixed)}.\nUse only these dictionary keys for heads, verbs, adjectives and adverbs:\n{keys}\n\n"
           'Answer in JSON: {"sentences": [{"en": "English meaning", "frame": {...}}]}')
    return [{"role": "system", "content": section("Builder: writing course sentences")}, {"role": "user", "content": msg}]


def check_frame(pack, frame):
    """(template, text, why) for a frame: why is empty when it renders cleanly and survives a round trip."""
    try:
        t = I.render_template(pack, frame)
        text = I.realize(pack, t)
        if "?" in text.rstrip("?"):
            missing = re.findall(r"\?([\w'\-]+)", text)
            return t, text, "unknown keys: " + ", ".join(missing)
        back = I.render(pack, I.parse(pack, text))
        if back != text:
            return t, text, f"does not read back the same ({back})"
        return t, text, ""
    except Exception as e:
        return "", "", f"{type(e).__name__}: {e}"


def propose_sentences(pack, topic, model, n=10):
    rows = pack.rows()
    answer = model.chat_json(sentence_prompt(pack, rows, topic, n))
    ok, bad = [], []
    for s in (answer.get("sentences", []) if isinstance(answer, dict) else [])[: n * 2]:
        frame = s.get("frame") if isinstance(s, dict) else None
        if not isinstance(frame, dict):
            bad.append({"en": str(s), "why": "no frame"})
            continue
        t, text, why = check_frame(pack, frame)
        (bad if why else ok).append({"topic": topic, "en": s.get("en", ""), "frame": frame, "t": t, "v": text,
                                     **({"why": why} if why else {})})
    return ok, bad


def add_sentences(pack, sentences):
    path = pack.home / "course" / "sentences.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    have = json.loads(path.read_text()) if path.exists() else []
    seen = {s["v"] for s in have}
    new = [s for s in sentences if s["v"] not in seen]
    path.write_text(json.dumps(have + new, indent=1, ensure_ascii=False))
    return path, len(new)


# ---------- what to grow next ----------
def field_counts(pack):
    counts = {}
    for r in pack.rows():
        counts[r.get("field") or "other"] = counts.get(r.get("field") or "other", 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1]))


def suggest_topics(pack, model=None, n=8):
    counts = field_counts(pack)
    done = sorted(p.stem for p in batches_dir(pack).glob("*.csv"))
    if model is None:
        return [f"{f.replace('-', ' ')} ({c} words)" for f, c in list(counts.items())[:n]]
    msg = (f"Language: {pack.meta.get('language', pack.name)}\nDesign notes:\n{design_notes(pack)}\n\n"
           f"Words per field: {json.dumps(counts)}\nBatches already done: {', '.join(done) or 'none'}\n\n"
           f"Suggest the {n} most useful topics to add next, for this culture and for writers and learners. "
           'Answer in JSON: {"topics": ["...", ...]}')
    ans = model.chat_json([{"role": "user", "content": msg}])
    return [str(t) for t in (ans.get("topics", []) if isinstance(ans, dict) else [])][:n]
