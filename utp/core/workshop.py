"""The workshop: the steps of utp/METHOD.md that come before growing words.

  audit()          every word the sources already use, with the passage it appears in. The code checks each
                   one: the passage must exist and the word must really be in it.          -> audit/attested.csv
  draft()          the next design questions, each with options argued from several angles and cited.
  decide()         your answer: filed in design/decisions.json, written into DESIGN.md (which every prompt
                   reads), and added to the library as an author source, so it outranks everything.
  propose_sounds() a proto-language and sound laws that produce the attested words; the engine runs them and
                   reports which attested words come out right.                       -> design/sounds-proposal.json
  accept_sounds()  the proposal becomes sound_laws.json; attested words join meanings.csv with their fixed
                   proto-form and attested spelling, so every build checks them (E6).

Each step works without sources (from scratch) and gets better with them.
"""
import csv
import datetime
import json
import pathlib
import re

from .expand import design_notes, slug
from .library import CITE, Sources, format_passages
from .llm import section
from .phonotactics import Phonotactics
from .sca import SoundLaws

ROOT = pathlib.Path(__file__).resolve().parents[1]
METHOD = ROOT / "METHOD.md"
ATTESTED = ["form", "gloss", "pos", "key", "kind", "branch", "tier", "source", "cite", "evidence", "confidence", "status",
            "proto", "notes"]
KINDS = {"word", "phrase", "name", "place", "title"}


def method_rules():
    m = re.search(r"^## For models\n(.*?)(?=^## |\Z)", METHOD.read_text(), re.S | re.M)
    return m.group(1).strip() if m else ""


def question_bank():
    """The design questions from METHOD.md: [{id, question, angles}]."""
    text = METHOD.read_text()
    block = re.search(r"^## The design questions\n(.*?)(?=^## |\Z)", text, re.S | re.M).group(1)
    out = []
    for line in block.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("Id", "") and not set(cells[0]) <= set("-"):
            out.append({"id": cells[0], "question": cells[1], "angles": [a.strip() for a in cells[2].split(",")]})
    return out


def _system(extra=""):
    return f"{method_rules()}\n\n{extra}".strip()


def _norm(s):
    return (s or "").replace("’", "'").replace("‘", "'").replace("ʼ", "'").lower()


def _branches(pack):
    d = pack.meta.get("derivation", {})
    return d.get("branches", []), d.get("standard")


# ---------- attested words ----------
def attested_path(pack):
    return pack.home / "audit" / "attested.csv"


def read_attested(pack):
    p = attested_path(pack)
    if not p.exists():
        return []
    with open(p, newline="") as f:
        return [{k: (r.get(k) or "") for k in ATTESTED} for r in csv.DictReader(f)]


def write_attested(pack, rows):
    p = attested_path(pack)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["status"] == "rejected", r["kind"] != "word", _norm(r["form"])))
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ATTESTED, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


def audit_prompt(pack, group):
    lang = pack.meta.get("language", pack.name)
    branches, std = _branches(pack)
    msg = (f"Language: {lang}. Branches: {', '.join(branches)} (standard: {std}).\n\n"
           f"Find every word, phrase, name, place name or title IN {lang.upper()} (not English, and not another "
           f"language) that these passages use. For each, give the form exactly as spelled in the passage, what it "
           f"means if the passage says or clearly implies it, the passage id it appears in, and a short quote "
           f"(under 25 words) from that passage as evidence. If a passage says a word belongs to a particular "
           f"branch or people, give the branch. Skip passages with nothing in {lang}.\n\n"
           f"Passages:\n\n{format_passages(group, limit=1400)}\n\n"
           'Answer in JSON: {"words": [{"form": "...", "gloss": "... or empty", "kind": "word|phrase|name|place|title", '
           f'"branch": "{std}", "cite": "S1.2", "evidence": "...", "confidence": "high|medium|low", "notes": "..."}}]}}')
    return [{"role": "system", "content": _system("You are auditing sources for a constructed language.")},
            {"role": "user", "content": msg}]


def check_word(src, row):
    """Why an attested row fails its sources ('' when it holds): every cite exists and contains the form."""
    cites = CITE.findall(row.get("cite", ""))
    if not cites:
        return "no source cited"
    found = False
    for lib, d, n in cites:
        p = src.passage(f"{lib}{d}.{n}")
        if not p:
            return f"cites {lib}{d}.{n}, which is not in the library"
        if _norm(row["form"]) in _norm(p["text"]):
            found = True
    return "" if found else f"'{row['form']}' does not appear in {', '.join(f'{a}{b}.{c}' for a, b, c in cites)}"


