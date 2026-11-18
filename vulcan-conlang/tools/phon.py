"""Shared phonology helpers: provisional sound segmentation and the spelling standard.

segment(word)     -> list of IPA-ish segments read from an English-style spelling
standardize(form) -> the form in the project's standard romanization
Both the analysis script and the Lab build use this file, so they always agree.
"""
import re

# English-spelling digraphs, longest first. 'ah', 'eh', 'oh' are plain vowels
# (the h is an English spelling habit); 'uh' is schwa; doubled vowels are long.
MULTI = [
    ("tch", "tʃ"), ("dzh", "dʒ"), ("zh", "ʒ"), ("sh", "ʃ"), ("kh", "x"),
    ("th", "θ"), ("dh", "ð"), ("ch", "tʃ"), ("dz", "dz"), ("lh", "ɬ"),
    ("hw", "ʍ"), ("ph", "f"), ("ng", "ŋ"), ("ck", "k"),
    ("oo", "uː"), ("ee", "iː"), ("aa", "aː"), ("ai", "ai"), ("au", "au"),
    ("ei", "ei"), ("ae", "ae"), ("oy", "oi"), ("oi", "oi"),
    ("ah", "a"), ("uh", "ə"), ("eh", "e"), ("oh", "o"),
]
SINGLE = {"a": "a", "e": "e", "i": "i", "o": "o", "u": "u", "y": "j",
          "'": "ʔ", "c": "k", "q": "q", "x": "ks", "j": "dʒ"}
VOWELS = {"ɨ", "a", "e", "i", "o", "u", "uː", "iː", "aː", "ai", "au", "ei", "ae", "oi", "ə"}
LONG = {"uː", "iː", "aː", "ai", "au", "ei", "ae", "oi"}
FRIC = {"x", "ʃ", "ʒ", "θ", "ð", "s", "z", "f", "v", "h", "ɬ"}
ENGLISH = {"spock", "spohkh", "saavik", "michael", "tucker"}


def words(form):
    text = re.sub(r"[^a-z' ]", " ", form.lower().replace("-", " ").replace("...", " "))
    return [w.strip("'") for w in text.split() if w.strip("'")]


def segment(word):
    segs, i = [], 0
    while i < len(word):
        for src, dst in MULTI:
            if word.startswith(src, i):
                # vowel + h before another vowel is a real h: 'sehaik' = se-ha-ik
                if src in ("ah", "eh", "oh", "uh") and i + 2 < len(word) and word[i + 2] in "aeiou":
                    continue
                segs.append(dst)
                i += len(src)
                break
        else:
            ch = word[i]
            if ch == "y":
                prev_v = i > 0 and word[i - 1] in "aeiou"
                next_v = i + 1 < len(word) and word[i + 1] in "aeiou"
                segs.append("j" if prev_v or next_v else "ɨ")   # t'hy'la: y as a vowel
            else:
                segs.append(SINGLE.get(ch, ch))
            i += 1
    out = []
    for s in segs:
        if out and s == out[-1] and s not in VOWELS:
            out[-1] = s + "ː"
        else:
            out.append(s)
    return out


def ipa(form):
    """IPA-style reading of the standardized form; hyphenated members stay separate."""
    return " ".join("".join(segment(w)) for w in words(standardize(form)) if w not in ENGLISH)


# Hyphens kept only between attested meaningful pieces (compound members).
KEEP = {("koon", "ut"), ("ut", "kal"), ("fal", "tor"), ("tor", "pan"), ("tor", "voh"),
        ("dif", "tor"), ("tal", "shaya"), ("tal", "shanar"), ("ihk", "banut"),
        ("ish", "veh"), ("tor", "ut"), ("terau", "kashkau"), ("kashkau", "veh"),
        ("veh", "shetau"), ("saavik", "kam"), ("kal", "toh"), ("pa", "nar")}
NAME_NATIVE = {"Spock": "Spokh", "Spohkh": "Spokh"}


def _std_word(w):
    if w in NAME_NATIVE:
        return NAME_NATIVE[w]
    pieces = w.split("-")
    out = pieces[0]
    for prev, nxt in zip(pieces, pieces[1:]):
        if (prev.lower(), nxt.lower()) in KEEP:
            out += "-" + nxt
        elif out and nxt and out[-1].lower() == nxt[0].lower() and out[-1].lower() not in "aeiou":
            out += nxt[1:]          # kal-if-fee: the doubled f marked a syllable edge only
        else:
            out += nxt
    s = out
    s = re.sub(r"ck", "k", s)
    s = re.sub(r"(?i)ph", "f", s)
    s = re.sub(r"(?i)dzh", "j", s)
    s = re.sub(r"c(?!h)", "k", s)
    s = re.sub(r"C(?!h)", "K", s)
    s = re.sub(r"oy", "oi", s)
    s = re.sub(r"(?i)^gh", lambda m: m.group(0)[0], s)   # Ghishun: gh is just g
    s = re.sub(r"([aeo])h(?![aeiou])", r"\1", s)   # English-style ah/eh/oh before a consonant or at the end
    return s


def standardize(form, is_name=False):
    tokens = re.split(r"(\s+|\.\.\.|[.,?!])", form)
    out = []
    for t in tokens:
        if not t or not re.search(r"[A-Za-z]", t):
            out.append(t)
            continue
        out.append(NAME_NATIVE.get(t) or (t if t.lower() in ENGLISH else _std_word(t)))
    return "".join(out).strip()
