"""Build the UTP universal meaning registry from Concepticon.

  python3 utp/concepts/build_concepts.py /path/to/concepticon-data

Writes utp/concepts/concepts.csv: one row per meaning, language-neutral. English
glosses are labels only; no language's words are built from them. Run once (the
CSV ships with the UTP, so nothing here is needed offline).

The same anthropological rules the Vulcan build used decide each meaning's place:
  tier 1  core: in a Swadesh or Leipzig-Jakarta list (the oldest, most stable meanings) -> roots, earliest era
  tier 2  basic: in the World Loanword Database or Intercontinental Dictionary Series lists -> roots
  tier 3  extended: everything else -> roots, unless built from older meanings (below)
  colour terms enter in the Berlin-Kay order; "Modern world" meanings come last
  a meaning whose label is a derivation or compound of other meanings is built from
  them, never given a root of its own (teacher = teach + agent; black pepper = black + pepper)

Concepticon: List, Johann-Mattis et al. (CC BY 4.0), https://concepticon.clld.org
"""
import csv
import pathlib
import re
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
POS = {"Person/Thing": "noun", "Action/Process": "verb", "Property": "adjective", "Number": "number",
       "Classifier": "classifier", "Other": "particle"}
WOLD_POS = {"Noun": "noun", "Verb": "verb", "Adjective": "adjective", "Adverb": "adverb", "Pronoun": "pronoun",
            "Numeral": "number", "Conjunction": "conjunction", "Interrogative": "particle", "Preposition": "particle"}
CORE_LISTS = re.compile(r"^(Swadesh-19\d\d-\d+[ab]?|Tadmor-2009-100)\.tsv$")
BASIC_LISTS = {"Haspelmath-2009-1460.tsv", "Key-2016-1310.tsv"}
# Berlin-Kay stages: I-II black, white, red; III-IV green, yellow; V blue; VI brown; VII the rest
COLOUR_RANK = {"BLACK": 0, "WHITE": 0, "RED": 0, "GREEN": 1, "YELLOW": 1, "BLUE": 2, "BROWN": 2,
               "PURPLE": 3, "PINK": 3, "ORANGE (COLOR)": 3, "GREY": 3, "GRAY": 3}
# derivations recognisable from the label: (ending, base pos, affix meaning, result pos)
DERIVED_BY_LABEL = [("ER", "verb", "agent", "noun"), ("R", "verb", "agent", "noun"), ("OR", "verb", "agent", "noun"),
                    ("ING", "verb", "action", "noun"), ("MENT", "verb", "action", "noun"),
                    ("NESS", "adjective", "abstract", "noun"), ("ITY", "adjective", "abstract", "noun"),
                    ("Y", "noun", "adjectival", "adjective")]
# labels that only look derived (bus + y, shin + y, slipper + y ...), checked by hand
FALSE_FRIENDS = {"BUSY", "GELDING", "PRAYER", "SHINY", "SLIPPERY", "STICKY", "SWEATER", "DRAWER"}


def slug(gloss):
    s = gloss.lower().replace("(", " ").replace(")", " ").replace("/", " ").replace(",", " ")
    return re.sub(r"[^a-z0-9']+", "-", s).strip("-")


