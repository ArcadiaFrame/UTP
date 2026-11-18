"""Vulcan dictionary builder: generator + checker.

  python3 tools/lexicon.py build   fill missing roots from lexicon/meanings.csv,
                                   derive every branch, check, write lexicon.csv
  python3 tools/lexicon.py check   re-derive and check lexicon/lexicon.csv only

Every candidate root is generated from the Proto-Vulcan sound system in
tools/rules.json and kept only if it passes every check against the words
already accepted. Nothing is ever chosen at random twice: each meaning seeds
its own generator, so a rebuild gives the same dictionary.

Checks (errors stop a word; warnings are reported):
  E1 spelling outside the Proto-Vulcan sound system or root shape
  E2 same Proto form used twice
  E3 same Standard Vulcan spelling for two meanings
  E4 two Standard Vulcan words that sound the same
  E5 same meaning, part of speech and register already covered
  E6 an attested form the sound laws fail to produce
  E7 a generated word that takes an unglossed canon word (reserved)
  E8-E10 spelling shape (tripled letters, doubled apostrophes); E9 unresolved compound
  E11 a built word dated earlier than one of its parts
  E12 an affix joined the wrong way: word-building endings fuse (+), bound words take a hyphen (-)
  W1 Standard or Romulan form is a common English word
  W2 same Romulan spelling for two meanings
  W3 an affix on a word class the morphology spec does not list for it (review, not an error)
"""
import csv, hashlib, json, pathlib, random, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from sca import apply, RULES  # noqa: E402
from phon import ipa, standardize  # noqa: E402

LEX = ROOT / "lexicon"
P = RULES["proto"]
UNITS = sorted(P["units"], key=len, reverse=True)
VOW = set(P["vowels"])
ENGLISH = set((LEX / "english_block.txt").read_text().split()) | {
    "of", "to", "in", "it", "is", "be", "as", "at", "so", "we", "he", "by", "or", "on", "do", "if", "me", "my",
    "up", "an", "go", "no", "us", "am", "oh", "ok", "ma", "pa", "hi", "ha", "ah", "eh", "uh", "id", "ox", "ax"}
def _reserved():
    """Standard spellings of canon and novel words that are not glossed yet.
    The generator may never take one: a later reading might give it a meaning."""
    from phon import standardize, words as _words
    out = set()
    for name in ("canon.csv", "novel.csv"):
        with open(ROOT / "corpus" / name, newline="") as f:
            for r in csv.DictReader(f):
                if r.get("type") in ("name", "place"):
                    continue
                for w in re.split(r"[\s.,?!]+", standardize(r["form"]).lower()):
                    for piece in [w] + w.split("-"):
                        if piece:
                            out.add(piece)
    return out


RESERVED = _reserved()
FIELDS_OUT = ["id", "key", "proto", "vulcan", "ceremonial", "romulan", "ipa", "gloss", "pos", "field", "kind",
              "era", "register", "parts", "attested_vulcan", "attested_ceremonial", "attested_romulan",
              "source", "status", "exception", "notes"]


# ---------- Proto-Vulcan structure ----------
def units(form):
    out, i = [], 0
    while i < len(form):
        for u in UNITS:
            if form.startswith(u, i):
                out.append(u)
                i += len(u)
                break
        else:
            return None
    return out


def shape_ok(form):
    """E1: every piece is a Proto-Vulcan sound and the root has a legal shape."""
    us = units(form)
    if not us:
        return False, "contains a sound outside Proto-Vulcan"
    if us[0] == "'":
        return False, "cannot start with a glottal stop"
    cons_run, onset, seen_v = [], [], False
    for u in us:
        if u in VOW:
            if not seen_v and len(onset) > 1 and "".join(onset) not in P["onset_clusters"]:
                return False, f"onset {''.join(onset)}- not allowed"
            if seen_v and len([c for c in cons_run if c != "'"]) > 2:
                return False, "more than two consonants together"
            seen_v, cons_run = True, []
        else:
            (cons_run if seen_v else onset).append(u)
    if not seen_v:
        return False, "no vowel"
    final = [c for c in cons_run if c != "'"]
    if len(final) > 1:
        return False, "word ends in a consonant cluster"
    if final and final[0] not in P["finals"]:
        return False, f"cannot end in {final[0]}"
    return True, ""


