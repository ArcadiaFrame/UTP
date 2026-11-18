"""UTP and language models: optional, local-first, never trusted unchecked.

The UTP builds whole languages with no language model at all. A model helps in
three places, and in each one the UTP checks every answer before it is used:

  context()   the dictionary entries and grammar card a model needs for a request,
              so it looks words up instead of inventing them (paste into any chat,
              or send with ask())
  propose()   suggest how later meanings could be built from older ones (as the Vulcan
              build did by hand with Latin and Japanese cross-checks); every proposal
              must name only existing, older meanings or it is rejected
  curate()    flag template-made meanings that make no sense (one who: rain); nothing
              is removed until you approve the list

Model connection: utp/core/models.py (Anthropic, OpenAI-compatible servers, Ollama).
"""
import csv
import json
import pathlib
import re

from .models import Model, ModelError  # noqa: F401

INSTRUCTIONS = pathlib.Path(__file__).resolve().parent.parent / "LLM-INSTRUCTIONS.md"
LLM = Model          # the name the older tools use


def section(name):
    """One section of LLM-INSTRUCTIONS.md, by its heading."""
    text = INSTRUCTIONS.read_text()
    m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def grammar_card(pack):
    lines = [f"# {pack.meta.get('language', pack.name)}: grammar card", ""]
    for branch, prof in pack.typology.items():
        lines.append(f"## {branch}")
        for k, v in prof.items():
            if k != "source":
                lines.append(f"- {k.replace('_', ' ')}: {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v}")
        lines.append("")
    return "\n".join(lines)


STOP = set("a an the of to in on at by for with from and or but is are was were be been am do does did i you he "
           "she it we they me him her us them my your his its our their this that these those how what who say "
           "said tell please can could would will shall should not no yes so as if".split())
IRREGULAR = {"came": "come", "went": "go", "saw": "see", "seen": "see", "said": "say", "gave": "give", "given": "give",
             "took": "take", "ate": "eat", "ran": "run", "knew": "know", "told": "tell", "thought": "think",
             "found": "find", "made": "make", "brought": "bring", "taught": "teach", "spoke": "speak", "wrote": "write",
             "children": "child", "men": "man", "women": "woman", "feet": "foot", "teeth": "tooth", "felt": "feel"}