def merge_attested(rows, new):
    by = {(_norm(r["form"]), r["kind"]): r for r in rows}
    added = 0
    for r in new:
        k = (_norm(r["form"]), r["kind"])
        if k in by:
            old = by[k]
            cites = list(dict.fromkeys(old["cite"].split() + r["cite"].split()))
            old["cite"] = " ".join(cites)
            for f in ("gloss", "pos", "evidence", "branch", "notes"):
                old[f] = old[f] or r[f]
        else:
            by[k] = r
            rows.append(r)
            added += 1
    return added


def audit(pack, model, query=None, tiers=("canon", "licensed", "fan"), max_passages=240, per_call=8, log=print):
    """Ask the model for the attested words, passage by passage; keep only what the passages bear out.
    Returns (added, rejected rows)."""
    src = Sources(pack.home)
    try:
        branches, std = _branches(pack)
        if query:
            group_from = src.search(query, k=max_passages, tiers=list(tiers))
        else:
            group_from = list(src.passages(list(tiers)))[:max_passages]
        if not group_from:
            log("No sources to audit: add some with utp.py sources add, or start from scratch with utp.py design.")
            return 0, []
        rows, rejected, added = read_attested(pack), [], 0
        for i in range(0, len(group_from), per_call):
            group = group_from[i:i + per_call]
            ids = {g["id"]: g for g in group}
            ans = model.chat_json(audit_prompt(pack, group))
            new = []
            for w in (ans.get("words", []) if isinstance(ans, dict) else []):
                if not isinstance(w, dict) or not str(w.get("form", "")).strip():
                    continue
                cite = str(w.get("cite", "")).strip()
                p = ids.get(cite)
                r = {k: "" for k in ATTESTED}
                r.update({"form": str(w["form"]).strip(), "gloss": str(w.get("gloss") or "").strip(),
                          "pos": str(w.get("pos") or "").strip().lower(),
                          "kind": w.get("kind") if w.get("kind") in KINDS else "word",
                          "branch": w.get("branch") if w.get("branch") in branches else std,
                          "tier": p["tier"] if p else "", "source": p["title"] if p else "", "cite": cite,
                          "evidence": str(w.get("evidence") or "")[:240], "confidence": str(w.get("confidence") or ""),
                          "status": "attested", "notes": str(w.get("notes") or "")})
                why = check_word(src, r) if p else f"cites {cite or 'nothing'}, which was not one of the passages given"
                if why:
                    rejected.append({**r, "why": why})
                else:
                    new.append(r)
            added += merge_attested(rows, new)
            log(f"passages {i + 1}-{i + len(group)} of {len(group_from)}: {len(new)} found, {added} new so far")
        write_attested(pack, rows)
        return added, rejected
    finally:
        src.close()


def check_attested(pack):
    """[(form, problem)] for every attested row its sources no longer bear out."""
    src = Sources(pack.home)
    try:
        return [(r["form"], why) for r in read_attested(pack) if r["status"] == "attested" and r["cite"]
                for why in [check_word(src, r)] if why]
    finally:
        src.close()


# ---------- design decisions ----------
def decisions_path(pack):
    return pack.home / "design" / "decisions.json"


def read_decisions(pack):
    p = decisions_path(pack)
    state = json.loads(p.read_text()) if p.exists() else {"questions": []}
    have = {q["id"] for q in state["questions"]}
    for b in question_bank():                 # every bank question is listed, drafted or not
        if b["id"] not in have:
            state["questions"].append({**b, "status": "open", "options": []})
    order = {b["id"]: i for i, b in enumerate(question_bank())}
    state["questions"].sort(key=lambda q: order.get(q["id"], 999))
    return state


def write_decisions(pack, state):
    p = decisions_path(pack)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n")
    return p


def ask(pack, question, angles=("canon", "society")):
    """Add a question of your own to the design list."""
    state = read_decisions(pack)
    n = 1 + sum(q["id"].startswith("own-") for q in state["questions"])
    q = {"id": f"own-{n}", "question": question, "angles": list(angles), "status": "open", "options": []}
    state["questions"].append(q)
    write_decisions(pack, state)
    return q