# ---------- generator ----------
ONSET_W = {"t": 48, "k": 44, "s": 29, "p": 18, "v": 16, "f": 15, "n": 14, "m": 10, "sh": 9, "h": 7, "w": 6,
           "l": 8, "r": 5, "y": 2, "kh": 6, "th": 3, "lh": 3, "zh": 2, "ch": 3, "q": 5, "kʼ": 4, "tʼ": 4, "pʼ": 2,
           "nt": 4, "mp": 3, "nk": 3, "kl": 4, "kr": 3, "pl": 3, "tr": 3, "st": 4, "sm": 2, "sr": 2, "vr": 3,
           "sp": 2, "sk": 2, "khr": 1, "shl": 1}
MED_W = {"k": 20, "t": 14, "l": 14, "r": 16, "n": 14, "s": 10, "sh": 8, "kh": 6, "v": 8, "f": 6, "m": 8, "h": 4,
         "th": 3, "lh": 3, "zh": 3, "q": 3, "kʼ": 3, "tʼ": 3, "'": 6, "w": 3, "y": 3}
VOW_W = {"a": 30, "i": 18, "e": 16, "o": 14, "u": 12, "uh": 4, "ai": 3, "au": 3, "ei": 2, "ee": 2, "oo": 2}
FIN_W = {"k": 30, "l": 14, "n": 14, "r": 14, "t": 10, "sh": 7, "kh": 6, "s": 6, "f": 3, "v": 4, "m": 3,
         "lh": 2, "kʼ": 2, "q": 2, "th": 2, "zh": 1}
HARSH = {"kʼ", "tʼ", "pʼ", "q", "kh", "sh", "zh", "khr", "kr", "tr", "k", "t"}
SOFT = {"l", "n", "m", "y", "h", "w", "lh", "sh", "v", "s"}
FIELD_TONE = {"conflict": "harsh", "death": "harsh", "fire": "harsh", "desert": "harsh", "animal": "harsh",
              "mind": "soft", "bond": "soft", "kin": "soft", "discipline": "soft", "life": "soft",
              "emotion": "soft", "sky": "soft", "nature": "soft", "plant": "soft"}
SHAPES = {
    "noun": [("CVC", 30), ("CVCVC", 26), ("CVCV", 14), ("CCVC", 10), ("CVCCVC", 10), ("CVCCV", 5), ("VCVC", 5)],
    "verb": [("CVC", 34), ("CVCV", 18), ("CVCVC", 22), ("CCVC", 10), ("VCVC", 6), ("CVCCV", 10)],
    "adjective": [("CVC", 24), ("CVCVC", 26), ("CVCV", 16), ("CVCCVC", 12), ("CCVC", 10), ("VCVC", 12)],
    "short": [("CV", 40), ("VC", 25), ("CVC", 35)],
}


def pick(rng, table, tone, allow=None):
    items = [(k, w) for k, w in table.items() if allow is None or k in allow]
    adj = []
    for k, w in items:
        if tone == "harsh":
            w = w * (2.5 if k in HARSH else 0.6 if k in SOFT else 1)
        elif tone == "soft":
            w = w * (2.0 if k in SOFT else 0.3 if k in {"kʼ", "tʼ", "pʼ", "q"} else 1)
        adj.append((k, w))
    r = rng.random() * sum(w for _, w in adj)
    for k, w in adj:
        r -= w
        if r <= 0:
            return k
    return adj[-1][0]


def candidate(rng, pos, field):
    tone = FIELD_TONE.get(field)
    key = pos if pos in SHAPES else ("short" if pos in {"pronoun", "particle", "conjunction", "interjection",
                                                         "determiner", "adverb", "auxiliary", "number", "suffix", "prefix"} else "noun")
    shape = pick(rng, dict(SHAPES[key]), None)
    out, i = [], 0
    while i < len(shape):
        if shape[i] == "V":
            out.append(pick(rng, VOW_W, tone))
            i += 1
        elif shape.startswith("CC", i) and i == 0:
            out.append(pick(rng, ONSET_W, tone, {k for k in ONSET_W if k in P["onset_clusters"]}))
            i += 2
        elif i == 0:
            out.append(pick(rng, ONSET_W, tone, {k for k in ONSET_W if k not in P["onset_clusters"]}))
            i += 1
        elif i == len(shape) - 1:
            out.append(pick(rng, FIN_W, tone))
            i += 1
        else:
            out.append(pick(rng, MED_W, tone))
            i += 1
    return "".join(out)


# ---------- derivation ----------
KEY_PROTO = {}
LOANS = {}      # key -> form; a loanword enters compounds as it is, without sound laws
EXCEPT = {}     # key -> attested Standard form of a logged exception (sehlat, kaiidth), kept inside compounds too


