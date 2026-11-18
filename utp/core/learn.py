"""Each language's Lab and course, generated into the language's own folder.

  lab/index.html      dictionary, word builder, glosser, sentence builder, tutor, expansion review
  course/index.html   spaced-repetition course: word units by topic, then sentence units
                      (course/sentences.json, written by utp.py sentences)

Both pages carry their data inside, so they open from the file in any browser with no
internet. The tools that need the engine or a model (word builder, glosser, tutor,
expansion) light up when the page is opened through the UTP app (utp/app/server.py),
which serves it on this machine.
"""
import datetime
import hashlib
import json
import pathlib
import re

from .speech import phonemes

APP = pathlib.Path(__file__).resolve().parent.parent / "app"
SKIP_FIELDS = {"grammar"}


def _rank(pack):
    return {e["id"]: e["rank"] for e in pack.meta.get("eras", [])}


def _std(pack):
    return pack.meta["derivation"]["standard"]


def entries(pack, rows=None):
    rows = rows if rows is not None else pack.rows()
    br = pack.meta["derivation"]["branches"]
    out = []
    for r in rows:
        forms = {b: r.get(b, "") for b in br}
        if not any(forms.values()):
            continue
        out.append({"k": r["key"], "id": r.get("id", ""), "f": forms, "g": r.get("gloss", ""), "p": r.get("pos", ""),
                    "fd": r.get("field", ""), "e": r.get("era", ""), "kind": r.get("kind", ""),
                    "parts": r.get("parts", ""), "r": r.get("reading", "") or r.get("ipa", ""),
                    "rg": r.get("register", ""), "n": (r.get("notes", "") or "")[:300]})
    return out


def _json_for_html(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build_lab(pack, rows=None):
    from .llm import grammar_card
    out = pack.learning("utp_lab") or pack.learning("lab") or (pack.home / "lab" / "index.html")
    if not pack.buildable and pack.learning("utp_lab"):
        out = pack.learning("utp_lab")
    rows = rows if rows is not None else pack.rows()
    data = {
        "id": pack.id, "language": pack.meta.get("language", pack.name), "std": _std(pack),
        "branches": pack.meta["derivation"]["branches"],
        "labels": {b: pack.laws.data["branches"].get(b, {}).get("label", b) for b in pack.laws.branches},
        "eras": pack.meta.get("eras", []), "entries": entries(pack, rows), "card": grammar_card(pack),
        "laws": {b: [{"id": x.get("id", ""), "note": x.get("note", ""), "era": x.get("era", "")}
                     for x in pack.laws.data["branches"].get(b, {}).get("rules", [])] for b in pack.laws.branches},
        "proto": {"units": pack.laws.proto.get("units", []), "vowels": pack.laws.proto.get("vowels", [])},
        "buildable": pack.buildable, "built": datetime.date.today().strftime("%d %b %Y"),
    }
    page = (APP / "lab.template.html").read_text().replace("__TITLE__", f"{data['language']} Lab").replace(
        "__DATA__", _json_for_html(data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    return out


def _reading(pack, text):
    out = []
    for tok in re.findall(r"[^\s.,?!:;]+", text):
        ipa = phonemes(pack, tok)[0].replace("ˈ", "") if tok[:1].islower() else ""
        out.append({"w": tok, "parts": [{"s": tok, "st": False, "join": ""}], "ipa": ipa, "f": []})
    return out


def _item(pack, v, en):
    v = v[:1].upper() + v[1:] if re.search(r"[.?!]$", v) else v
    k = "s" if re.search(r"[.?!]$", v) else ("p" if " " in v else "w")
    return {"id": hashlib.sha1((pack.id + v + en).encode()).hexdigest()[:8], "v": v, "en": en, "k": k,
            "read": _reading(pack, v), "gaps": [], "tiles": re.sub(r"[.?!,:;]", "", v).split()}


def course_data(pack, rows=None, per_unit=6, max_units=40):
    rows = rows if rows is not None else pack.rows()
    std, rank = _std(pack), _rank(pack)
    words = [r for r in rows if r.get(std) and r.get("field") not in SKIP_FIELDS and r.get("pos") not in ("suffix", "prefix")]
    words.sort(key=lambda r: (rank.get(r.get("era"), 9), r.get("kind") != "root", r.get("id", "")))
    by_field = {}
    for r in words:
        by_field.setdefault(r.get("field") or "other", []).append(r)
    units = []
    # interleave fields so the first units cover the most basic words of every topic
    queues = sorted(by_field.items(), key=lambda kv: -len(kv[1]))
    seen = set()
    while len(units) < max_units and any(q for _, q in queues):
        for field, q in queues:
            chunk = [r for r in q[:per_unit] if r[std] not in seen]
            del q[:per_unit]
            if len(chunk) < 3 or len(units) >= max_units:
                continue
            seen |= {r[std] for r in chunk}
            n = sum(1 for u in units if u["field"] == field) + 1
            units.append({"id": f"w-{field}-{n}", "title": field.replace("-", " ").capitalize() + (f" {n}" if n > 1 else ""),
                          "field": field, "from": "Words: " + field.replace("-", " "), "level": "foundations",
                          "tip": "Each word comes back for review just before you would forget it.",
                          "items": [_item(pack, r[std], r["gloss"]) for r in chunk], "errors": []})
    sentences_path = pack.home / "course" / "sentences.json"
    sentences = json.loads(sentences_path.read_text()) if sentences_path.exists() else []
    by_topic = {}
    for s in sentences:
        by_topic.setdefault(s.get("topic", "sentences"), []).append(s)
    for topic, ss in by_topic.items():
        for i in range(0, len(ss), per_unit):
            chunk = ss[i:i + per_unit]
            units.append({"id": f"s-{re.sub(r'[^a-z0-9]+', '-', topic.lower())}-{i // per_unit + 1}",
                          "title": topic.capitalize() + (f" {i // per_unit + 1}" if len(ss) > per_unit else ""),
                          "from": "Sentences: " + topic, "level": "conversation",
                          "tip": "Every sentence was rendered by the language's own grammar from a meaning frame.",
                          "items": [_item(pack, s["v"], s["en"]) for s in chunk], "errors": []})
    for u in units:
        u.pop("field", None)
    return {"levels": [{"id": "foundations", "title": "Words", "about": "The core vocabulary, oldest and most basic first."},
                       {"id": "conversation", "title": "Sentences",
                        "about": "Sentences made with utp.py sentences or the Lab's Sentences tab."}],
            "units": units, "stories": [], "built": datetime.date.today().strftime("%d %b %Y"), "lexiconSize": len(rows)}


def build_course(pack, rows=None):
    out = pack.learning("course") or (pack.home / "course" / "index.html")
    if not pack.buildable:
        return None                               # Vulcan has its own course (vulcan-conlang/tools/build_course.py)
    data = course_data(pack, rows)
    lang = pack.meta.get("language", pack.name)
    page = (APP / "course.template.html").read_text().replace("__TITLE__", f"{lang} Course").replace(
        "__STORE__", f"utp-course-{pack.id}-v1").replace("__DATA__", _json_for_html(data))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    return out


def build_all(pack, rows=None):
    rows = rows if rows is not None else pack.rows()
    return [p for p in (build_lab(pack, rows), build_course(pack, rows)) if p]
