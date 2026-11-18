"""Proves the UTP core reproduces the Vulcan dictionary and changes nothing.

  python3 utp/tests/test_vulcan_pack.py

1. No-touch: every Vulcan file the pack reads has the same SHA-256 after the run as before.
2. The sound-law test cases in rules.json pass in the core engine.
3. The core engine gives the same output as vulcan-conlang/tools/sca.py for every
   proto form and compound piece, in every branch.
4. The core phonotactics agree with the Vulcan root-shape check (shape_ok in
   tools/lexicon.py) on every root and on 20,000 seeded random strings.
5. Every dictionary entry's Standard, Ceremonial and Romulan forms, and its IPA
   reading, come out of the core identical to lexicon.csv.
"""
import hashlib
import importlib.util
import pathlib
import random
import re
import sys

UTP = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UTP.parent))
from utp.core import Pack  # noqa: E402

pack = Pack("vulcan")
VC = pack.root / "vulcan-conlang"
WATCHED = [pack.path("sound_laws"), pack.path("lexicon"), pack.path("meanings"), VC / "tools" / "phon.py",
           VC / "tools" / "sca.py", VC / "tools" / "lexicon.py"]


def hashes():
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in WATCHED if p.exists()}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


def oracle_shape_ok():
    """The live shape_ok from tools/lexicon.py; if that module cannot load here (it needs the
    whole vulcan-conlang folder), a verbatim copy of it, taken 2026-11-14."""
    try:
        return load(VC / "tools" / "lexicon.py", "vc_lexicon").shape_ok, "live tools/lexicon.py"
    except Exception:
        P = pack.laws.proto
        UNITS = sorted(P["units"], key=len, reverse=True)
        VOW = set(P["vowels"])

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
        return shape_ok, "verbatim copy (tools/lexicon.py not loadable here)"


def main():
    before = hashes()
    fails, report = 0, []

    # 2. attested sound-law pairs
    t = pack.laws.run_tests()
    bad = [x for x in t if not x[4]]
    fails += len(bad)
    report.append(f"[{'PASS' if not bad else 'FAIL'}] sound-law test cases: {len(t) - len(bad)}/{len(t)}")

    # 3. engine equivalence against the live tools/sca.py
    orig = load(VC / "tools" / "sca.py", "vc_sca")
    rows = pack.rows()
    forms = {r["proto"] for r in rows if r["proto"]}
    for r in rows:
        if r["kind"] == "compound":
            forms |= {p for p in re.findall(r"[^\s+\-{}]+", re.sub(r"\{[^}]+\}", " ", r["parts"]))}
    forms |= {x["proto"] for x in pack.laws.data.get("tests", [])}
    diff = [(f, b) for f in sorted(forms) for b in pack.laws.branches if pack.laws.apply(f, b) != orig.apply(f, b)]
    fails += len(diff)
    report.append(f"[{'PASS' if not diff else 'FAIL'}] engine vs tools/sca.py: {len(forms)} forms x "
                  f"{len(pack.laws.branches)} branches, {len(diff)} differences {diff[:5]}")

    # 4. phonotactics against shape_ok
    shape_ok, which = oracle_shape_ok()
    rng = random.Random(1701)
    units = pack.laws.proto["units"]
    samples = {r["proto"] for r in rows if r["proto"] and r["kind"] not in ("compound", "loan")}
    samples |= {"".join(rng.choice(units) for _ in range(rng.randint(1, 7))) for _ in range(20000)}
    pdiff = [s for s in sorted(samples) if pack.phonotactics.check(s)[0] != shape_ok(s)[0]]
    legal = sum(pack.phonotactics.check(s)[0] for s in samples)
    fails += len(pdiff)
    report.append(f"[{'PASS' if not pdiff else 'FAIL'}] phonotactics vs shape_ok ({which}): {len(samples)} strings "
                  f"({legal} legal), {len(pdiff)} disagreements {pdiff[:5]}")

    # 5. the whole dictionary
    d = pack.deriver(rows)
    reading = pack.helper("reading")
    cols = pack.meta["derivation"]["branches"]
    mism = []
    for r in rows:
        got = d.derive(r)
        got["ipa"] = reading(got[pack.meta["derivation"]["standard"]]) if got[pack.meta["derivation"]["standard"]] else ""
        for c in cols + ["ipa"]:
            if got[c] != r[c]:
                mism.append((r["id"], r["key"], c, got[c], r[c]))
    fails += len(mism)
    report.append(f"[{'PASS' if not mism else 'FAIL'}] dictionary reproduced: {len(rows)} entries x {len(cols) + 1} "
                  f"columns, {len(mism)} mismatches {mism[:5]}")

    # 1. no-touch
    after = hashes()
    changed = [str(p) for p in before if before[p] != after.get(p)]
    fails += len(changed)
    report.insert(0, f"[{'PASS' if not changed else 'FAIL'}] no-touch: {len(before)} Vulcan files hashed before "
                     f"and after, {len(changed)} changed {changed}")

    print("\n".join(report))
    print("ALL PASS" if not fails else f"{fails} FAILURES")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
