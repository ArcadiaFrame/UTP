"""Templates keep every Vulcan sentence in the project in step with the dictionary.

A template writes words by dictionary key: {come}-{past-un} renders as sarla-un.
  {key}      the word's Standard Vulcan form (Romulan form in a Romulan template)
  {key}{key} joined with no hyphen (tan + fi -> tanfi)
  Anything outside braces is kept as written (names, punctuation).
render(text, lang) is used by build_lab.py and export.py.
to_template(sentence, lexicon_rows) turns a written sentence back into a template (used once, to convert).
"""
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_lex(path=None):
    with open(path or ROOT / "lexicon" / "lexicon.csv", newline="") as f:
        return list(csv.DictReader(f))


def form_map(rows, lang="v"):
    col = "romulan" if lang == "r" else "vulcan"
    return {r["key"]: r[col] for r in rows if r[col]}


def render(text, forms, sentence_case=True):
    out = re.sub(r"\{([^}]+)\}", lambda m: forms.get(m.group(1), "?" + m.group(1)), text)
    if not sentence_case:
        return out
    # sentence case: first letter, and the first letter after . ? ! or :
    return re.sub(r"(^|[.?!:]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), out)


SUFFIX_KEYS = ["past-un", "object-wizh", "toward", "ongoing", "causative", "adverbial", "plural", "honorific",
               "humble", "kam", "them-bi"]
PREFIX_KEYS = ["perfect-ki", "t'"]


def to_template(sentence, rows):
    """Best-effort conversion of a written Vulcan sentence into {key} form. Unknown pieces stay literal."""
    by_form = {}
    for r in rows:
        if r["vulcan"] and r["era"] != "Romulan":
            by_form.setdefault(r["vulcan"].lower(), r["key"])
    suffixes = sorted(((by_form_key, r["vulcan"]) for r in rows for by_form_key in [r["key"]]
                       if r["key"] in SUFFIX_KEYS and r["vulcan"]), key=lambda x: -len(x[1]))
    prefixes = [(r["key"], r["vulcan"]) for r in rows if r["key"] in PREFIX_KEYS and r["vulcan"]]
    multi = sorted((f for f in by_form if " " in f), key=len, reverse=True)

    def word(w):
        lw = w.lower()
        if lw in by_form:
            return "{%s}" % by_form[lw]
        if "-" in lw:
            parts = w.split("-")
            for i in range(len(parts) - 1, 0, -1):        # longest known head first (ish-ve, suthnoo-wizh)
                head = "-".join(parts[:i]).lower()
                if head in by_form:
                    rest = [word(p) for p in parts[i:]]
                    return "{%s}" % by_form[head] + "".join("-" + x for x in rest)
            return "-".join(word(p) for p in parts)
        for key, form in prefixes:
            if lw.startswith(form) and len(lw) > len(form):
                rest = w[len(form):]
                if rest[:1].isupper():
                    return "{%s}" % key + rest
                inner = word(rest)
                if "{" in inner:
                    return "{%s}" % key + inner
        for key, form in suffixes:
            if lw.endswith(form) and len(lw) > len(form) + 1:
                inner = word(w[:-len(form)])
                if inner.startswith("{") and inner.endswith("}"):
                    return inner + "{%s}" % key
        if lw.startswith("wim") and lw.endswith("ish"):
            return "{be}ish"
        return w

    s = sentence
    for m in multi:                                       # fixed phrases first (pash ta, t'nar ...)
        s = re.sub(r"(?i)\b" + re.escape(m) + r"\b", "{%s}" % by_form[m], s)
    tokens = re.split(r"(\{[^}]+\}|[\s.,?!:;()]+)", s)
    out = []
    for t in tokens:
        if not t or t.startswith("{") or re.fullmatch(r"[\s.,?!:;()]+", t):
            out.append(t)
        else:
            out.append(word(t))                           # a capitalised word that finds no key stays as a name
    return "".join(out)
