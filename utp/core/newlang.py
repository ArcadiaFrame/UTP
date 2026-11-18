"""Create a new language: the folder, its settings, its data files and its launchers.

  python3 utp/utp.py new nerani --language "Nerani" --order SOV \
      --branches high,low --eras Ancient,Old,Middle,Modern \
      --consonants "p t k m n s l r w y h sh" --vowels "a e i o u"

languages/<name>/
  pack.json         every setting: branches, eras, sound shapes, grammar, speech, typology
  sound_laws.json   the proto-language's sounds and each branch's sound changes (start empty)
  meanings.csv      the language's own meanings, beyond the universal registry
  batches/          model-proposed expansions waiting for your review (utp.py expand)
  build/            the dictionary, check report and dictionaries (utp.py build)
  docs/             grammar card and guides
  lab/index.html    the language's Lab           (utp.py lab, after each build)
  course/           the language's course         (utp.py course, after each build)
  open.py           opens the UTP app on this language (python3 open.py)
  README.md, DESIGN.md
"""
import json
import pathlib
import re
import shutil

from .pack import LANGUAGES, Pack

ORDERS = {
    # clause order, noun-phrase order, how the direction/possession markers attach
    "SVO": {"clause": ["subject", "verb", "object", "goal", "adverbs", "content", "evidence", "formal"],
            "np_order": ["poss", "num", "mods", "head", "of"], "adpositions": "prepositions",
            "toward": {"key": "g-toward", "attach": "before"}, "of": {"key": "g-of", "attach": "before"},
            "object": None, "noun_phrase": {"adjective": "Adj-N", "genitive": "Gen-N", "relative_clause": "N-Rel"}},
    "SOV": {"clause": ["subject", "adverbs", "object", "goal", "content", "verb", "evidence", "formal"],
            "np_order": ["head", "mods", "num", "of", "poss"], "adpositions": "postpositions",
            "toward": {"key": "g-toward", "attach": "hyphen"}, "of": {"key": "g-of", "attach": "prefix"},
            "object": {"key": "g-object", "attach": "hyphen", "drop_if_indefinite": True},
            "noun_phrase": {"adjective": "N-Adj", "genitive": "N-Gen", "relative_clause": "N-Rel"}},
}
DEFAULT_CONSONANTS = "p t k b d g m n s z f v l r w y h sh ch"
DEFAULT_VOWELS = "a e i o u"
SLUG = re.compile(r"^[a-z][a-z0-9-]{1,30}$")


def grammar(order):
    o = ORDERS[order]
    markers = {
        "toward": o["toward"], "of": o["of"],
        "plural": {"key": "g-plural", "attach": "hyphen" if order == "SOV" else "suffix"},
        "ongoing": {"key": "g-ongoing", "attach": "hyphen" if order == "SOV" else "suffix"},
        "past": {"key": "g-past", "attach": "hyphen" if order == "SOV" else "suffix"},
        "completed": {"key": "g-completed", "attach": "prefix"},
        "honorific": {"key": "g-honorific", "attach": "hyphen" if order == "SOV" else "suffix"},
        "humble": {"key": "g-humble", "attach": "hyphen" if order == "SOV" else "suffix"},
        "adverbial": {"key": "g-adverbial", "attach": "hyphen" if order == "SOV" else "suffix"},
        "future": "g-future", "negative": "not", "never": "never", "in": "in", "comp": "g-comp", "if": "if",
        "vocative": "g-vocative", "question": "g-question", "request": "g-request", "hortative": "g-hortative",
        "modal": {"ability": "g-ability", "duty": "g-duty"}, "evidence": {},
    }
    if o["object"]:
        markers["object"] = o["object"]
    return {
        "about": f"A starting {order} grammar made by utp.py new. Change anything; the interlingua follows it.",
        "clause": o["clause"], "np_order": o["np_order"], "front_aux_in_questions": False,
        "pronouns": {"1sg": "i", "2sg": "you", "3sg": "he-or-she", "1pl": "we", "3pl": "they"},
        "possessives": {"1sg": "my"},
        "wh": {"what": "what", "who": "who", "where": "where", "when": "when", "why": "why", "how": "how",
               "how-many": "how-many"},
        "markers": markers,
    }


