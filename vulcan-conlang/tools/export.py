"""Export the publication set from the dictionary: rendered docs, dictionaries and the phrasebook.

Inputs: lexicon/lexicon.csv, docs_src/*.md (templates with {key}), corpus/phrasebook.csv
Output: docs/*.md, docs/dictionary-*.md, docs/phrasebook.md
Run from the project root: python3 tools/export.py   (fails if any {key} does not resolve)
"""
import csv
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from templates import render, form_map, load_lex  # noqa: E402

OUT = ROOT / "docs"
STATUS = {"reconstructed": "canon", "aligned": "canon, aligned", "designed": "designed", "generated": "root",
          "compound": "built", "loan": "loan"}


def stats(rows):
    c = Counter(r["status"] for r in rows)
    rom = sum(r["era"] == "Romulan" for r in rows)
    canon = c["reconstructed"] + c["aligned"]
    return (f"The dictionary has {len(rows):,} entries: {canon} canon words, {c['generated']:,} roots, "
            f"{c['compound']} words built from older ones, {c['designed']} designed words and {c['loan']} loan; "
            f"{rom} of the entries are Romulan only.")


def entry_line(r, col):
    form = r[col]
    bits = [f"**{form}**", f"*{r['pos']}*", r["gloss"]]
    meta = [r["era"]]
    if r["register"] != "everyday":
        meta.append(r["register"])
    meta.append(STATUS.get(r["status"], r["status"]))
    if r["status"] == "compound" and r["parts"]:
        meta.append("built from " + re.sub(r"\{([^}]+)\}", lambda m: m.group(1), r["parts"]))
    if col == "vulcan" and r["romulan"]:
        meta.append(f"Romulan {r['romulan']}")
    if r["source"]:
        meta.append(r["source"])
    return " — ".join(bits) + " (" + "; ".join(meta) + ")"


def dictionaries(rows):
    vul = sorted((r for r in rows if r["vulcan"]), key=lambda r: r["vulcan"].lower().lstrip("'-"))
    rom = sorted((r for r in rows if r["era"] == "Romulan"), key=lambda r: r["romulan"].lower().lstrip("'-"))
    eng = sorted((r for r in rows if r["vulcan"]), key=lambda r: r["gloss"].lower().lstrip("(-'"))

    def by_letter(items, keyf, line):
        groups = defaultdict(list)
        for r in items:
            k = keyf(r)[:1].upper()
            groups[k if k.isalpha() else "#"].append(line(r))
        return "\n\n".join(f"## {L}\n\n" + "\n".join("- " + x for x in groups[L]) for L in sorted(groups))

    head = ("Generated from `lexicon/lexicon.csv` by `tools/export.py`; do not edit by hand. "
            "Each entry: form, part of speech, meaning (era; register if not everyday; source type; parts if built).\n\n")
    (OUT / "dictionary-vulcan-english.md").write_text(
        "# Vulcan–English dictionary\n\n" + head + by_letter(vul, lambda r: r["vulcan"].lstrip("'-"), lambda r: entry_line(r, "vulcan")) + "\n")
    (OUT / "dictionary-english-vulcan.md").write_text(
        "# English–Vulcan dictionary\n\n" + head + by_letter(
            eng, lambda r: r["gloss"].lstrip("(-'"),
            lambda r: f"{r['gloss']} — **{r['vulcan']}** *{r['pos']}* ({r['era']}"
                      + (f"; {r['register']}" if r['register'] != 'everyday' else "") + ")") + "\n")
    (OUT / "dictionary-romulan.md").write_text(
        "# Romulan dictionary (Romulan-only words)\n\n"
        "Every Vulcan entry also has an inherited Romulan form, shown in the Vulcan–English dictionary. "
        "These are the words coined or attested in Romulan after the Sundering.\n\n"
        + by_letter(rom, lambda r: r["romulan"].lstrip("'-"), lambda r: entry_line(r, "romulan")) + "\n")
    return len(vul), len(rom)


def phrasebook(rows):
    fv, fr = form_map(rows), form_map(rows, "r")
    pb = list(csv.DictReader(open(ROOT / "corpus" / "phrasebook.csv", newline="")))
    out, cat = ["# Phrasebook\n", "Generated from `corpus/phrasebook.csv`; every Vulcan line is a template, so it always matches the dictionary.\n"], None
    for p in pb:
        text = render(p["template"], fv) if p.get("template") else p["vulcan"]
        miss = re.findall(r"\{([^}]+)\}", p.get("template", "") + p["notes"])
        miss = [k for k in miss if k not in fv]
        if miss:
            raise SystemExit(f"phrasebook {p['id']}: unknown keys {miss}")
        if p["category"] != cat:
            cat = p["category"]
            out.append(f"\n## {cat}\n\n| {'Romulan' if p.get('lang') == 'r' else 'Vulcan'} | English | Note |\n|---|---|---|")
        out.append(f"| {text} | {p['english']} | {render(p['notes'], fv, sentence_case=False)} |")
    (OUT / "phrasebook.md").write_text("\n".join(out) + "\n")
    return len(pb)


def main():
    rows = load_lex()
    OUT.mkdir(exist_ok=True)
    forms = form_map(rows)
    bad = []
    for src in sorted((ROOT / "docs_src").glob("*.md")):
        text = src.read_text().replace("@STATS@", stats(rows))
        done = render(text, forms, sentence_case=False)
        # an italic example that is a whole sentence starts with a capital
        done = re.sub(r"\*([a-z])([^*\n]*[.?!])\*", lambda m: "*" + m.group(1).upper() + m.group(2) + "*", done)
        bad += [f"{src.name}: {m}" for m in re.findall(r"\?[\w'-]+", done) if m[1:] not in forms and "?" + m[1:] == m]
        (OUT / src.name).write_text(done)
    nv, nr = dictionaries(rows)
    npb = phrasebook(rows)
    unresolved = [b for b in bad if re.search(r"\?[a-z]", b)]
    print(f"docs rendered; dictionaries: {nv} Vulcan, {nr} Romulan-only; phrasebook {npb} lines")
    if unresolved:
        print("UNRESOLVED KEYS:", unresolved)
        sys.exit(1)


if __name__ == "__main__":
    main()