def draft_prompt(pack, q, hits, attested):
    lang = pack.meta.get("language", pack.name)
    words = "\n".join(f"- {r['form']}: {r['gloss'] or '(meaning unknown)'} [{r['kind']}, {r['tier']}]"
                      for r in attested[:120]) or "(none: this language starts from scratch)"
    msg = (f"Language: {lang}.\n\nDesign so far (DESIGN.md):\n{design_notes(pack, limit=8000) or '(nothing yet)'}\n\n"
           f"Attested words:\n{words}\n\n"
           f"Library passages for this question:\n\n{format_passages(hits) if hits else '(none: argue from the angles and mark each option as invention)'}\n\n"
           f"Design question: {q['question']}\nAngles that bear on it: {', '.join(q.get('angles', []))}\n\n"
           "Offer 2 to 4 real options (distinct choices someone could make, not one choice reworded). For each, "
           "argue for it from the angles, name the angles, cite passage ids where they support it, and say what it "
           "would cost. Then recommend one. If the sources already settle the question, say so and offer the "
           "settled answer as option A.\n\n"
           'Answer in JSON: {"options": [{"label": "short name", "argument": "...", "angles": ["canon", "body"], '
           '"cites": ["S1.2"], "cost": "..."}], "recommended": "A", "settled": false, "notes": "..."}')
    return [{"role": "system", "content": _system("You are helping design a constructed language.")},
            {"role": "user", "content": msg}]


def draft(pack, model, ids=None, n=3, log=print):
    """Options for the next open questions (or the ones named). Returns the questions drafted."""
    state = read_decisions(pack)
    src = Sources(pack.home)
    try:
        attested = [r for r in read_attested(pack) if r["status"] == "attested"]
        todo = [q for q in state["questions"] if (q["id"] in ids if ids else q["status"] == "open" and not q["options"])]
        todo = todo if ids else todo[:n]
        lang = pack.meta.get("language", pack.name)
        for q in todo:
            hits = src.search(f"{lang} {q['question']}", k=8)
            ans = model.chat_json(draft_prompt(pack, q, hits, attested))
            opts = []
            for i, o in enumerate((ans.get("options", []) if isinstance(ans, dict) else [])[:4]):
                if not isinstance(o, dict) or not o.get("label"):
                    continue
                cites = [str(c) for c in o.get("cites", []) if isinstance(c, (str, int))]
                good = [c for c in cites if src.passage(c)]
                opts.append({"id": "ABCD"[len(opts)], "label": str(o["label"]), "argument": str(o.get("argument", "")),
                             "angles": [str(a) for a in o.get("angles", [])], "cites": good,
                             "cost": str(o.get("cost", "")),
                             "invention": not good,
                             **({"dropped_cites": [c for c in cites if c not in good]} if len(good) < len(cites) else {})})
            if len(opts) < 2:
                log(f"{q['id']}: the model gave fewer than two usable options; try again or answer it yourself")
                continue
            rec = str(ans.get("recommended", "A")).strip()[:1].upper()
            q.update({"options": opts, "recommended": rec if rec in [o["id"] for o in opts] else "A",
                      "settled": bool(ans.get("settled")), "notes": str(ans.get("notes", "")),
                      "drafted": datetime.date.today().isoformat()})
            log(f"{q['id']}: {len(opts)} options drafted ({sum(len(o['cites']) for o in opts)} citations)")
        write_decisions(pack, state)
        return todo
    finally:
        src.close()


def decide(pack, qid, choice, reason=""):
    """Choose an option by its letter, or write your own answer. Files it in DESIGN.md and the library."""
    state = read_decisions(pack)
    q = next((q for q in state["questions"] if q["id"] == qid), None)
    if not q:
        raise KeyError(f"no design question '{qid}'")
    opt = next((o for o in q.get("options", []) if o["id"] == str(choice).strip().upper()), None)
    if choice in ("skip", "skipped"):
        q.update({"status": "skipped", "chosen": None, "decided": datetime.date.today().isoformat()})
    else:
        q.update({"status": "decided", "chosen": opt["id"] if opt else None,
                  "answer": opt["label"] if opt else str(choice), "reason": reason,
                  "decided": datetime.date.today().isoformat()})
    src = Sources(pack.home, include_shared=False)
    try:
        if q.get("library_doc"):
            try:
                src.own.remove(q["library_doc"])
            except KeyError:
                pass
            q.pop("library_doc")
        if q["status"] == "decided":
            body = (f"Design decision ({q['id']}): {q['question']}\nDecided: {q['answer']}."
                    + (f"\n{opt['argument']}" if opt and opt.get("argument") else "")
                    + (f"\nReason: {reason}" if reason else ""))
            doc, _ = src.own.add_text(body, f"Decision: {q['question']}", "author", "decision")
            q["library_doc"] = doc
    finally:
        src.close()
    write_decisions(pack, state)
    render_design(pack, state)
    return q