def create(name, language=None, order="SOV", branches=("standard",), eras=("Ancient", "Old", "Middle", "Modern"),
           consonants=DEFAULT_CONSONANTS, vowels=DEFAULT_VOWELS, about="", where=None, force=False):
    if not SLUG.match(name):
        raise ValueError("name: lower-case letters, digits and hyphens, starting with a letter")
    order = order.upper()
    if order not in ORDERS:
        raise ValueError(f"word order: one of {', '.join(ORDERS)}")
    base = pathlib.Path(where) if where else LANGUAGES
    home = base / name
    if home.exists() and any(home.iterdir()) and not force:
        raise FileExistsError(f"{home} already exists")
    language = language or name.replace("-", " ").title()
    branches = [b.strip().lower() for b in branches if b.strip()]
    std = branches[0]
    cons = consonants.split()
    vows = vowels.split()
    long_vowels = [v * 2 for v in vows if len(v) == 1][:3]
    units = sorted(set(cons + vows + long_vowels), key=lambda u: (-len(u), u))
    stops = [c for c in cons if c in ("p", "t", "k", "b", "d", "g")]
    liquids = [c for c in cons if c in ("l", "r")]
    clusters = [s + l for s in stops for l in liquids][:10] + [f"s{c}" for c in ("p", "t", "k", "m", "n", "l") if c in cons and "s" in cons]
    finals = [c for c in cons if c not in ("h", "w", "y", "b", "d", "g", "z", "v", "ch")]
    harsh = [c for c in cons if c in ("k", "t", "g", "d", "ch", "kh", "q", "x", "r")]
    soft = [c for c in cons if c in ("l", "m", "n", "w", "y", "h", "s", "v", "sh")]
    link = next((c for c in ("h", "y", "w") if c in cons), cons[0])     # breaks up three like vowels at a join
    prefix = re.sub(r"[^A-Z]", "", name[:2].upper()) or "L"

    pack = {
        "name": f"{language} language family",
        "language": language,
        "format": "utp-pack/1",
        "about": about or f"{language}: a UTP language created with utp.py new.",
        "root": ".",
        "home": ".",
        "files": {"sound_laws": "sound_laws.json", "lexicon": "build/lexicon.csv"},
        "derivation": {"branches": branches, "standard": std, "kinds": {"compound": "compound", "loan": "loan"},
                       "loan_branch": std, "coined_in_branch": {},
                       "join_rules": [
                           {"pattern": "([aeiou])\\1\\+(?=\\1)", "replace": f"\\1\\1+{link}",
                            "note": f"a long vowel meeting a like vowel at a fused join takes a linking {link}"},
                           {"pattern": "([aeiou])\\+(?=\\1\\1)", "replace": f"\\1+{link}",
                            "note": f"a vowel meeting a like long vowel at a fused join takes a linking {link}"}]},
        "phonotactics": {"transparent": [], "no_initial": [], "max_medial_cluster": 2, "final_cluster": False},
        "eras": [{"id": e.strip(), "rank": i} for i, e in enumerate(eras) if e.strip()],
        "generator": {
            "shapes": {
                "noun": [["CVC", 30], ["CVCV", 25], ["CVCVC", 25], ["CCVC", 8], ["CVCCV", 7], ["VCVC", 5]],
                "verb": [["CVC", 35], ["CVCV", 30], ["CVCVC", 20], ["CCVC", 8], ["VCV", 7]],
                "adjective": [["CVCV", 30], ["CVC", 25], ["CVCVC", 25], ["VCVC", 10], ["CCVCV", 10]],
                "short": [["CV", 40], ["VC", 20], ["CVC", 40]]},
            "harsh": harsh, "soft": soft,
            "field_tone": {"warfare-and-hunting": "harsh", "emotions-and-values": "soft", "kinship": "soft"}},
        "build": {"out": "build", "id_prefix": prefix,
                  "registry": {"tiers": [1, 2, 3], "exclude_pos": ["classifier"], "templates": "all"},
                  "meanings": "meanings.csv", "compound_head": "last", "compound_join": "-", "affix_join": "+",
                  "affix_position": {"negative": "prefix"},
                  "blocklist": "../../utp/concepts/english_labels.txt", "reserved": []},
        "speech": {"voice": "am_michael", "from": "spelling",
                   "sounds": {"sh": "ʃ", "ch": "ʧ", "aa": "aː", "ee": "eː", "ii": "iː", "y": "j", "r": "ɾ"},
                   "stress": "first"},
        "grammar": {std: grammar(order)},
        "typology": {std: {"word_order": order, "noun_phrase": ORDERS[order]["noun_phrase"],
                           "adpositions": ORDERS[order]["adpositions"], "alignment": "nominative-accusative",
                           "morphology": {"type": "agglutinative", "affixes": "suffixing; negative is a prefix"},
                           "prosody": {"tone": "none", "stress": "first syllable"}}},
        "learning": {"lab": "lab/index.html", "course": "course/index.html"},
        "open_questions": [
            {"id": "Q1", "question": "What are the speakers like, and what do they talk about most?",
             "proposal": "Write it in DESIGN.md; the expansion prompts read it."},
            {"id": "Q2", "question": "What sound changes split the branches?",
             "proposal": "Add rules to sound_laws.json, then rebuild."}],
    }
    laws = {
        "proto": {"about": f"Proto-{language}.", "units": units, "vowels": vows + long_vowels,
                  "onset_clusters": clusters, "finals": finals},
        "branches": {b: {"label": f"{language}" if b == std else f"{b.title()} {language}", "rules": []}
                     for b in branches},
        "tests": [],
    }
    for d in ("batches", "build", "docs", "lab", "course"):
        (home / d).mkdir(parents=True, exist_ok=True)
    (home / "batches" / ".gitkeep").write_text("")
    (home / "pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n")
    (home / "sound_laws.json").write_text(json.dumps(laws, indent=2, ensure_ascii=False) + "\n")
    (home / "meanings.csv").write_text("key,gloss,pos,field,era,kind,parts,notes\n")
    (home / "DESIGN.md").write_text(DESIGN.format(language=language, order=order, eras=", ".join(eras),
                                                  branches=", ".join(branches)))
    (home / "README.md").write_text(README.format(language=language, name=name))
    shutil.copy(pathlib.Path(__file__).resolve().parent.parent / "app" / "open_template.py", home / "open.py")
    return home


