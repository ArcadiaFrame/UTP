"""Sound-change applier for the Vulcan language family.

Rules, branches and test cases live in tools/rules.json, the same file the
Vuhlkansu Lab page is built from. Laws are ordered regex rewrites on each word;
a branch with "inherits" runs its parent's laws first (Standard Vulcan runs the
Classical laws, then its own 2240s smoothing). Replacements use $1-style groups.

  python3 tools/sca.py              run the test cases
  python3 tools/sca.py "*proto"     derive one form in every branch
"""
import json, pathlib, re, sys

RULES = json.loads((pathlib.Path(__file__).parent / "rules.json").read_text())
BRANCHES = list(RULES["branches"])


def chain(branch):
    b = RULES["branches"][branch]
    return (chain(b["inherits"]) if b.get("inherits") else []) + b["rules"]


def _py(rep):
    return re.sub(r"\$(\d)", r"\\\1", rep)


def apply(form, branch, trace=False):
    out, traces = [], []
    for w in form.lstrip("*").split():
        steps = [w]
        for r in chain(branch):
            new = re.sub(r["pattern"], _py(r["replace"]), w)
            if new != w:
                steps.append(f"{r['id']}:{new}")
                w = new
        out.append(w)
        traces.append(steps)
    return (" ".join(out), traces) if trace else " ".join(out)


def run_tests(verbose=True):
    ok = True
    for t in RULES["tests"]:
        if verbose:
            print(f"{t['proto']} '{t['gloss']}' ({t['kind']})")
        for b in BRANCHES:
            if b not in t:
                continue
            res, tr = apply(t["proto"], b, trace=True)
            good = res == t[b]
            ok &= good
            if verbose:
                print(f"  {b:11} {res:12} {'OK' if good else 'FAIL (want ' + t[b] + ')'}   {tr}")
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1:
        form = " ".join(sys.argv[1:])
        for b in BRANCHES:
            res, tr = apply(form, b, trace=True)
            print(f"{b:11} {res:16} {tr}")
        sys.exit()
    print("ALL PASS" if run_tests() else "SOME FAILED")