def derive(row, by_proto):
    if row.get("era") == "Romulan" and row.get("attested_romulan") and row["kind"] != "compound":
        # coined or attested in Romulan after the Sundering: spelled as attested, no sound laws
        return {"vulcan": "", "ceremonial": "", "romulan": row["attested_romulan"]}
    if row["kind"] == "loan":
        return {"vulcan": row["attested_vulcan"], "ceremonial": "", "romulan": ""}
    if row["kind"] == "compound":
        res = {}
        for b in ("vulcan", "ceremonial", "romulan"):
            def sub(m):
                part = m.group(0)
                if part.startswith("{"):
                    if part.strip("{}") in LOANS:
                        return LOANS[part.strip("{}")]
                    if b == "vulcan" and part.strip("{}") in EXCEPT:
                        return EXCEPT[part.strip("{}")]
                    part = KEY_PROTO.get(part.strip("{}"), "?" + part)
                if part not in by_proto:
                    return "?" + part
                out = apply(part, b)
                return standardize(out) if b == "vulcan" else out   # each piece in standard spelling
            joined = re.sub(r"\{[^}]+\}|[^\s+\-]+", sub, row["parts"])
            if b == "vulcan":   # a screen spelling's final length-h drops before a fused ending (sarlah + uth > sarlauth)
                joined = re.sub(r"(?<!u)([aeio])h\+(?=[aeiouh])", r"\1+", joined)   # uh is a vowel, not a length mark
            joined = re.sub(r"(?<=[aeo])([iu])\+\1", r"\1+", joined)   # a diphthong absorbs a like vowel: kau+uth > kauth, sharshei+ik > sharsheik
            res[b] = joined.replace("+", "")
        return res
    return {b: apply(row["proto"], b) for b in ("vulcan", "ceremonial", "romulan")}


def norm_gloss(g):
    return re.split(r"[,;(]", g.lower())[0].strip()


FUSE = {"action", "abstract", "participle-ik", "adjectival", "place-suf", "instrument", "collective", "ordinal",
        "adverbial", "indef", "univ", "toward", "causative"}      # docs/morphology.md: endings that fuse
BOUND = {"ve", "kam", "tor", "kau", "endear", "pejorative"}      # bound words: always after a hyphen
BASES = {"action": {"verb"}, "abstract": {"adjective", "noun", "verb", "auxiliary", "adverb", "pronoun"},
         "participle-ik": {"verb", "noun"}, "adverbial": {"adjective", "noun", "particle"}, "ordinal": {"number"},
         "kam": {"noun", "name"}}