MARK = "<!-- decisions: written by utp.py design; edit them there, not here -->"


def render_design(pack, state=None):
    """DESIGN.md: your own text stays; the decisions section below the marker is rewritten."""
    state = state or read_decisions(pack)
    p = pack.home / "DESIGN.md"
    text = p.read_text() if p.exists() else f"# {pack.meta.get('language', pack.name)}: design notes\n"
    head = text.split(MARK)[0].rstrip() + "\n\n"
    done = [q for q in state["questions"] if q["status"] == "decided"]
    lines = [MARK, "", "## Decisions", ""]
    if not done:
        lines.append("None yet: `utp.py design` drafts the questions.")
    for q in done:
        opt = next((o for o in q.get("options", []) if o["id"] == q.get("chosen")), None)
        lines.append(f"### {q['question']}")
        lines.append("")
        lines.append(f"**{q['answer']}.**" + (f" {opt['argument']}" if opt and opt.get("argument") else ""))
        if q.get("reason"):
            lines.append(f"\nWhy: {q['reason']}")
        if opt and opt.get("cites"):
            lines.append(f"\nSources: {', '.join(opt['cites'])}")
        others = [o for o in q.get("options", []) if o["id"] != q.get("chosen")]
        if others:
            lines.append("\nConsidered and set aside: " + "; ".join(o["label"] for o in others) + ".")
        lines.append(f"\n<sub>{q['id']}, decided {q.get('decided', '')}</sub>\n")
    p.write_text(head + "\n".join(lines).rstrip() + "\n")
    return p


# ---------- sound laws from the attested words ----------
def proposal_path(pack):
    return pack.home / "design" / "sounds-proposal.json"


def segments_ok(form, units):
    """True if a proto-form is made only of the proto-language's sound units (spaces and hyphens allowed)."""
    if not units:
        return True
    rx = "(?:" + "|".join(re.escape(u) for u in sorted(units, key=len, reverse=True)) + ")+"
    return all(re.fullmatch(rx, w) for w in re.split(r"[ \-]+", form.lstrip("*")) if w)


def legal(proto, laws_data, policy=None):
    """'' if every word of a proto-form is a legal root of the proto-language, else why not."""
    units = laws_data.get("proto", {}).get("units", [])
    if not segments_ok(proto, units):
        return "proto-form uses sounds outside the proto-language"
    try:
        ph = Phonotactics(laws_data["proto"], policy)
    except (KeyError, TypeError):
        return ""
    for w in re.split(r"[ \-]+", proto.lstrip("*")):
        if w:
            ok, why = ph.check(w)
            if not ok:
                return f"*{w}: {why}"
    return ""


def fit(laws_data, words, policy=None):
    """Run the laws on each attested word's proto-form: [{form, branch, proto, got, ok, why}]."""
    out = []
    try:
        laws = SoundLaws(laws_data)
        for b in laws.branches:
            laws.chain(b)                          # compile every rule now, so a bad pattern is caught here
    except (re.error, KeyError, TypeError) as e:
        return [{"form": w["form"], "branch": w.get("branch", ""), "proto": w.get("proto", ""), "got": "",
                 "ok": False, "why": f"the laws do not run: {e}"} for w in words]
    units = laws_data.get("proto", {}).get("units", [])
    for w in words:
        proto, branch = (w.get("proto") or "").strip(), w.get("branch")
        r = {"form": w["form"], "branch": branch, "proto": proto, "got": "", "ok": False, "why": ""}
        if not proto:
            r["why"] = "no proto-form"
        elif branch not in laws.branches:
            r["why"] = f"no branch '{branch}'"
        elif legal(proto, laws_data, policy):
            r["why"] = legal(proto, laws_data, policy)
        else:
            r["got"] = laws.apply(proto, branch)
            r["ok"] = _norm(r["got"]) == _norm(w["form"])
            r["why"] = "" if r["ok"] else f"the laws give '{r['got']}'"
        out.append(r)
    return out