def first_build(home):
    """Build the dictionary, then the Lab, course and grammar card, so a new language opens complete."""
    from .builder import Builder
    from . import learn
    from .llm import grammar_card
    p = Pack(home)
    rows, errors, warnings = Builder(p).build()
    p = Pack(home)
    (home / "docs" / "grammar-card.md").write_text(grammar_card(p))
    learn.build_all(p)
    return rows, errors, warnings


DESIGN = """# {language}: design notes

The expansion prompts read this file, so what you write here shapes every word a model proposes.

- **Word order:** {order}
- **Branches:** {branches}
- **Eras:** {eras}

## Who speaks it

(Their world, their history, what they value, what they talk about every day. A desert people names
water a hundred ways; a seafaring people names the wind.)

## Sound and feel

(Harsh or soft, short or long words, what it should sound like to an outsider.)

## Rules the words must follow

(Anything a model must respect: taboo sounds, honorifics, metaphors the culture uses, metaphors it never uses.)

## Decisions log

| Date | Decision |
|---|---|
"""

README = """# {language}

Made with the UTP. Every file below is generated from `pack.json`, `sound_laws.json` and `meanings.csv`.

| Do this | Command (from the repository's top folder) |
|---|---|
| Open the app on this language | `python3 languages/{name}/open.py` |
| Rebuild the dictionary, Lab and course | `python3 utp/utp.py build {name}` |
| Ask a model for a batch of new words on a topic | `python3 utp/utp.py expand {name} "kinship and the household" --n 40` |
| Approve a batch (mark `approve` = yes in the CSV), then | `python3 utp/utp.py apply {name} languages/{name}/batches/<file>.csv` |
| Ask a model for course sentences | `python3 utp/utp.py sentences {name} "greetings" --n 12` |
| Grammar card for any chat model | `python3 utp/utp.py card {name}` |

Files: `build/dictionary.md` and `build/english.md` (the dictionaries), `build/check_report.md`,
`docs/grammar-card.md`, `lab/index.html` (open in any browser; the tutor needs the app),
`course/index.html`, `batches/` (proposals waiting for review).

Design notes that every model prompt reads: `DESIGN.md`.
"""