def check(rows):
    """Return (errors, warnings) as lists of (id, code, message)."""
    errs, warns = [], []
    era_of = {r["key"]: r["era"] for r in rows}
    RANK = {"Tribal": 0, "Classical": 1, "Unified": 2, "Standard": 3, "Romulan": 3}
    for r in rows:
        if r["kind"] == "compound":
            for k in re.findall(r"\{([^}]+)\}", r["parts"]):
                if k in era_of and RANK.get(era_of[k], 0) > RANK.get(r["era"], 0):
                    errs.append((r["id"], "E11", f"dated {r['era']} but its part '{k}' is {era_of[k]}"))
    pos_of = {r["key"]: r["pos"] for r in rows}
    for r in rows:
        if r["kind"] != "compound" or r["era"] == "Romulan":
            continue
        toks = re.findall(r"([+\-\s]?)\{([^}]+)\}", r["parts"])
        for i, (sep, k) in enumerate(toks[1:], 1):
            if k in FUSE and sep == "-":
                errs.append((r["id"], "E12", f"ending '{k}' must fuse (+), not take a hyphen"))
            if k in BOUND and sep == "+":
                errs.append((r["id"], "E12", f"bound word '{k}' takes a hyphen (-), not fusion"))
            if k in BASES and len(toks) == 2 and pos_of.get(toks[0][1]) not in BASES[k]:
                warns.append((r["id"], "W3", f"'{k}' on a {pos_of.get(toks[0][1])} ({toks[0][1]}): check the morphology spec"))
    seen = {"proto": {}, "vulcan": {}, "ipa": {}, "romulan": {}, "meaning": {}}
    for r in rows:
        rid = r["id"]
        if r["kind"] not in ("compound", "loan"):
            ok, why = shape_ok(r["proto"]) if r["kind"] != "anchor" or r["pos"] != "particle" else (True, "")
            if not ok and r["status"] not in ("reconstructed", "aligned", "designed"):
                errs.append((rid, "E1", f"*{r['proto']}: {why}"))
            if r["proto"] in seen["proto"]:
                errs.append((rid, "E2", f"*{r['proto']} already used by {seen['proto'][r['proto']]}"))
            seen["proto"].setdefault(r["proto"], rid)
        if r["kind"] == "compound" and any("?" in r[b] for b in ("vulcan", "ceremonial", "romulan")):
            errs.append((rid, "E9", f"compound parts '{r['parts']}' name a key with no root form"))
        v = r["vulcan"]
        if v and ("''" in v or re.search(r"([a-z])\1\1", v)):
            errs.append((rid, "E10", f"Standard '{v}' has a doubled apostrophe or a letter three times in a row"))
        if v:
            if v in seen["vulcan"]:
                errs.append((rid, "E3", f"Standard '{v}' already means '{seen['vulcan'][v][1]}' ({seen['vulcan'][v][0]})"))
            else:
                seen["vulcan"][v] = (rid, r["gloss"])
                sound = r["ipa"].replace(" ", "")
                if sound and sound in seen["ipa"]:   # an empty reading (a name) matches nothing
                    errs.append((rid, "E4", f"'{v}' sounds the same as '{seen['ipa'][sound]}'"))
                if sound:
                    seen["ipa"].setdefault(sound, v)
        m = (norm_gloss(r["gloss"]), r["pos"], r["register"], r["era"] == "Romulan")
        if m in seen["meaning"]:
            errs.append((rid, "E5", f"meaning '{m[0]}' ({m[1]}, {m[2]}) already covered by {seen['meaning'][m]}"))
        seen["meaning"].setdefault(m, rid)
        if r["exception"]:
            warns.append((rid, "X", f"accepted exception: {r['exception']}"))
        for b in ("vulcan", "ceremonial", "romulan"):
            want = r[f"attested_{b}"]
            if want and r[b] != want:
                if r["exception"]:
                    warns.append((rid, "X", f"accepted exception: {b} '{r[b]}' vs attested '{want}': {r['exception']}"))
                else:
                    errs.append((rid, "E6", f"{b} law gives '{r[b]}', canon has '{want}'"))
        if r["status"] == "generated":
            for b in ("vulcan", "romulan"):
                if r[b] in ENGLISH:
                    warns.append((rid, "W1", f"{b} '{r[b]}' is an English word"))
            if r["vulcan"] in RESERVED:
                errs.append((rid, "E7", f"'{r['vulcan']}' is an unglossed canon word, reserved"))
        rom = r["romulan"]
        if rom and re.search(r"([a-z])\1\1", rom):
            errs.append((rid, "E8", f"Romulan '{rom}' has a letter three times in a row"))
        if rom:
            if rom in seen["romulan"] and seen["romulan"][rom] != rid:
                warns.append((rid, "W2", f"Romulan '{rom}' also used by {seen['romulan'][rom]}"))
            seen["romulan"].setdefault(rom, rid)
    return errs, warns


def std_keep(form):
    """Standard spelling, keeping the word's own spaces and hyphens."""
    return " ".join("-".join(standardize(p) if p else p for p in w.split("-")) for w in form.split(" "))


def fill(row, by_proto):
    d = derive(row, by_proto)
    if row.get("era") == "Romulan":     # coined after the Sundering: no Vulcan or Ceremonial reflex
        d["vulcan"] = d["ceremonial"] = ""
    elif row["kind"] not in ("compound", "loan") and not row.get("exception") and d["vulcan"]:
        d["vulcan"] = std_keep(d["vulcan"])   # one spelling system: oy > oi, vowel+h > vowel, ck > k ...
    if row.get("exception"):
        # a logged exception means the attested form is the dictionary form; the law output is kept in the notes
        for b in ("vulcan", "ceremonial", "romulan"):
            want = row.get(f"attested_{b}")
            if want and d.get(b) and d[b] != want:
                law = f"Sound law alone gives {b} '{d[b]}'."
                if law not in row.get("notes", ""):
                    row["notes"] = (row["notes"] + " " if row.get("notes") else "") + law
                d[b] = want
    row.update(d)
    row["ipa"] = ipa(row["vulcan"]) if row["vulcan"] else ""
    return row


def read_existing():
    path = LEX / "lexicon.csv"
    if not path.exists():
        return {}
    with open(path, newline="") as f:
        # a row without a proper id or key is a damaged line, never a word: skip it
        return {r["key"]: r for r in csv.DictReader(f) if r.get("id", "")[1:].isdigit() and r.get("key")}


KIND_ORDER = {"anchor": 0, "aligned": 0, "design": 1, "loan": 1, "core": 2, "compound": 3}
KIND_STATUS = {"anchor": "reconstructed", "aligned": "aligned", "design": "designed", "loan": "loan", "compound": "compound", "core": "generated"}