def sounds_prompt(pack, laws, words, decisions):
    lang = pack.meta.get("language", pack.name)
    branches, std = _branches(pack)
    wl = "\n".join(f"- {w['form']} ({w['branch']}): {w['gloss'] or w['kind']}" for w in words)
    dec = "\n".join(f"- {q['question']} {q['answer']}" for q in decisions) or "(none yet)"
    msg = (f"Language: {lang}. Branches: {', '.join(branches)} (standard: {std}; a branch may inherit another's laws).\n\n"
           f"Design decisions:\n{dec}\n\nAttested words the laws must produce, exactly as spelled:\n{wl or '(none)'}\n\n"
           f"Current sound laws:\n{json.dumps(laws, ensure_ascii=False)[:6000]}\n\n"
           "Reconstruct the proto-language: its sound units (letters or digraphs), vowels, allowed onset clusters and "
           "final sounds, and a proto-form for every attested word. Then write each branch's sound laws as ordered "
           "regex rewrites (Python regex; use $1 for groups) that turn each proto-form into the attested spelling in "
           "its branch. Prefer few, general, phonetically natural laws to one law per word; it is better to leave a "
           "word unexplained (and say why) than to write a law only that word uses. Keep any current law that still "
           "works.\n\n"
           'Answer in JSON: {"proto": {"units": [...], "vowels": [...], "onset_clusters": [...], "finals": [...], '
           '"about": "..."}, "branches": {"<branch>": {"rules": [{"id": "V1", "pattern": "...", "replace": "...", '
           '"note": "what changed and why"}]}}, "words": [{"form": "...", "branch": "...", "proto": "*...", '
           '"why": "..."}], "notes": "..."}')
    return [{"role": "system", "content": _system("You are reconstructing a proto-language and its sound changes.")},
            {"role": "user", "content": msg}]


def _laws_file(pack):
    return pack.dir / pack.meta.get("files", {}).get("sound_laws", "sound_laws.json")


def propose_sounds(pack, model):
    """Ask for proto-forms and laws, run them, and save the proposal with its fit. Returns the proposal."""
    current = json.loads(_laws_file(pack).read_text())
    rows = [r for r in read_attested(pack) if r["status"] == "attested" and r["kind"] != "phrase"]
    decisions = [q for q in read_decisions(pack)["questions"] if q["status"] == "decided"]
    ans = model.chat_json(sounds_prompt(pack, current, rows, decisions))
    ans = ans if isinstance(ans, dict) else {}
    laws = json.loads(json.dumps(current))
    if isinstance(ans.get("proto"), dict):
        laws["proto"] = {**laws.get("proto", {}), **{k: v for k, v in ans["proto"].items() if v}}
    for b, spec in (ans.get("branches") or {}).items():
        if b in laws["branches"] and isinstance(spec, dict) and isinstance(spec.get("rules"), list):
            laws["branches"][b]["rules"] = [{"id": str(r.get("id", f"{b[:1].upper()}{i + 1}")),
                                            "pattern": str(r.get("pattern", "")), "replace": str(r.get("replace", "")),
                                            "note": str(r.get("note", ""))}
                                           for i, r in enumerate(spec["rules"]) if isinstance(r, dict) and r.get("pattern")]
    given = {(_norm(w.get("form")), w.get("branch")): w for w in ans.get("words", []) if isinstance(w, dict)}
    words = []
    for r in rows:
        w = given.get((_norm(r["form"]), r["branch"])) or next((g for (f, _), g in given.items() if f == _norm(r["form"])), {})
        proto = str(w.get("proto") or r["proto"] or "").strip()
        words.append({"form": r["form"], "branch": r["branch"], "gloss": r["gloss"], "kind": r["kind"],
                      "proto": proto if proto.startswith("*") or not proto else "*" + proto, "why": str(w.get("why", ""))})
    result = fit(laws, words, pack.meta.get("phonotactics"))
    prop = {"date": datetime.date.today().isoformat(), "laws": laws, "words": words, "fit": result,
            "fits": sum(r["ok"] for r in result), "total": len(result), "notes": str(ans.get("notes", ""))}
    p = proposal_path(pack)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(prop, indent=1, ensure_ascii=False) + "\n")
    return prop


