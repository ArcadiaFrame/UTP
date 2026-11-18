"""UTP builder: a whole dictionary for a language pack, by the rules the Vulcan build proved.

  meanings   the universal registry (utp/concepts/concepts.csv), the derivation templates
             (utp/concepts/templates.json) and the pack's own meanings (culture words, canon anchors)
  roots      the oldest meanings get roots generated from the proto-language's sound system:
             each meaning seeds its own generator, so a rebuild gives the same dictionary
  built      later meanings are built from older ones, never given roots of their own;
             a built meaning is dated no earlier than its parts
  branches   every form runs through each branch's sound laws
  checks     a candidate root is kept only if it passes every check against what is already
             accepted; nothing is ever listed twice
  frozen     a rebuild keeps every existing word's form and id and only adds new meanings

Checks (as in the Vulcan build):
  E1 root shape outside the proto sound system      E2 same proto form twice
  E3 same spelling for two meanings in a branch     E4 two words that sound the same
  E5 same meaning listed twice                      E6 an attested form the laws fail to produce
  E7 a generated word takes a reserved form         E8 a letter three times in a row; E10 doubled apostrophe
  E9 a built word names a meaning with no form      E11 a built word dated earlier than a part
  W1 a generated form is a word on the pack's blocklist (e.g. common English)

The builder writes only into the pack's own build folder (pack.json "build" -> "out").
A pack without a build section, such as the Vulcan pack, cannot be built: the Vulcan
dictionary is made by vulcan-conlang/tools and stays untouched.
"""
import csv
import hashlib
import json
import pathlib
import random
import re
from collections import Counter

from .lexicon import Deriver

CONCEPTS = pathlib.Path(__file__).resolve().parent.parent / "concepts"
TRIPLE = re.compile(r"([a-z])\1\1")


class BuildRefused(Exception):
    pass


def _weighted(rng, items):
    total = sum(w for _, w in items)
    r = rng.random() * total
    for k, w in items:
        r -= w
        if r <= 0:
            return k
    return items[-1][0]


class Generator:
    """Root candidates from the proto sound system, weighted by the pack."""
    SHORT = {"pronoun", "particle", "conjunction", "interjection", "determiner", "adverb", "auxiliary",
             "number", "suffix", "prefix", "classifier"}

    def __init__(self, proto, cfg, transparent=()):
        cons = [u for u in proto["units"] if u not in proto["vowels"] and u not in transparent]
        uni = lambda xs: {x: 1 for x in xs}  # noqa: E731
        self.onset = cfg.get("onset") or uni(c for c in cons)
        self.clusters = {k: w for k, w in (cfg.get("onset_clusters") or uni(proto.get("onset_clusters", []))).items()}
        self.medial = cfg.get("medial") or uni(cons)
        self.vowel = cfg.get("vowel") or uni(proto["vowels"])
        self.final = cfg.get("final") or uni(proto.get("finals", cons))
        self.shapes = cfg.get("shapes") or {"noun": [["CVC", 3], ["CVCV", 2], ["CVCVC", 2]],
                                            "verb": [["CVC", 3], ["CVCV", 2]], "short": [["CV", 2], ["CVC", 1]]}
        self.harsh, self.soft = set(cfg.get("harsh", [])), set(cfg.get("soft", []))
        self.field_tone = cfg.get("field_tone", {})

    def _pick(self, rng, table, tone):
        items = []
        for k, w in table.items():
            if tone == "harsh":
                w *= 2.5 if k in self.harsh else 0.6 if k in self.soft else 1
            elif tone == "soft":
                w *= 2.0 if k in self.soft else 0.3 if k in self.harsh else 1
            items.append((k, w))
        return _weighted(rng, items)

    def candidate(self, rng, pos, field):
        tone = self.field_tone.get(field)
        group = pos if pos in self.shapes else ("short" if pos in self.SHORT and "short" in self.shapes else "noun")
        shape = _weighted(rng, [(s, w) for s, w in self.shapes[group]])
        out, i = [], 0
        while i < len(shape):
            if shape[i] == "V":
                out.append(self._pick(rng, self.vowel, tone))
                i += 1
            elif shape.startswith("CC", i) and i == 0:
                out.append(self._pick(rng, self.clusters, tone))
                i += 2
            elif i == 0:
                out.append(self._pick(rng, self.onset, tone))
                i += 1
            elif i == len(shape) - 1:
                out.append(self._pick(rng, self.final, tone))
                i += 1
            else:
                out.append(self._pick(rng, self.medial, tone))
                i += 1
        return "".join(out)