def main(cdir):
    cdir = pathlib.Path(cdir) / "concepticondata"
    rows = [r for r in csv.DictReader(open(cdir / "concepticon.tsv", newline=""), delimiter="\t")
            if not r["REPLACEMENT_ID"]]
    lists, core, basic, wold = Counter(), set(), set(), {}
    for p in sorted((cdir / "conceptlists").glob("*.tsv")):
        ids = {r.get("CONCEPTICON_ID") for r in csv.DictReader(open(p, newline=""), delimiter="\t")} - {None, ""}
        lists.update(ids)
        if CORE_LISTS.match(p.name):
            core |= ids
        if p.name in BASIC_LISTS:
            basic |= ids
        if p.name == "Haspelmath-2009-1460.tsv":
            for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
                if r["CONCEPTICON_ID"]:
                    wold.setdefault(r["CONCEPTICON_ID"], r)

    out, seen = [], set()
    for r in rows:
        cid = r["ID"]
        key = slug(r["GLOSS"])
        if key in seen:
            key = f"{key}-c{cid}"
        seen.add(key)
        w = wold.get(cid, {})
        pos = WOLD_POS.get(w.get("PART_OF_SPEECH", ""), POS.get(r["ONTOLOGICAL_CATEGORY"], "noun"))
        tier = 1 if cid in core else 2 if cid in basic else 3
        rank = {1: 0, 2: 1, 3: 2}[tier]
        if r["SEMANTICFIELD"] == "Modern world":
            rank = 3
        if r["GLOSS"] in COLOUR_RANK:
            rank = COLOUR_RANK[r["GLOSS"]]
        out.append({"cid": f"C{int(cid):05d}", "key": key, "gloss": r["GLOSS"].lower(), "pos": pos,
                    "field": slug(r["SEMANTICFIELD"] or "other"), "tier": tier, "rank": rank,
                    "lists": lists[cid], "age": w.get("AGE_SCORE", ""), "kind": "root", "parts": "", "head": "",
                    "definition": r["DEFINITION"].replace("\n", " ").strip(),
                    "source": f"Concepticon {cid}"})

    # meanings built from other meanings, recognised from their labels
    by_gloss = {o["gloss"].upper(): o for o in out}
    by_head = {}                                       # "LEAD (GUIDE)" is found by its head word LEAD
    for o in out:
        by_head.setdefault(o["gloss"].upper().split(" (")[0], []).append(o)
    derived = compounds = 0
    for o in out:
        g = o["gloss"].upper()
        if o["tier"] == 1 or g in FALSE_FRIENDS:
            continue                                   # the oldest meanings stay roots, as in Vulcan
        for end, bpos, affix, rpos in DERIVED_BY_LABEL:
            if not (g.endswith(end) and len(g) - len(end) >= 3 and o["pos"] == rpos):
                continue
            stem = g[: -len(end)]
            cands = [by_gloss[stem]] if stem in by_gloss else []
            cands += [c for c in by_head.get(stem, []) if c not in cands]
            base = next((c for c in cands if c["pos"] == bpos and c is not o), None)
            if base:
                o.update(kind="derived", parts=f"{{{base['key']}}}+{{{affix}}}", head=base["key"])
                derived += 1
                break
        else:
            words = [w for w in re.split(r"[\s\-]+", g) if w]
            if len(words) == 2 and all(w in by_gloss for w in words) and "(" not in g:
                a, b = (by_gloss[w] for w in words)
                o.update(kind="compound", parts=f"{{{a['key']}}} {{{b['key']}}}", head=b["key"])
                compounds += 1
    # a built meaning can be no older than its parts
    rank = {o["key"]: o["rank"] for o in out}
    for o in out:
        for k in re.findall(r"\{([^}]+)\}", o["parts"]):
            o["rank"] = max(o["rank"], rank.get(k, 1))
    fields = ["cid", "key", "gloss", "pos", "field", "tier", "rank", "lists", "age", "kind", "parts", "head",
              "definition", "source"]
    with open(HERE / "concepts.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(sorted(out, key=lambda o: o["cid"]))
    # every single English word used as a label anywhere in Concepticon: a blocklist, so that a
    # generated word is never also a common English word (the Vulcan check W1)
    eng = set()
    for g in [r["GLOSS"] for r in rows]:
        eng |= set(re.findall(r"[a-z]+", g.lower()))
    for p in sorted((cdir / "conceptlists").glob("*.tsv")):
        for r in csv.DictReader(open(p, newline=""), delimiter="\t"):
            for col in ("ENGLISH", "GLOSS"):
                eng |= set(re.findall(r"[a-z]+", (r.get(col) or "").lower()))
    eng = sorted(w for w in eng if len(w) >= 2)
    (HERE / "english_labels.txt").write_text("\n".join(eng) + "\n")
    print(f"{len(eng)} English label words written to english_labels.txt")
    t = Counter(o["tier"] for o in out)
    print(f"{len(out)} meanings: tier 1 {t[1]}, tier 2 {t[2]}, tier 3 {t[3]}; "
          f"{derived} recognised as derivations, {compounds} as compounds")


if __name__ == "__main__":
    main(sys.argv[1])