def build():
    """Accepted words are frozen: a rebuild keeps every existing word's form and id,
    takes descriptive fields from meanings.csv, and generates only new meanings.
    An explicit proto in meanings.csv (a canon anchor) always wins."""
    with open(LEX / "meanings.csv", newline="") as f:
        wants = list(csv.DictReader(f))
    existing = read_existing()
    next_id = max([int(r["id"][1:]) for r in existing.values()] + [0]) + 1
    accepted, by_proto, gen_log, changes = [], set(), [], []
    order = sorted(wants, key=lambda w: (KIND_ORDER[w["kind"]], w["key"] not in existing))
    for w in order:
        old = existing.get(w["key"])
        row = {k: w.get(k, "") for k in FIELDS_OUT}
        row["status"] = KIND_STATUS[w["kind"]]
        if old:
            row["id"] = old["id"]
            if w["kind"] == "core" and not w["proto"]:
                row["proto"] = old["proto"]
            elif w["proto"] and old["proto"] and w["proto"] != old["proto"]:
                changes.append(f"{w['key']}: *{old['proto']} replaced by *{w['proto']} ({w['notes'] or w['source']})")
        else:
            row["id"] = f"V{next_id:04d}"
            next_id += 1
        if w["kind"] == "core" and not row["proto"]:
            seed = int(hashlib.sha256(w["key"].encode()).hexdigest()[:12], 16)
            rng = random.Random(seed)
            for attempt in range(1, 2001):
                row["proto"] = candidate(rng, w["pos"], w["field"])
                fill(row, by_proto)
                ok, _ = shape_ok(row["proto"])
                e, wn = check(accepted + [row])
                e = [x for x in e if x[0] == row["id"]]
                wn = [x for x in wn if x[0] == row["id"] and x[1] in ("W1", "W2")]
                if ok and not e and not wn:
                    gen_log.append((row["id"], w["key"], attempt))
                    break
            else:
                row["notes"] = "generator found no clean form"
        else:
            fill(row, by_proto)
        if row["proto"]:
            by_proto.add(row["proto"])
            KEY_PROTO[row["key"]] = row["proto"]
        if row["kind"] == "loan" and row["vulcan"]:
            LOANS[row["key"]] = row["vulcan"]
        if row.get("exception") and row.get("attested_vulcan"):
            EXCEPT[row["key"]] = row["attested_vulcan"]
        accepted.append(row)
    for row in accepted:
        if row["status"] == "compound":
            fill(row, by_proto)
    retired = [f"{k}: *{r['proto'] or r['parts']} {r['vulcan']} '{r['gloss']}'" for k, r in existing.items()
               if k not in {w['key'] for w in wants}]
    accepted.sort(key=lambda r: r["id"])
    write(accepted)
    return accepted, gen_log, changes, retired


def write(rows):
    with open(LEX / "lexicon.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_OUT)
        w.writeheader()
        w.writerows(rows)


def report(rows, gen_log=None):
    errs, warns = check(rows)
    lines = ["# Dictionary check", "", f"{len(rows)} entries. {len(errs)} errors, {len(warns)} warnings or accepted exceptions.", ""]
    if not sys.argv[1:2] == ["check"] and RULES.get("tests"):
        from sca import run_tests
        lines.append(f"Sound-law test cases: {'all pass' if run_tests(False) else 'FAILURES'}.")
        lines.append("")
    for title, items in (("Errors", errs), ("Warnings and exceptions", warns)):
        lines.append(f"## {title}")
        lines += [f"- {i} {c}: {m}" for i, c, m in items] or ["- none"]
        lines.append("")
    if gen_log:
        tries = [a for _, _, a in gen_log]
        lines.append(f"Generator: {len(gen_log)} roots, {sum(tries)} candidates tried, "
                     f"{sum(tries) - len(gen_log)} rejected by the checks.")
    (LEX / "check_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return errs


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "build":
        rows, log, changes, retired = build()
        for title, items in (("Replaced by canon", changes), ("Retired", retired)):
            if items:
                print(f"## {title}")
                print("\n".join("- " + i for i in items))
        sys.exit(1 if report(rows, log) else 0)
    with open(LEX / "lexicon.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    by_proto = {r["proto"] for r in rows if r["proto"]}
    KEY_PROTO.update({r["key"]: r["proto"] for r in rows if r["proto"]})   # compounds resolve {key} through this
    LOANS.update({r["key"]: r["vulcan"] for r in rows if r["kind"] == "loan" and r["vulcan"]})
    EXCEPT.update({r["key"]: r["attested_vulcan"] for r in rows if r.get("exception") and r.get("attested_vulcan")})
    rows = [fill(r, by_proto) for r in rows]
    sys.exit(1 if report(rows) else 0)
