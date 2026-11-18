"""Build the Vuhlkansu Course page from the course plan and the dictionary.

Inputs: corpus/course.json (units, items and stories as {key} templates),
        lexicon/lexicon.csv, tools/course.template.html
Output: course/vuhlkansu-course.html
Run from the project root: python3 tools/build_course.py   (fails if any {key} does not resolve)

Every Vulcan form is rendered from the dictionary at build time, so the course always
matches it. Item ids are a hash of the template, so a learner's progress survives
reordering units and rebuilding; only rewriting an item's template starts it fresh.
"""
import csv
import datetime
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from templates import render, form_map  # noqa: E402

# ---------- spelling units: one letter or letter pair is one sound ----------
PAIRS = [("kh", "x"), ("sh", "ʃ"), ("zh", "ʒ"), ("th", "θ"), ("ch", "tʃ"), ("uh", "ə"),
         ("aa", "aː"), ("ee", "iː"), ("oo", "uː"), ("ai", "ai"), ("au", "au"), ("ei", "ei"), ("oi", "oi")]
SINGLE = {"j": "dʒ", "'": "ʔ", "r": "ɾ", "y": "j"}
VOWEL_SOUNDS = {"a", "e", "i", "o", "u", "ə", "aː", "iː", "uː", "ai", "au", "ei", "oi", "ɨ"}
LONG = {"aː", "iː", "uː"}
DIPH = {"ai", "au", "ei", "oi"}


def units(word):
    """Split a spelling into (letters, sound) units."""
    w, out, i = word.lower(), [], 0
    while i < len(w):
        for src, snd in PAIRS:
            if w.startswith(src, i):
                out.append([word[i:i + 2], snd]); i += 2; break
        else:
            ch = w[i]
            # canon-style vowel + h at a word end ("eh") is just the vowel
            if ch == "h" and i == len(w) - 1 and out and out[-1][1] in VOWEL_SOUNDS:
                out[-1][0] += word[i]; i += 1; continue
            out.append([word[i], SINGLE.get(ch, ch)]); i += 1
    # y between consonants is the vowel /ɨ/
    for k, (letters, snd) in enumerate(out):
        if letters.lower() == "y":
            pv = k > 0 and out[k - 1][1] in VOWEL_SOUNDS
            nv = k + 1 < len(out) and out[k + 1][1] in VOWEL_SOUNDS
            if not pv and not nv:
                out[k][1] = "ɨ"
    return out


def syllables(member):
    """Syllables of one hyphen-free word: a list of lists of units."""
    us = units(member)
    vi = [k for k, u in enumerate(us) if u[1] in VOWEL_SOUNDS]
    if not vi:
        return [us]
    cuts = []
    for a, b in zip(vi, vi[1:]):
        cluster = list(range(a + 1, b))
        if not cluster:
            cuts.append(b)
        elif any(us[k][1] == "ʔ" for k in cluster):        # the catch closes the syllable before it
            g = max(k for k in cluster if us[k][1] == "ʔ")
            cuts.append(g + 1)
        else:
            cuts.append(b - 1)                               # the last consonant opens the next syllable
    sy, start = [], 0
    for c in cuts:
        sy.append(us[start:c]); start = c
    sy.append(us[start:])
    return sy


def say(word):
    """Reading aid for one written word: syllables (spelling kept), stress, IPA, sound features."""
    members = [m for m in word.split("-") if m]
    parts, ipa, feats = [], [], set()
    for mi, m in enumerate(members):
        sy = syllables(m)
        for si, s in enumerate(sy):
            stressed = mi == 0 and si == 0 and len(members) + len(sy) > 2   # monosyllables carry no mark
            parts.append({"s": "".join(u[0] for u in s), "st": stressed, "join": "-" if (si == 0 and mi > 0) else ("·" if parts else "")})
            snd = ""
            for k, u in enumerate(s):
                prev = s[k - 1][1] if k else None
                snd += "ː" if (u[1] == prev and u[1] not in VOWEL_SOUNDS) else u[1]
            ipa.append(("ˈ" if stressed else "") + snd)
        for u in units(m):
            l, s = u[0].lower(), u[1]
            if s in ("x", "ʃ", "ʒ", "θ", "tʃ", "dʒ", "ʔ", "ɾ", "ə", "ɨ"):
                feats.add({"x": "kh", "ʃ": "sh", "ʒ": "zh", "θ": "th", "tʃ": "ch", "dʒ": "j", "ʔ": "'", "ɾ": "r", "ə": "uh", "ɨ": "y-vowel"}[s])
            if s in LONG: feats.add("long")
            if s in DIPH: feats.add("diph")
            if l == "l": feats.add("l")
            if l == "y" and s == "j": feats.add("y")
        if re.search(r"([bcdfgklmnprstvz])\1", m.lower()): feats.add("double")
    return {"parts": parts, "ipa": "".join(ipa), "f": sorted(feats)}