def check_sounds(pack):
    """The current sound laws against every attested word that has a proto-form."""
    laws = json.loads(_laws_file(pack).read_text())
    rows = [r for r in read_attested(pack) if r["status"] == "attested" and r["proto"]]
    return fit(laws, rows, pack.meta.get("phonotactics"))


def has_approved_words(pack):
    """True once any batch has been applied: from then on a rebuild should not reshuffle generated roots."""
    from .expand import batches_dir, read_batch
    return any(r.get("status") == "applied" for p in batches_dir(pack).glob("*.csv") for r in read_batch(p))


def accept_sounds(pack, only_fitting=True, fresh=None):
    """The saved proposal becomes the language's sound laws; attested words get their proto-forms and join
    meanings.csv (words) or the laws' tests (names, places, titles). fresh=True gives every generated root a new
    form from the new sound system (the default until any batch has been approved); otherwise only the roots the
    new proto-language cannot say are remade. Returns (words added, tests)."""
    if not pack.buildable:
        raise RuntimeError(f"{pack.id} keeps its own sound laws; change them with its own tools")
    prop = json.loads(proposal_path(pack).read_text())
    laws, ok = prop["laws"], {(_norm(r["form"]), r["branch"]) for r in prop["fit"] if r["ok"]}
    words = [w for w in prop["words"] if w["proto"] and (not only_fitting or (_norm(w["form"]), w["branch"]) in ok)]
    laws["tests"] = [{"proto": w["proto"], w["branch"]: w["form"], "gloss": w.get("gloss") or w.get("kind", "")} for w in words]
    _laws_file(pack).write_text(json.dumps(laws, indent=2, ensure_ascii=False) + "\n")
    rows = read_attested(pack)
    by = {(_norm(w["form"]), w["branch"]): w for w in words}
    for r in rows:
        w = by.get((_norm(r["form"]), r["branch"]))
        if w:
            r["proto"] = w["proto"]
    have = {r["gloss"].lower().strip(): r["key"] for r in pack.rows() if r.get("gloss")}
    entries = []
    for r in rows:
        if (_norm(r["form"]), r["branch"]) in by and r["kind"] == "word" and r["gloss"]:
            r["key"] = r["key"] or have.get(r["gloss"].lower().strip()) or slug(r["gloss"])
            entries.append({"key": r["key"], "gloss": r["gloss"], "pos": r["pos"] or "noun", "field": "attested", "era": "",
                            "kind": "root", "proto": r["proto"].lstrip("*"), f"attested_{r['branch']}": r["form"],
                            "notes": f"Attested: {r['source']} {r['cite']}".strip()})
    write_attested(pack, rows)
    add_meanings(pack, entries)
    regenerate_roots(pack, laws, everything=(not has_approved_words(pack)) if fresh is None else fresh)
    return len(entries), len(laws["tests"])


def regenerate_roots(pack, laws, everything=False):
    """Generated roots the new proto-language cannot say (or all of them) are forgotten, so the next build makes
    new ones. Roots you fixed (attested, or given a proto-form by hand) are never touched. Returns how many."""
    lex = pack.dir / pack.meta["build"].get("out", "build") / "lexicon.csv"
    if not lex.exists():
        return 0
    with open(lex, newline="") as f:
        rd = csv.DictReader(f)
        fields, rows = rd.fieldnames, list(rd)
    n, policy = 0, pack.meta.get("phonotactics")
    for r in rows:
        if r.get("status") == "generated" and r.get("proto") and (everything or legal(r["proto"], laws, policy)):
            r["proto"], r["status"] = "", ""
            n += 1
    with open(lex, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return n


def add_meanings(pack, entries):
    """Add or update rows in meanings.csv, widening its columns when a row needs a new one."""
    path = pack.dir / pack.meta["build"].get("meanings", "meanings.csv")
    rows, fields = [], ["key", "gloss", "pos", "field", "era", "kind", "parts", "notes"]
    if path.exists() and path.read_text().strip():
        with open(path, newline="") as f:
            rd = csv.DictReader(f)
            fields = list(rd.fieldnames)
            rows = list(rd)
    by = {r["key"]: r for r in rows}
    for e in entries:
        for k in e:
            if k not in fields:
                fields.append(k)
        if e["key"] in by:
            by[e["key"]].update({k: v for k, v in e.items() if v and k not in ("pos", "field") or not by[e["key"]].get(k)})
        else:
            rows.append(e)
            by[e["key"]] = e
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path
