"""Build the Vuhlkansu Lab page from the corpus and rules files.

Inputs: corpus/canon.csv, corpus/novel.csv, corpus/romulan.csv,
        corpus/duane_rombas_blocks.txt, tools/rules.json, tools/lab.template.html
Output: lab/vuhlkansu-lab.html
Run from the project root: python3 tools/build_lab.py
"""
import csv, datetime, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from phon import words, segment, standardize, ipa, ENGLISH, MULTI, SINGLE  # noqa: E402
import lexicon as L  # noqa: E402


def read_csv(name):
    with open(ROOT / "corpus" / name, newline="") as f:
        return list(csv.DictReader(f))


def romulan_diphthong_share():
    lines = [l for l in (ROOT / "corpus" / "duane_rombas_blocks.txt").read_text().splitlines()
             if l and not l.startswith("#")]
    toks = [t.strip("'-.,;! ").lower() for l in lines for t in l.split(":", 1)[1].split()]
    vowels = [t for t in toks if t and all(c in "aeiouy'" for c in t)]
    long_ = [t for t in vowels if len(t.replace("'", "")) >= 2]
    return round(100 * len(long_) / len(vowels), 1)


def rendered(name):
    """Template rows rendered from the current dictionary, so no sentence can go stale."""
    from templates import render, form_map
    forms = form_map(read_lex())
    out = read_csv(name)
    for r in out:
        if r.get("template"):
            r["vulcan"] = render(r["template"], forms)
        if "{" in r.get("notes", ""):
            r["notes"] = render(r["notes"], forms, sentence_case=False)
    return out


def read_lex():
    with open(ROOT / "lexicon" / "lexicon.csv", newline="") as f:
        return list(csv.DictReader(f))


def lex_check():
    errs, warns = L.check(read_lex())
    return {"errors": len(errs), "exceptions": sum(1 for w in warns if w[1] == "X"), "warnings": sum(1 for w in warns if w[1] != "X")}


LAYER_OF = {"Scharfe/Doohan": "Film I Gol liturgy", "Okrand": "Okrand", "writers": "Episode writers",
            "film": "Film writers", "fan origin (Heydt)": "Episode writers"}

canon, novel, romulan = read_csv("canon.csv"), read_csv("novel.csv"), read_csv("romulan.csv")
tokens = []
for r in canon + novel:
    is_name = r.get("type") in ("name", "place")
    r["std"] = standardize(r["form"], is_name)
    r["ipa"] = ipa(r["form"])
    layer = "Names" if is_name else ("Novels' Old Vulcan" if r["id"].startswith("n") else LAYER_OF.get(r["maker_layer"], r["maker_layer"]))
    for w in words(r["form"]):
        if w not in ENGLISH:
            tokens.append({"id": r["id"], "layer": layer, "w": w, "segs": segment(w)})
for r in romulan:
    r["std"], r["ipa"] = r["form"], ""

data = {
    "canon": canon,
    "novel": novel,
    "romulan": romulan,
    "concepts": read_csv("concepts.csv"),
    "phrasebook": rendered("phrasebook.csv"),
    "examples": rendered("examples.csv"),
    "idioms": rendered("idioms.csv"),
    "interlinear": read_csv("interlinear.csv"),
    "tokens": tokens,
    "lexicon": read_lex(),
    "lexCheck": lex_check(),
    "english": sorted(L.ENGLISH),
    "phon": {"multi": MULTI, "single": SINGLE},
    "gen": {"onset": L.ONSET_W, "medial": L.MED_W, "vowels": L.VOW_W, "finals": L.FIN_W,
            "harsh": sorted(L.HARSH), "soft": sorted(L.SOFT), "tones": L.FIELD_TONE,
            "shapes": L.SHAPES},
    "rules": json.loads((ROOT / "tools" / "rules.json").read_text()),
    "romulanDiphthongShare": romulan_diphthong_share(),
    "built": datetime.date.today().strftime("%d %b %Y"),
}
page = (ROOT / "tools" / "lab.template.html").read_text().replace(
    "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
out = ROOT / "lab" / "vuhlkansu-lab.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f"wrote {out} ({len(page) // 1024} KB), {len(canon)} canon, {len(novel)} novel, "
      f"{len(romulan)} Romulan entries, {len(data['concepts'])} concepts, {len(data['idioms'])} idioms")