def reading(text):
    """Per-word reading aids for a rendered phrase or sentence."""
    out = []
    for tok in re.findall(r"[A-Za-z'][A-Za-z'\-]*", text):
        out.append({"w": tok, **say(tok)})
    return out


# ---------- gaps: blank one grammatical piece, choose from its family ----------
GAP_SETS = {
    "ending": ["object-wizh", "ongoing", "past-un", "plural", "toward", "humble", "adverbial"],
    "evidential": ["ev-seen", "ev-inferred", "ev-reported", "ev-melded"],
}


def gaps(template, forms):
    out = []
    keys = re.findall(r"\{([^}]+)\}", template)
    for family, members in GAP_SETS.items():
        for idx, k in enumerate(keys):
            if k not in members:
                continue
            n = [0]

            def repl(m):
                i = n[0]; n[0] += 1
                return "___" if i == idx else forms[m.group(1)]
            shown = re.sub(r"\{([^}]+)\}", repl, template)
            shown = re.sub(r"(^|[.?!:]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), shown)
            out.append({"text": shown, "answer": forms[k], "options": [forms[x] for x in members if x in forms]})
    return out


def kind(rendered):
    if re.search(r"[.?!]$", rendered):
        return "s"
    return "p" if " " in rendered else "w"


def item_id(template):
    return hashlib.sha1(template.encode()).hexdigest()[:8]


def main():
    with open(ROOT / "lexicon" / "lexicon.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    forms = form_map(rows)
    plan = json.loads((ROOT / "corpus" / "course.json").read_text())
    missing = []

    def check(t, where):
        for k in re.findall(r"\{([^}]+)\}", t):
            if k not in forms:
                missing.append(f"{where}: {{{k}}}")

    def rend(t):
        out = render(t, forms)
        return out[0].upper() + out[1:] if kind(out) == "s" else out

    seen = {}
    units_out = []
    for u in plan["units"]:
        items = []
        for it in u["items"]:
            check(it["t"], u["id"])
            iid = item_id(it["t"])
            if iid in seen:
                raise SystemExit(f"duplicate item {it['t']} in {u['id']} and {seen[iid]}")
            seen[iid] = u["id"]
            v = rend(it["t"])
            tiles = re.sub(r"[.?!,:]", "", render(it["t"], forms, sentence_case=False)).split()
            items.append({"id": iid, "v": v, "en": it["en"], "k": kind(v), "read": reading(v), "gaps": gaps(it["t"], forms),
                          "tiles": tiles})
        errs = []
        for e in u.get("errors", []):
            for t in [e["right"], *e["wrong"]]:
                check(t, u["id"] + " errors")
            errs.append({"en": e["en"], "right": rend(e["right"]), "wrong": [rend(w) for w in e["wrong"]], "why": e["why"]})
        units_out.append({"id": u["id"], "title": u["title"], "lesson": u.get("lesson"), "from": u.get("from"), "level": u.get("level", "foundations"),
                          "tip": u["tip"], "items": items, "errors": errs})
    stories = []
    for s in plan["stories"]:
        lines = []
        for ln in s["lines"]:
            check(ln["t"], "story " + s["id"])
            v = rend(ln["t"])
            lines.append({"who": ln["who"], "v": v, "en": ln["en"], "read": reading(v)})
        stories.append({**{k: s[k] for k in ("id", "title", "after", "setting", "questions")}, "lines": lines})
    if missing:
        raise SystemExit("UNRESOLVED KEYS: " + ", ".join(missing))

    data = {"levels": plan["levels"], "units": units_out, "stories": stories,
            "built": datetime.date.today().strftime("%d %b %Y"),
            "lexiconSize": len(rows)}
    page = (ROOT / "tools" / "course.template.html").read_text().replace(
        "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    out = ROOT / "course" / "vuhlkansu-course.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    n = sum(len(u["items"]) for u in units_out)
    print(f"wrote {out} ({len(page) // 1024} KB): {len(units_out)} units, {n} items, {len(stories)} stories")


if __name__ == "__main__":
    main()
