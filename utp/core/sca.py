"""UTP sound-change engine: language-independent.

Reads the sound-laws format (UTP format v1, which is the format the Vulcan
project already uses in vulcan-conlang/tools/rules.json):

  {"proto":    {"units": [...], "vowels": [...], "onset_clusters": [...], "finals": [...]},
   "branches": {"<id>": {"label": ..., "inherits": "<parent id>"?, "rules": [
                   {"id": ..., "pattern": <regex>, "replace": <with $1 groups>, "note": ..., "era": ...}]}},
   "tests":    [{"proto": "*form", "<branch id>": "<expected>", ...}]}

Laws are ordered regex rewrites applied to each word of a form. A branch that
inherits runs its parent's whole chain first, so the branches form a family tree
rooted in the proto-language. Nothing here knows about any particular language.
"""
import re


def _py_replacement(rep):
    """$1-style groups (the format's convention) to Python's \\1."""
    return re.sub(r"\$(\d)", r"\\\1", rep)


class SoundLaws:
    def __init__(self, data):
        self.data = data
        self.proto = data.get("proto", {})
        self.branches = list(data["branches"])
        self._chains = {}

    # ---- the family tree ----
    def parent(self, branch):
        return self.data["branches"][branch].get("inherits")

    def lineage(self, branch):
        """Proto-language first, then each ancestor branch, then the branch itself."""
        line = []
        while branch:
            line.insert(0, branch)
            branch = self.parent(branch)
        return ["proto"] + line

    def tree(self):
        """{branch: parent or 'proto'} for every branch."""
        return {b: self.parent(b) or "proto" for b in self.branches}

    # ---- applying the laws ----
    def chain(self, branch):
        if branch not in self._chains:
            b = self.data["branches"][branch]
            rules = (self.chain(b["inherits"]) if b.get("inherits") else []) + [
                (r["id"], re.compile(r["pattern"]), _py_replacement(r["replace"])) for r in b["rules"]]
            self._chains[branch] = rules
        return self._chains[branch]

    def apply(self, form, branch, trace=False):
        out, traces = [], []
        for w in form.lstrip("*").split():
            steps = [w]
            for rid, rx, rep in self.chain(branch):
                new = rx.sub(rep, w)
                if new != w:
                    steps.append(f"{rid}:{new}")
                    w = new
            out.append(w)
            traces.append(steps)
        return (" ".join(out), traces) if trace else " ".join(out)

    def run_tests(self):
        """Every attested pair in the file: list of (proto, branch, got, want, ok)."""
        results = []
        for t in self.data.get("tests", []):
            for b in self.branches:
                if b in t:
                    got = self.apply(t["proto"], b)
                    results.append((t["proto"], b, got, t[b], got == t[b]))
        return results
