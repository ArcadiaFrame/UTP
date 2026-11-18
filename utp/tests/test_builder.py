"""The UTP builder at full scale.

  python3 utp/tests/test_builder.py

1. The Vulcan pack cannot be built (its dictionary is made by vulcan-conlang/tools).
2. The sample pack builds 8,000+ entries with 0 errors.
3. The build is deterministic: a fresh build gives a byte-identical lexicon.csv.
4. A rebuild keeps every word: adding meanings changes no existing word or id.
5. Nothing is listed twice: no template meaning duplicates a registry meaning
   (teacher = teach + agent exists, so no separate "one who: teach"), no meaning or spelling twice.
6. Every built word is dated no earlier than its parts, and every part resolves.
"""
import csv
import hashlib
import json
import pathlib
import re
import shutil
import sys
import tempfile

UTP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UTP.parent))
from utp.core import Pack  # noqa: E402
from utp.core.builder import Builder, BuildRefused  # noqa: E402


def main():
    report, fails = [], 0

    def check(ok, text):
        nonlocal fails
        fails += not ok
        report.append(f"[{'PASS' if ok else 'FAIL'}] {text}")

    try:
        Builder(Pack("vulcan"))
        check(False, "Vulcan pack refused by the builder")
    except BuildRefused:
        check(True, "Vulcan pack refused by the builder (read-only)")

    tmp = pathlib.Path(tempfile.mkdtemp())
    src = UTP / "packs" / "sample"
    work = tmp / "packs" / "sample"
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("build", "meanings.csv", "exclude.txt"))
    shutil.copytree(UTP / "concepts", tmp / "concepts")      # the blocklist path is relative to the pack
    lex = work / "build" / "lexicon.csv"
    digest = lambda: hashlib.sha256(lex.read_bytes()).hexdigest()  # noqa: E731

    rows, errors, warnings = Builder(Pack(work)).build()
    check(len(rows) >= 8000 and not errors, f"sample pack: {len(rows)} entries, {len(errors)} errors {errors[:3]}")
    first = digest()
    shutil.rmtree(work / "build")
    Builder(Pack(work)).build()
    check(digest() == first, "fresh build is byte-identical (deterministic)")

    before = {r["key"]: r for r in csv.DictReader(open(lex, newline=""))}
    (work / "meanings.csv").write_text("key,gloss,pos,field,era,kind,parts\n"
                                       "sky-spirit,spirit of the sky,noun,religion-and-belief,Ancient,root,\n"
                                       "star-road,road of stars,noun,the-physical-world,Middle,compound,{star}-{road}\n")
    rows, errors, _ = Builder(Pack(work)).build()
    after = {r["key"]: r for r in rows}
    moved = [k for k in before if (before[k]["east"], before[k]["id"]) != (after[k]["east"], after[k]["id"])]
    check(not moved and not errors and len(rows) == len(before) + 2,
          f"rebuild with 2 new meanings: {len(moved)} existing words changed, {len(errors)} errors")

    keys = set(after)
    # a template meaning whose registry twin exists would be listed twice: teacher = teach + agent,
    # leader = lead (guide) + agent, darkness = dark + abstract
    twins = {"teacher": "teach.agent", "leader": "lead-guide.agent", "darkness": "dark.abstract", "hunter": "hunt.agent"}
    dup_tpl = [t for reg, t in twins.items() if reg not in keys or t in keys or not after[reg]["parts"]]
    gloss = {}
    for r in rows:
        gloss.setdefault((r["gloss"], r["pos"]), []).append(r["key"])
    spell = {}
    for r in rows:
        spell.setdefault(r["east"], []).append(r["key"])
    check("teacher" in keys and "teach.agent" not in keys and not dup_tpl,
          "no template meaning duplicates a registry meaning (teacher, never teach.agent)")
    check(all(len(v) == 1 for v in gloss.values()) and all(len(v) == 1 for v in spell.values() if v != [""]),
          "no meaning and no spelling listed twice")

    era = {e["id"]: e["rank"] for e in json.loads((work / "pack.json").read_text())["eras"]}
    bad_era = [r["key"] for r in rows for k in re.findall(r"\{([^}]+)\}", r["parts"])
               if era[after[k]["era"]] > era[r["era"]]]
    unresolved = [r["key"] for r in rows if "?" in r["east"] or "?" in r["west"]]
    check(not bad_era and not unresolved, f"built words: {len(bad_era)} dated before a part, {len(unresolved)} unresolved")
    shutil.rmtree(tmp)
    print("\n".join(report))
    print("ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
