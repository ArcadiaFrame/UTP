"""Phase 1 analysis of the Vulcan corpus.

Reads corpus/canon.csv and corpus/novel.csv, segments each form into
provisional phonemes, and reports:
  - segment frequencies by maker layer
  - word shapes (CV patterns), initial and final segments
  - consonant clusters
  - recurring substrings shared by 2+ distinct entries (morpheme candidates)
Writes analysis/report.md and analysis/segments.csv.
"""
import csv, re, collections, pathlib, sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from phon import words, segment, VOWELS, LONG, FRIC, ENGLISH  # noqa: E402


def shape(segs):
    return "".join("V" if s in VOWELS else "C" for s in segs)


rows = []
for name, layer_col in (("canon.csv", "maker_layer"), ("novel.csv", "tier")):
    with open(ROOT / "corpus" / name, newline="") as f:
        for r in csv.DictReader(f):
            layer = r[layer_col] if name == "canon.csv" else "novels"
            if r.get("type") in ("name", "place"):
                layer_tag = "names"
            else:
                layer_tag = {"Scharfe/Doohan": "TMP liturgy", "Okrand": "Okrand",
                             "writers": "episode writers", "film": "film writers",
                             "fan origin (Heydt)": "episode writers"}.get(layer, layer)
            for w in words(r["form"]):
                rows.append((r["id"], layer_tag, w, segment(w)))

# Drop English names that sit inside canon sentences (ENGLISH comes from phon.py).
rows = [x for x in rows if x[2] not in ENGLISH]

with open(OUT / "segments.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["entry", "layer", "word", "segments", "shape"])
    for eid, layer, word, segs in rows:
        w.writerow([eid, layer, word, " ".join(segs), shape(segs)])

layers = sorted({r[1] for r in rows})
freq = {l: collections.Counter() for l in layers}
initial, final, clusters, shapes = (collections.Counter() for _ in range(4))
for _, layer, word, segs in rows:
    freq[layer].update(s.rstrip("ː") for s in segs)
    initial[segs[0]] += 1
    final[segs[-1]] += 1
    shapes[shape(segs)] += 1
    run = []
    for s in segs + ["a"]:
        if s in VOWELS:
            if len(run) > 1:
                clusters["".join(run)] += 1
            run = []
        else:
            run.append(s)

# Morpheme candidates: substrings of length 3+ (in spelling) that occur in
# two or more different entries, ignoring ones fully contained in a longer hit.
by_entry = collections.defaultdict(set)
for eid, _, word, _ in rows:
    for n in range(3, 7):
        for i in range(len(word) - n + 1):
            by_entry[word[i:i + n]].add(eid)
cands = {k: v for k, v in by_entry.items() if len(v) >= 2}
keep = {}
for k, v in sorted(cands.items(), key=lambda kv: -len(kv[0])):
    if any(k in big and v <= keep[big] for big in keep):
        continue
    keep[k] = v

total_words = len(rows)
lines = [f"# Phase 1 analysis\n", f"{total_words} word tokens from "
         f"{len({r[0] for r in rows})} entries.\n"]
lines.append("## Segment frequency by maker layer (share of segments, %)\n")
allsegs = sorted({s for c in freq.values() for s in c}, key=lambda s: -sum(freq[l][s] for l in layers))
lines.append("| segment | " + " | ".join(layers) + " |")
lines.append("|---|" + "---|" * len(layers))
for s in allsegs:
    cells = []
    for l in layers:
        tot = sum(freq[l].values()) or 1
        cells.append(f"{100 * freq[l][s] / tot:.1f}")
    lines.append(f"| {s} | " + " | ".join(cells) + " |")

def topn(c, n=15):
    return ", ".join(f"{k} ({v})" for k, v in c.most_common(n))

lines += ["", "## Word edges", f"- Initial: {topn(initial)}", f"- Final: {topn(final)}",
          "", "## Consonant clusters", f"- {topn(clusters, 30)}",
          "", "## Word shapes", f"- {topn(shapes, 15)}",
          "", "## Recurring substrings (2+ entries)", "| substring | entries |", "|---|---|"]
for k, v in sorted(keep.items(), key=lambda kv: (-len(kv[1]), kv[0])):
    lines.append(f"| {k} | {', '.join(sorted(v))} |")

# Vowel share and consonant share per layer, as the harshness index.
lines += ["", "## Harshness index by layer",
          "| layer | vowel share % | fricative share % | long/diphthong share of vowels % | mean word length (segments) |",
          "|---|---|---|---|---|"]
for l in layers:
    segs = [s.rstrip("ː") for _, ly, _, ss in rows if ly == l for s in ss]
    nwords = sum(1 for r in rows if r[1] == l)
    v = sum(1 for s in segs if s in VOWELS)
    fr = sum(1 for s in segs if s in FRIC)
    lg = sum(1 for s in segs if s in LONG)
    lines.append(f"| {l} | {100 * v / len(segs):.1f} | {100 * fr / len(segs):.1f} | {100 * lg / v:.1f} | {len(segs) / nwords:.1f} |")

(OUT / "report.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