class Builder:
    def __init__(self, pack):
        if "build" not in pack.meta:
            raise BuildRefused(f"pack '{pack.name}' has no build section: its dictionary is made elsewhere "
                               "and the UTP only reads it")
        self.pack, self.cfg = pack, pack.meta["build"]
        self.out = (pack.dir / self.cfg.get("out", "build")).resolve()
        if pack.dir not in self.out.parents:
            raise BuildRefused("build output must be a folder inside the pack")
        d = pack.meta["derivation"]
        self.branches, self.std = d["branches"], d["standard"]
        eras = [e for e in pack.meta.get("eras", []) if not e.get("branch")]
        self.era_of_rank = {e["rank"]: e["id"] for e in reversed(eras)}
        self.max_rank = max(self.era_of_rank) if self.era_of_rank else 0
        self.rank_of_era = {e["id"]: e["rank"] for e in pack.meta.get("eras", [])}
        self.reading = pack.helper("reading") or (lambda s: re.sub(r"[\s\-]", "", s.lower()))
        self.ortho = pack.helper("orthography") or (lambda s: s)
        self.gen = Generator(pack.laws.proto, pack.meta.get("generator", {}), pack.phonotactics.transparent)
        self.block = set()
        if self.cfg.get("blocklist"):
            self.block = set((pack.root / self.cfg["blocklist"]).read_text().split())
        self.reserved = set(self.cfg.get("reserved", []))

    # ---------- meanings ----------
    def era(self, rank):
        rank = min(max(rank, 0), self.max_rank)
        while rank not in self.era_of_rank and rank > 0:
            rank -= 1
        return self.era_of_rank.get(rank, "")

    def meanings(self):
        reg = self.cfg.get("registry", {})
        tiers = set(reg.get("tiers", [1, 2, 3]))
        skip_pos = set(reg.get("exclude_pos", ["classifier"]))
        skip_fields = set(reg.get("exclude_fields", []))
        rows, by = [], {}

        def add(r):
            if r["key"] in by:
                by[r["key"]].update({k: v for k, v in r.items() if v not in ("", None)})
                return
            by[r["key"]] = r
            rows.append(r)

        for c in csv.DictReader(open(CONCEPTS / "concepts.csv", newline="")):
            if int(c["tier"]) in tiers and c["pos"] not in skip_pos and c["field"] not in skip_fields:
                add({"key": c["key"], "cid": c["cid"], "gloss": c["gloss"], "pos": c["pos"], "field": c["field"],
                     "rank": int(c["rank"]), "kind": c["kind"], "parts": c["parts"], "head": c["head"],
                     "lists": int(c["lists"]), "source": c["source"]})
        tpl = json.loads((CONCEPTS / "templates.json").read_text())
        position = self.cfg.get("affix_position", {})
        for a in tpl["affixes"]:
            add({"key": a["key"], "cid": f"G-{a['key']}", "gloss": a["gloss"], "pos": position.get(a["key"], a["pos"]),
                 "field": "grammar", "rank": a["rank"], "kind": "root", "parts": "", "lists": 999, "source": "UTP grammar"})
        if self.cfg.get("grammar_morphemes", True):
            for a in tpl.get("grammar", []):
                add({"key": a["key"], "cid": f"G-{a['key']}", "gloss": a["gloss"], "pos": a["pos"], "field": "grammar",
                     "rank": a["rank"], "kind": "root", "parts": "", "lists": 999, "source": "UTP grammar"})
        use = reg.get("templates", "all")
        have = {r["parts"] for r in rows if r["parts"]}
        for t in tpl["templates"]:
            if use != "all" and t["id"] not in use:
                continue
            fields = set(reg.get("template_fields", {}).get(t["id"], t.get("fields", [])))
            for base in [r for r in rows if r["kind"] == "root" and r["pos"] == t["from"] and r["field"] != "grammar"]:
                if fields and base["field"] not in fields:
                    continue
                parts = f"{{{base['key']}}}+{{{t['affix']}}}"
                if parts in have:
                    continue                    # the registry already has this meaning (teacher = teach + agent)
                add({"key": t["key"].format(k=base["key"]), "cid": f"{base['cid']}.{t['id']}",
                     "gloss": t["gloss"].format(g=base["gloss"]), "pos": t["to"], "field": base["field"],
                     "rank": base["rank"], "kind": "derived", "parts": parts, "head": base["key"], "lists": 0,
                     "source": f"template {t['id']}"})
                have.add(parts)
        if (self.pack.dir / self.cfg.get("exclude", "exclude.txt")).exists():
            drop = set((self.pack.dir / self.cfg.get("exclude", "exclude.txt")).read_text().split())
            rows = [r for r in rows if r["key"] not in drop]     # meanings you approved removing (utp.py apply)
            by = {r["key"]: r for r in rows}
        extra = self.cfg.get("meanings", "meanings.csv")
        if (self.pack.dir / extra).exists():
            for r in csv.DictReader(open(self.pack.dir / extra, newline="")):
                r = {k: v for k, v in r.items() if v}
                r.setdefault("kind", "root")
                r.setdefault("parts", "")
                r.setdefault("cid", f"P-{r['key']}")
                if r["kind"] == "compound" and " " not in r["parts"]:
                    r["kind"] = "fixed-compound"       # parts already written in the pack's own order
                r["rank"] = int(r["rank"]) if "rank" in r else self.rank_of_era.get(r.get("era"), 1)
                r.setdefault("lists", 999)
                r.setdefault("source", "pack meanings")
                add(r)
        return rows

    def _normalize(self, rows):
        """Registry parts to Deriver parts, in the pack's order, expanded down to roots."""
        join, ajoin = self.cfg.get("compound_join", "-"), self.cfg.get("affix_join", "+")
        head_first = self.cfg.get("compound_head", "last") == "first"
        prefixes = {r["key"] for r in rows if r.get("pos") == "prefix"}
        by = {r["key"]: r for r in rows}
        for r in rows:
            p = r.get("parts", "")
            if r["kind"] == "fixed-compound":
                r["kind"] = "compound"
            elif r["kind"] == "derived":
                base, affix = re.findall(r"\{([^}]+)\}", p)
                r["parts"] = (f"{{{affix}}}{ajoin}{{{base}}}" if affix in prefixes else f"{{{base}}}{ajoin}{{{affix}}}")
            elif r["kind"] == "compound" and " " in p and "{" in p:
                a, b = re.findall(r"\{([^}]+)\}", p)
                r["parts"] = f"{{{b}}}{join}{{{a}}}" if head_first else f"{{{a}}}{join}{{{b}}}"

        def expand(parts, seen):
            def sub(m):
                k = m.group(1)
                inner = by.get(k)
                if inner and inner["kind"] in ("derived", "compound") and k not in seen:
                    return expand(inner["parts"], seen | {k})
                return m.group(0)
            return re.sub(r"\{([^}]+)\}", sub, parts)
        for r in rows:
            if r["kind"] in ("derived", "compound"):
                r["parts"] = expand(r["parts"], {r["key"]})
                r["kind"] = "compound"           # the Deriver's word for anything built from parts
                ranks = [by[k]["rank"] for k in re.findall(r"\{([^}]+)\}", r["parts"]) if k in by]
                r["rank"] = max([r["rank"]] + ranks)
        return rows

    # ---------- the build ----------
    def build(self):
        rows = self._normalize(self.meanings())
        prev = {}
        if (self.out / "lexicon.csv").exists():
            prev = {r["key"]: r for r in csv.DictReader(open(self.out / "lexicon.csv", newline=""))}
        prefix = self.cfg.get("id_prefix", "W")
        next_id = max([int(r["id"][len(prefix):]) for r in prev.values() if r["id"][len(prefix):].isdigit()] + [0]) + 1
        for r in rows:
            r["era"] = r.get("era") or self.era(r["rank"])
            r.setdefault("register", "everyday")
            if r["key"] in prev:
                r["id"] = prev[r["key"]]["id"]
                if r["kind"] == "root" and not r.get("proto") and prev[r["key"]]["proto"]:
                    r["proto"], r["status"] = prev[r["key"]]["proto"], prev[r["key"]]["status"]
            else:
                r["id"], next_id = f"{prefix}{next_id:05d}", next_id + 1

        # indices of everything accepted: forms in every branch, readings, protos
        taken = {b: {} for b in self.branches}
        heard, protos = {}, {}
        accepted = []

        def forms_of(proto):
            f = {b: self.pack.laws.apply(proto, b) for b in self.branches}
            f[self.std] = self.ortho(f[self.std])
            return f

        def clean(proto, f):
            if proto in protos or proto in self.reserved:
                return False
            if not self.pack.phonotactics.check(proto)[0]:
                return False
            for b, w in f.items():
                if not w or w in taken[b] or "''" in w or TRIPLE.search(w) or w in self.block or w in self.reserved:
                    return False
            return self.reading(f[self.std]) not in heard

        def accept(r, f):
            protos[r["proto"]] = r["key"]
            for b, w in f.items():
                if w:
                    taken[b].setdefault(w, r["key"])
            heard.setdefault(self.reading(f[self.std]), r["key"])

        def release(r):
            for b in self.branches:
                if taken[b].get(r[b]) == r["key"]:
                    del taken[b][r[b]]
            if heard.get(r["reading"]) == r["key"]:
                del heard[r["reading"]]
            self.reserved.add(r["proto"])          # this form is spent for this build
            protos.pop(r["proto"], None)

        def generate(r, salt=""):
            rng = random.Random(int(hashlib.sha256((r["key"] + salt).encode()).hexdigest()[:12], 16))
            for attempt in range(1, 3001):
                cand = self.gen.candidate(rng, r["pos"], r["field"])
                f = forms_of(cand)
                if clean(cand, f):
                    r["proto"], r["status"] = cand, "generated"
                    accept(r, f)
                    log["tries"] += attempt
                    return
            r["proto"], r["notes"] = "", "generator found no clean form"
            log["failed"] += 1

        roots = [r for r in rows if r["kind"] not in ("compound", "loan")]
        fixed = [r for r in roots if r.get("proto")]
        new = sorted((r for r in roots if not r.get("proto")), key=lambda r: (r["rank"], -int(r.get("lists", 0)), r["key"]))
        log = Counter()
        for r in fixed:
            accept(r, forms_of(r["proto"]))
        for r in new:
            generate(r)
        for r in roots:
            r.setdefault("status", "fixed" if r.get("proto") else "missing")

        # a built word can land on a root's form; then the newly generated root steps aside and is regenerated
        new_keys = {r["key"] for r in new}
        for round_ in range(1, 26):
            d = self.derive_all(rows)
            movers = self.clashes(rows, new_keys)
            if not movers:
                break
            for r in movers:
                r["reading"] = self.reading(r[self.std]) if r[self.std] else ""
                release(r)
                generate(r, salt=f"#{round_}")
                log["regenerated"] += 1
        errors, warnings = self.check(rows, d)
        rows.sort(key=lambda r: r["id"])
        retired = sorted(set(prev) - {r["key"] for r in rows})
        self.write(rows, errors, warnings, log, retired)
        return rows, errors, warnings

    def derive_all(self, rows):
        d = Deriver(self.pack.laws, self.pack.meta["derivation"], self.ortho)
        d.index(rows)
        for r in rows:
            r.update(d.derive(r))
            r["reading"] = self.reading(r[self.std]) if r[self.std] else ""
            if r["kind"] == "compound":
                r["status"] = "built"
        return d

    def clashes(self, rows, new_keys):
        """Roots generated in this build that share a spelling or a sound with another meaning."""
        groups = {}
        for r in rows:
            for b in self.branches:
                if r[b]:
                    groups.setdefault((b, r[b]), []).append(r)
            if r["reading"]:
                groups.setdefault(("heard", r["reading"]), []).append(r)
        movers = {}
        for members in groups.values():
            if len(members) > 1:
                for r in sorted(members, key=lambda r: r["id"], reverse=True):
                    if r["kind"] not in ("compound", "loan") and r["key"] in new_keys and r.get("status") == "generated":
                        movers[r["key"]] = r
                        break
        return list(movers.values())

    def check(self, rows, deriver):
        errs, warns = [], []
        rank = {r["key"]: r["rank"] for r in rows}
        seen = {"proto": {}, "meaning": {}, "heard": {}, **{b: {} for b in self.branches}}
        for r in rows:
            rid, kind = r["id"], r["kind"]
            if kind not in ("compound", "loan"):
                p = r.get("proto", "")
                if not p:
                    errs.append((rid, "E1", f"{r['key']}: no root form"))
                elif r.get("status") == "generated" and not self.pack.phonotactics.check(p)[0]:
                    errs.append((rid, "E1", f"*{p}: {self.pack.phonotactics.check(p)[1]}"))
                if p and p in seen["proto"]:
                    errs.append((rid, "E2", f"*{p} already used by {seen['proto'][p]}"))
                seen["proto"].setdefault(p, rid)
                if r.get("status") == "generated" and (r[self.std] in self.reserved):
                    errs.append((rid, "E7", f"'{r[self.std]}' is reserved"))
                if r.get("status") == "generated" and any(r[b] in self.block for b in self.branches if r[b]):
                    warns.append((rid, "W1", f"'{r[self.std]}' is on the blocklist"))
            else:
                for k in re.findall(r"\{([^}]+)\}", r.get("parts", "")):
                    if rank.get(k, 0) > r["rank"]:
                        errs.append((rid, "E11", f"dated rank {r['rank']} but part '{k}' is rank {rank[k]}"))
            if deriver.unresolved({b: r[b] for b in self.branches}):
                errs.append((rid, "E9", f"'{r['parts']}' names a meaning with no form"))
            for b in self.branches:
                w = r[b]
                if not w:
                    continue
                if TRIPLE.search(w):
                    errs.append((rid, "E8", f"{b} '{w}' has a letter three times in a row"))
                if "''" in w:
                    errs.append((rid, "E10", f"{b} '{w}' has a doubled apostrophe"))
                if w in seen[b]:
                    errs.append((rid, "E3", f"{b} '{w}' already means '{seen[b][w][1]}' ({seen[b][w][0]})"))
                seen[b].setdefault(w, (rid, r["gloss"]))
                want = r.get(f"attested_{b}")
                if want and w != want and not r.get("exception"):
                    errs.append((rid, "E6", f"{b} law gives '{w}', attested '{want}'"))
            if r["reading"]:
                if r["reading"] in seen["heard"] and seen["heard"][r["reading"]] != r[self.std]:
                    errs.append((rid, "E4", f"'{r[self.std]}' sounds the same as '{seen['heard'][r['reading']]}'"))
                seen["heard"].setdefault(r["reading"], r[self.std])
            m = (r["gloss"].lower().strip(), r["pos"], r.get("register", ""))
            if m in seen["meaning"]:
                errs.append((rid, "E5", f"meaning '{m[0]}' ({m[1]}) already listed as {seen['meaning'][m]}"))
            seen["meaning"].setdefault(m, rid)
        return errs, warns

    # ---------- output ----------
    def write(self, rows, errors, warnings, log, retired):
        self.out.mkdir(parents=True, exist_ok=True)
        att = [f"attested_{b}" for b in self.branches]
        fields = ["id", "key", "cid", "proto", *self.branches, "reading", "gloss", "pos", "field", "kind", "era",
                  "register", "parts", *att, "source", "status", "exception", "notes"]
        with open(self.out / "lexicon.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        name, std = self.pack.meta.get("language", self.pack.name), self.std
        kinds = Counter(r["kind"] for r in rows)
        lines = [f"# {name}: dictionary check", "",
                 f"{len(rows)} entries ({kinds['root']} roots, {kinds['compound']} built from older words). "
                 f"{len(errors)} errors, {len(warnings)} warnings.",
                 f"Generator: {log['tries']} candidates for {len([r for r in rows if r.get('status') == 'generated'])} "
                 f"new roots; {log['failed']} meanings found no clean form.", ""]
        for title, items in (("Errors", errors), ("Warnings", warnings)):
            lines.append(f"## {title}")
            lines += [f"- {i} {c}: {m}" for i, c, m in items] or ["- none"]
            lines.append("")
        if retired:
            lines += ["## Retired since the last build", *[f"- {k}" for k in retired], ""]
        (self.out / "check_report.md").write_text("\n".join(lines))

        write_dictionaries(rows, std, name, self.out)
        (self.out / "stats.json").write_text(json.dumps({
            "entries": len(rows), "roots": kinds["root"], "built": kinds["compound"], "errors": len(errors),
            "warnings": len(warnings), "by_era": Counter(r["era"] for r in rows),
            "by_pos": Counter(r["pos"] for r in rows)}, indent=2))


def write_dictionaries(rows, std, name, out):
    """dictionary.md (word to meaning) and english.md (meaning to word): knowledge files for people and models."""
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)

    def line(r, by_word):
        a, b = (r[std], r["gloss"]) if by_word else (r["gloss"], r[std])
        return f"| {a} | {b} | {r['pos']} | {r.get('era', '')} | {r.get('parts') or ''} |"
    head = "| {} | {} | Part of speech | Era | Built from |\n|---|---|---|---|---|"
    words = [r for r in rows if r.get(std)]
    (out / "dictionary.md").write_text(
        f"# {name} to English\n\nGenerated by the UTP from lexicon.csv. Do not edit: change the source and rebuild.\n\n"
        + head.format("Word", "Meaning") + "\n" + "\n".join(line(r, True) for r in sorted(words, key=lambda r: r[std].lower())) + "\n")
    (out / "english.md").write_text(
        f"# English to {name}\n\nEnglish glosses are labels for meanings; the words were not made from them.\n\n"
        + head.format("Meaning", "Word") + "\n" + "\n".join(line(r, False) for r in sorted(words, key=lambda r: r["gloss"].lower())) + "\n")
