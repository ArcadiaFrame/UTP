"""UTP lexicon engine: turn dictionary rows into forms in every branch.

A row is one meaning. Its "kind" says how its forms are made:

  root      (any kind not named below) the proto form runs through each branch's laws
  compound  "parts" names older words: {key} for a word, + to fuse, - to hyphenate;
            each piece is derived in each branch, then joined
  loan      borrowed whole into one branch, spelled as attested, never aged by sound laws

and two pack-level rules cover what history adds:

  coined_in_branch  an era that belongs to one branch (a word coined after a split)
                    exists only in that branch, spelled as attested when it has one
  exceptions        a row with a logged exception keeps its attested forms

The standard branch gets the pack's orthography (its spelling standard) on each
space- and hyphen-separated piece. Nothing here knows about any one language:
which kinds, branches and eras mean what is set in the pack.
"""
import re

TOKEN = re.compile(r"\{[^}]+\}|[^\s+\-]+")


def piecewise(fn, form):
    """Apply an orthography to each piece, keeping the form's own spaces and hyphens."""
    return " ".join("-".join(fn(p) if p else p for p in w.split("-")) for w in form.split(" "))


class Deriver:
    def __init__(self, laws, config, orthography=None):
        self.laws = laws
        self.branches = config["branches"]
        self.standard = config["standard"]
        self.kind_compound = config["kinds"]["compound"]
        self.kind_loan = config["kinds"]["loan"]
        self.loan_branch = config.get("loan_branch", self.standard)
        self.coined_in = config.get("coined_in_branch", {})
        self.ortho = orthography or (lambda s: s)
        # sound changes at a fused join, applied before the + is removed:
        # [{"pattern": regex, "replace": text, "branches": [only these; all if absent]}]
        self.join_rules = [(re.compile(j["pattern"]), j["replace"], j.get("branches"))
                           for j in config.get("join_rules", [])]
        self.key_proto, self.loans, self.excepts, self.protos = {}, {}, {}, set()

    def index(self, rows):
        """Everything compounds look up: each key's proto, loans, and logged exceptions."""
        for r in rows:
            if r.get("proto"):
                self.protos.add(r["proto"])
                self.key_proto[r["key"]] = r["proto"]
            if r["kind"] == self.kind_loan and r.get(self.loan_branch):
                self.loans[r["key"]] = r[self.loan_branch]
            if r.get("exception") and r.get(f"attested_{self.standard}"):
                self.excepts[r["key"]] = r[f"attested_{self.standard}"]

    def _compound(self, parts, b):
        def sub(m):
            part = m.group(0)
            if part.startswith("{"):
                key = part.strip("{}")
                if key in self.loans:
                    return self.loans[key]
                if b == self.standard and key in self.excepts:
                    return self.excepts[key]
                part = self.key_proto.get(key, "?" + part)
            if part not in self.protos:
                return "?" + part
            out = self.laws.apply(part, b)
            return self.ortho(out) if b == self.standard else out
        joined = TOKEN.sub(sub, parts)
        for rx, rep, only in self.join_rules:
            if not only or b in only:
                joined = rx.sub(rep, joined)
        return joined.replace("+", "")

    def derive(self, row):
        kind, era = row["kind"], row.get("era", "")
        only = self.coined_in.get(era)
        if only and row.get(f"attested_{only}") and kind != self.kind_compound:
            forms = {b: "" for b in self.branches}
            forms[only] = row[f"attested_{only}"]
        elif kind == self.kind_loan:
            forms = {b: "" for b in self.branches}
            forms[self.loan_branch] = row.get(f"attested_{self.loan_branch}", "")
        elif kind == self.kind_compound:
            forms = {b: self._compound(row["parts"], b) for b in self.branches}
        else:
            forms = {b: self.laws.apply(row["proto"], b) for b in self.branches}
        if only:
            for b in self.branches:
                if b != only:
                    forms[b] = ""
        elif kind not in (self.kind_compound, self.kind_loan) and not row.get("exception") and forms[self.standard]:
            forms[self.standard] = piecewise(self.ortho, forms[self.standard])
        if row.get("exception"):
            for b in self.branches:
                want = row.get(f"attested_{b}")
                if want and forms.get(b) and forms[b] != want:
                    forms[b] = want
        return forms

    def unresolved(self, forms):
        """Branches whose compound named a key with no root form."""
        return [b for b, f in forms.items() if "?" in f]