def _lemmas(w):
    out = {w, IRREGULAR.get(w, w)}
    for end, add in (("ies", "y"), ("es", ""), ("s", ""), ("ied", "y"), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e")):
        if w.endswith(end) and len(w) - len(end) >= 3:
            out.add(w[: -len(end)] + add)
    return out


def lookup(rows, text, std, limit=40):
    """Dictionary rows a request needs: by form (conlang text) and by meaning (English text)."""
    tokens = [w.lower().strip("'") for w in re.findall(r"[A-Za-z'\-]+", text)]
    forms = set(tokens)
    content = set().union(*[_lemmas(w) for w in tokens if w not in STOP]) if tokens else set()
    scored = []
    for r in rows:
        form = r.get(std, "").lower()
        head = re.split(r"[,;(:]", r["gloss"].lower())[0].strip()
        head_words = set(re.findall(r"[a-z']+", head)) - STOP
        score = 0
        if form and (form in forms or form.split("-")[0] in forms):
            score = 4
        elif head in content:
            score = 3
        elif head_words and head_words <= content:
            score = 2
        elif head_words & content and len(head_words) <= 2:
            score = 1
        if score:
            scored.append((-score, r.get("kind") == "compound", len(r["gloss"]), r["key"], r))
    scored.sort(key=lambda x: x[:4])
    return [x[4] for x in scored[:limit]]


def context(pack, text, rows=None, limit=40):
    std = pack.meta["derivation"]["standard"]
    rows = rows or pack.rows()
    hits = lookup(rows, text, std, limit)
    table = "\n".join(f"| {r[std]} | {r['gloss']} | {r['pos']} | {r.get('era', '')} | {r.get('parts', '')} |"
                      for r in hits if r[std])
    return (grammar_card(pack) + "\n## Dictionary entries for this request\n\n| Word | Meaning | Part of speech | Era | Built from |\n"
            "|---|---|---|---|---|\n" + table + "\n")


# ---------- propose: derivations for later meanings ----------
def propose(pack, rows, llm, limit=40, batch=20, out=None):
    """Ask the model how tier-3 root meanings could be built from older meanings; keep only valid answers."""
    std = pack.meta["derivation"]["standard"]
    era_rank = {e["id"]: e["rank"] for e in pack.meta.get("eras", [])}
    rank = {r["key"]: era_rank.get(r.get("era"), 0) for r in rows}
    roots = [r for r in rows if r.get("kind") == "root" and r.get("status") == "generated" and rank[r["key"]] >= 2
             and r.get("field") != "grammar"][:limit]
    older = [r for r in rows if r.get("kind") == "root" and rank[r["key"]] <= 1]
    vocab = ", ".join(f"{r['key']}={r['gloss']}" for r in older[:1500])
    accepted, rejected = [], []
    for i in range(0, len(roots), batch):
        chunk = roots[i:i + batch]
        ask = "\n".join(f"- {r['key']}: {r['gloss']} ({r['pos']})" for r in chunk)
        msg = [{"role": "system", "content": section("Builder: proposing derivations")},
               {"role": "user", "content": f"Older meanings (key=gloss): {vocab}\n\nMeanings to build:\n{ask}\n\n"
                                           "Answer in JSON: {\"proposals\": [{\"key\": ..., \"parts\": \"{a}-{b}\", \"basis\": ...}]}"}]
        try:
            answer = llm.chat_json(msg).get("proposals", [])
        except Exception as e:                      # a model that will not answer in JSON: skip the batch
            rejected.append({"key": "(batch)", "parts": "", "basis": "", "why": f"no JSON: {e}"})
            continue
        asked = {r["key"]: r for r in chunk}
        for p in answer:
            k, parts = p.get("key", ""), p.get("parts", "")
            names = re.findall(r"\{([^}]+)\}", parts)
            why = ("not asked" if k not in asked else "no parts" if not names else
                   "unknown meaning: " + ", ".join(n for n in names if n not in rank) if any(n not in rank for n in names) else
                   "names itself" if k in names else
                   "part is not older" if any(rank[n] > rank[k] for n in names) else
                   "bad joiners" if re.sub(r"\{[^}]+\}", "", parts).strip(" +-") else "")
            (rejected if why else accepted).append({"key": k, "gloss": asked.get(k, {}).get("gloss", ""),
                                                    "parts": parts, "basis": p.get("basis", ""), "why": why})
    if out:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["key", "gloss", "parts", "basis", "why", "approve"])
            w.writeheader()
            w.writerows([dict(a, approve="") for a in accepted] + [dict(r, approve="no") for r in rejected])
    return accepted, rejected


# ---------- curate: template meanings that make no sense ----------
def curate(pack, rows, llm, limit=200, batch=50, out=None):
    made = [r for r in rows if str(r.get("source", "")).startswith("template")][:limit]
    flags = []
    for i in range(0, len(made), batch):
        chunk = made[i:i + batch]
        ask = "\n".join(f"- {r['key']}: {r['gloss']}" for r in chunk)
        msg = [{"role": "system", "content": section("Builder: curating template meanings")},
               {"role": "user", "content": f"{ask}\n\nAnswer in JSON: {{\"drop\": [{{\"key\": ..., \"why\": ...}}]}}"}]
        try:
            answer = llm.chat_json(msg).get("drop", [])
        except Exception:
            continue
        keys = {r["key"] for r in chunk}
        flags += [d for d in answer if d.get("key") in keys]
    if out:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["key", "why", "approve"])
            w.writeheader()
            w.writerows([{"key": d["key"], "why": d.get("why", ""), "approve": ""} for d in flags])
    return flags
