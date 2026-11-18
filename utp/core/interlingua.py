"""UTP interlingua (phase 2): language-neutral meaning frames.

A frame says what a sentence means, in no language. Each pack's grammar ("grammar"
in pack.json) renders it, and the parser reads a sentence back into a frame, so a
frame written once can be said in Vulcan, in Romulan, or in any pack with a grammar.
Meanings are dictionary keys, never words: the words come from the dictionary.

Frame
  type        statement | wh | yes-no | command | request | hortative | fragment
  subject     NP, or absent (dropped)        object   NP (definite: false drops the marker where the grammar allows)
  goal        NP (motion toward)             adverbs  [key | {"manner": key}]
  verb        key, or predicate: {"adj": key} | {"noun": NP} | {"emotion": key, "experiencer": NP}
  tense       present | past | future        aspect   simple | ongoing | completed
  modal       ability | duty                 negative true | "never"
  evidence    seen | inferred | reported | touch    noted   true (the noting particle)
  register    honorific | humble | formal    relation up | down | level (speaker to listener; rank grammars)
  wh          {"word": what|who|where|when|why|how|how-many, "role": ..., "np": NP}
  content     frame (what was said or known)  condition  frame (if ...)   vocative  NP (+ vocative_last)
  words       [key | name] for a fragment
NP
  head key | pron 1sg|2sg|3sg|1pl|2pl|3pl|2hon | name "Sorel";  mods [key];  num key;  poss 1sg..;  of NP;
  plural true;  definite false
"""
import re

DEFAULTS = {"type": "statement", "tense": "present", "aspect": "simple"}


def W(key):
    return "{%s}" % key


class Grammar:
    def __init__(self, pack, branch=None):
        allg = pack.meta.get("grammar", {})
        self.branch = branch or pack.meta["derivation"]["standard"]
        cfg, b = {}, self.branch
        chain = []
        while b:
            chain.insert(0, allg.get(b, {}))
            b = allg.get(b, {}).get("inherits")
        for c in chain:
            for k, v in c.items():
                cfg[k] = {**cfg.get(k, {}), **v} if isinstance(v, dict) and isinstance(cfg.get(k), dict) else v
        if not cfg:
            raise ValueError(f"pack has no grammar for branch '{self.branch}'")
        self.c = cfg
        self.m = cfg["markers"]
        self.pack = pack

    def key(self, role):
        v = self.m.get(role)
        return v["key"] if isinstance(v, dict) else v


def _attach(word, g, role):
    spec = g.m.get(role)
    if not spec:
        return word
    if spec.get("attach") == "before":
        return W(spec["key"]) + " " + word
    if spec.get("attach") == "after":
        return word + " " + W(spec["key"])
    if spec.get("attach") == "prefix":
        return W(spec["key"]) + word
    return word + ("-" if spec.get("attach") == "hyphen" else "") + W(spec["key"])


# ---------------- rendering ----------------
def render_np(g, n, mark=None):
    if n is None:
        return []
    if "name" in n:
        head = n["name"]
    elif "pron" in n:
        head = W(g.c["pronouns"][n["pron"]])
    else:
        head = W(n["head"])
    if n.get("plural"):
        head = _attach(head, g, "plural")
    parts = {"head": [head], "mods": [W(m) for m in n.get("mods", [])], "num": [W(n["num"])] if n.get("num") else [],
             "poss": [W(g.c["possessives"][n["poss"]])] if n.get("poss") else [],
             "of": [W(g.key("of")) + w for w in render_np(g, n["of"])[:1]] + render_np(g, n["of"])[1:] if n.get("of") else []}
    words = [w for slot in g.c["np_order"] for w in parts[slot]]
    if mark and g.m.get(mark, {}).get("attach") == "before":
        words = [W(g.m[mark]["key"])] + words           # a preposition stands before the whole phrase
    elif mark and g.m.get(mark, {}).get("attach") == "after":
        words = words + [W(g.m[mark]["key"])]
    elif mark:
        words[-1] = _attach(words[-1], g, mark)
    return words


def _object_mark(g, n):
    if n is None:
        return None
    drop = g.m.get("object", {}).get("drop_if_indefinite") and n.get("definite") is False
    return None if drop else "object"


def render_verb(g, f, front_aux):
    out = []
    aux = g.m["modal"][f["modal"]] if f.get("modal") else (g.key("future") if f.get("tense") == "future" else None)
    if aux and not front_aux:
        out.append(W(aux))
    if f.get("negative"):
        out.append(W(g.key("never" if f["negative"] == "never" else "negative")))
    pred = f.get("predicate")
    if pred and "adj" in pred:
        out.append(W(pred["adj"]))
        return out, aux
    v = W(f["verb"])
    if f.get("aspect") == "completed":
        v = _attach(v, g, "completed")
    if f.get("aspect") == "ongoing":
        v = _attach(v, g, "ongoing")
    if f.get("tense") == "past":
        v = _attach(v, g, "past")
    if f.get("register") in ("honorific", "humble"):
        v = _attach(v, g, f["register"])
    if f.get("relation") and "mode" in g.c:
        v = v + W(g.c["mode"][f["relation"] + ("-q" if f.get("type") in ("wh", "yes-no") and
                                                   f["relation"] + "-q" in g.c["mode"] else "")])
    out.append(v)
    return out, aux


def render_clause(g, f, drop=()):
    t = f.get("type", "statement")
    if t == "fragment":
        words = [w if w[:1].isupper() else W(w) for w in f["words"]]
        if g.m.get("evidence", {}).get(f.get("evidence")):
            words.append(W(g.m["evidence"][f["evidence"]]))
        return words
    pred = f.get("predicate") or {}
    wh = f.get("wh")
    slots = {k: [] for k in g.c["clause"]}
    if "emotion" in pred:
        slots["subject"] = [W(pred["emotion"]), W(g.key("in"))] + render_np(g, pred["experiencer"])
    elif f.get("subject") and "subject" not in drop and not (wh and wh.get("role") == "subject"):
        slots["subject"] = render_np(g, f["subject"])
    for a in f.get("adverbs", []):
        slots["adverbs"].append(_attach(W(a["manner"]), g, "adverbial") if isinstance(a, dict) else W(a))
    if f.get("object") and not (wh and wh.get("role") == "patient"):
        slots["object"] = render_np(g, f["object"], _object_mark(g, f["object"]))
    if f.get("goal"):
        slots["goal"] = render_np(g, f["goal"], "toward")
    if f.get("content"):
        slots["content"] = [W(g.key("comp"))] + render_clause(g, f["content"], drop=("subject",))
    front = t in ("wh", "yes-no") and g.c.get("front_aux_in_questions")
    if "noun" in pred:
        identity = g.c.get("identity_1sg")
        if identity and f.get("subject", {}).get("pron") == "1sg":
            slots["subject"] = render_np(g, pred["noun"]) + [W(identity["key"]) + identity["ending"]]
        else:
            slots["verb"] = render_np(g, pred["noun"])
        aux = None
    elif "emotion" in pred or (wh and not f.get("verb") and not pred):
        aux = None
    else:
        slots["verb"], aux = render_verb(g, f, front)
    if g.m.get("evidence", {}).get(f.get("evidence")):
        slots["evidence"] = [W(g.m["evidence"][f["evidence"]])]
    if f.get("noted"):
        slots["evidence"] = [W(g.key("noting"))] + slots["evidence"]
    if f.get("register") == "formal":
        slots["formal"] = [W(g.key("formal"))]
    words = [w for k in g.c["clause"] for w in slots[k]]
    lead = []
    if wh:
        lead = [W(g.c["wh"][wh["word"]])] + (render_np(g, wh["np"]) if wh.get("np") else [])
    elif t == "yes-no":
        lead = [] if (front and aux) else [W(g.key("question"))]
    elif t in ("request", "hortative"):
        lead = [W(g.key(t))]
    if front and aux:
        lead.append(W(aux))
    return lead + words


def render_template(pack, f, branch=None):
    g = Grammar(pack, branch)
    out = ""
    if f.get("vocative") and not f.get("vocative_last"):
        out += " ".join([W(g.key("vocative"))] + render_np(g, f["vocative"])) + ", "
    if f.get("condition"):
        out += " ".join([W(g.key("if"))] + render_clause(g, f["condition"])) + ", "
    out += " ".join(render_clause(g, f))
    if f.get("vocative") and f.get("vocative_last"):
        out += ", " + " ".join([W(g.key("vocative"))] + render_np(g, f["vocative"]))
    end = f.get("punct") or ("?" if f.get("type") in ("wh", "yes-no") else "!" if f.get("exclaim") else ".")
    return out + end


def realize(pack, template, branch=None):
    """A template in dictionary keys to text in the branch's own words."""
    branch = branch or pack.meta["derivation"]["standard"]
    forms = {r["key"]: r[branch] for r in pack.rows() if r.get(branch)}
    text = re.sub(r"\{([^}]+)\}", lambda m: forms.get(m.group(1), "?" + m.group(1)), template)
    return re.sub(r"(^|[.?!:]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)


def render(pack, f, branch=None):
    return realize(pack, render_template(pack, f, branch), branch)


# ---------------- parsing ----------------
class Reader:
    """Text in one branch back to tokens of dictionary keys and grammatical markers."""

    def __init__(self, pack, branch=None):
        self.g = Grammar(pack, branch)
        b = self.g.branch
        rows = pack.rows()
        self.pos = {r["key"]: r["pos"] for r in rows}
        self.form = {}
        for r in sorted(rows, key=lambda r: (r["kind"] == "compound", r["id"])):
            if r.get(b):
                self.form.setdefault(r[b].lower(), r["key"])
        forms = {r["key"]: r[b] for r in rows if r.get(b)}
        self.role_of, self.suffixes, self.prefixes = {}, [], []
        self.word_marker = {}
        for role, spec in self.g.m.items():
            if isinstance(spec, dict) and spec.get("attach") in ("before", "after") and forms.get(spec["key"]):
                self.word_marker[spec["key"]] = (role, spec["attach"])
            elif isinstance(spec, dict) and spec.get("attach") and forms.get(spec["key"]):
                self.role_of[spec["key"]] = role
                (self.prefixes if spec["attach"] == "prefix" else self.suffixes).append(
                    (forms[spec["key"]].lower(), spec["key"], spec["attach"]))
        for rel, k in self.g.c.get("mode", {}).items():
            if forms.get(k):
                self.role_of[k] = "mode:" + rel
                self.suffixes.append((forms[k].lower(), k, "fused"))
        if self.g.c.get("identity_1sg"):
            ident = self.g.c["identity_1sg"]
            self.form[forms[ident["key"]].lower() + ident["ending"]] = ident["key"] + "+1sg"
        self.suffixes.sort(key=lambda s: -len(s[0]))
        self.prefixes.sort(key=lambda s: -len(s[0]))

    def word(self, w):
        """{'key', 'name', 'marks': [roles]} for one written word, or None if unreadable."""
        lw = w.lower()
        if lw in self.form:
            return {"key": self.form[lw], "marks": []}
        for form, key, how in self.suffixes:
            sep = "-" if how == "hyphen" else ""
            if lw.endswith(sep + form) and len(lw) > len(sep + form):
                inner = self.word(w[: -len(sep + form)])
                if inner:
                    inner["marks"].append(self.role_of[key])
                    return inner
        for form, key, how in self.prefixes:
            if lw.startswith(form) and len(lw) > len(form):
                inner = self.word(w[len(form):])
                if inner:
                    inner["marks"].insert(0, self.role_of[key])
                    return inner
        if w[:1].isupper():
            return {"name": w, "marks": []}
        return None


def _inv(d):
    return {v: k for k, v in d.items()}


def parse(pack, text, branch=None):
    rd = Reader(pack, branch)
    g = rd.g
    text = text.strip()
    punct = text[-1] if text[-1] in ".?!" else ""
    body = text[:-1] if punct else text
    segments = [s.strip() for s in body.split(",")]
    frame = {}
    voc_key, if_key = g.key("vocative"), g.key("if")
    main = []
    for i, seg in enumerate(segments):
        toks = [rd.word(w) for w in seg.split()]
        if None in toks:
            raise ValueError(f"cannot read '{seg}'")
        if toks and toks[0].get("key") == voc_key:
            frame["vocative"] = _np(rd, toks[1:])[0]
            if i == len(segments) - 1 and i > 0:
                frame["vocative_last"] = True
        elif toks and toks[0].get("key") == if_key:
            frame["condition"] = _clause(rd, toks[1:], "")
        else:
            main = toks
    frame.update(_clause(rd, main, punct))
    return frame


def _np(rd, toks):
    """Read one noun phrase from the front of toks; return (NP, tokens used, mark)."""
    g = rd.g
    pron, poss = _inv(g.c["pronouns"]), _inv(g.c["possessives"])
    n, used, mark = {}, 0, None
    order = g.c["np_order"]
    pre = set(order[: order.index("head")])                  # modifiers that stand before the noun
    have_head = False
    for i, t in enumerate(toks):
        k, pos = t.get("key"), rd.pos.get(t.get("key"), "")
        marks = [m for m in t["marks"] if m in ("plural", "object", "toward", "of")]
        if not have_head and pre and not ("name" in t or k in pron or pos in ("noun", "pronoun", "phrase", "interjection")):
            if k in poss and "poss" in pre:
                n["poss"] = poss[k]
            elif pos == "number" and "num" in pre:
                n["num"] = k
            elif pos == "adjective" and "mods" in pre:
                n.setdefault("mods", []).append(k)
            else:
                break
        elif not have_head:
            have_head = True
            if "name" in t:
                n["name"] = t["name"]
            elif k in pron:
                n["pron"] = pron[k]
            else:
                n["head"] = k
        elif "of" in t["marks"]:
            n["of"] = {"name": t["name"]} if "name" in t else {"head": k}
        elif k in poss and "poss" not in pre:
            n["poss"] = poss[k]
        elif pos == "number" and "num" not in pre:
            n["num"] = k
        elif pos == "adjective" and "adverbial" not in t["marks"] and "mods" not in pre:
            n.setdefault("mods", []).append(k)
        else:
            break
        used = i + 1
        if "plural" in marks:
            n["plural"] = True
        for m in ("object", "toward"):
            if m in marks:
                mark = m
        if mark:
            break
    return n, used, mark


def _clause(rd, toks, punct, embedded=False):
    g = rd.g
    f = {}
    wh_inv, modal_inv = _inv(g.c["wh"]), _inv(g.m["modal"])
    ev_inv = _inv(g.m.get("evidence", {}))
    first = toks[0].get("key") if toks else None
    if first in (g.key("request"), g.key("hortative")):
        f["type"] = "request" if first == g.key("request") else "hortative"
        toks = toks[1:]
    elif first == g.key("question"):
        f["type"] = "yes-no"
        toks = toks[1:]
    elif first in wh_inv:
        f["type"], f["wh"] = "wh", {"word": wh_inv[first]}
        toks = toks[1:]
    elif first in modal_inv or first == g.key("future"):
        f["type"] = "yes-no"
    elif punct == "?":
        f["type"] = "yes-no"
    # clause-final particles
    while toks and toks[-1].get("key") in list(ev_inv) + [g.key("noting"), g.key("formal")]:
        k = toks.pop()["key"]
        if k in ev_inv:
            f["evidence"] = ev_inv[k]
        elif k == g.key("noting"):
            f["noted"] = True
        else:
            f["register"] = "formal"
    core = list(toks)
    # fronted auxiliary in questions
    if toks and f.get("type") in ("wh", "yes-no") and toks[0].get("key") in list(modal_inv) + [g.key("future")]:
        k = toks.pop(0)["key"]
        if k in modal_inv:
            f["modal"] = modal_inv[k]
        else:
            f["tense"] = "future"
    # emotion: FEELING in NP
    if len(toks) >= 3 and toks[1].get("key") == g.key("in") and not any(rd.pos.get(t.get("key")) == "verb" for t in toks):
        exp, used, _ = _np(rd, toks[2:])
        f["predicate"] = {"emotion": toks[0]["key"], "experiencer": exp}
        rest = toks[2 + used:]
        if rest:
            f["adverbs"] = [t["key"] for t in rest]
        return _tidy(f)
    if f.get("type") == "wh" and toks and not {"object", "toward"} & set(toks[0]["marks"]) and f["wh"]["word"] == "how-many":
        f["wh"]["np"], used, _ = _np(rd, toks)
        toks = toks[used:]
    # the predicate: from the end
    ident = toks and toks[-1].get("key", "").endswith("+1sg")
    if ident:
        toks.pop()
        f["subject"] = {"pron": "1sg"}
        f["predicate"] = {"noun": _np(rd, toks)[0]}
        return _tidy(f)
    pred_i = None
    poss_keys = set(g.c["possessives"].values())
    for i in range(len(toks) - 1, -1, -1):
        t = toks[i]
        if i + 1 < len(toks) and toks[i + 1].get("key") in poss_keys and not t["marks"]:
            continue
        verbal = {"ongoing", "past", "completed", "honorific", "humble"} & set(t["marks"]) or any(m.startswith("mode:") for m in t["marks"])
        if verbal or rd.pos.get(t.get("key")) in ("verb", "auxiliary") and t.get("key") not in modal_inv:
            pred_i = i
            break
    after = []
    if pred_i is None and len(toks) >= 1 and rd.pos.get(toks[-1].get("key")) in ("adjective", "adverb") \
            and not toks[-1]["marks"] and (len(toks) > 1 or f.get("type") in ("yes-no",) or
                                           (len(toks) == 1 and rd.pos.get(toks[-1].get("key")) == "adjective")):
        f["predicate"] = {"adj": toks[-1]["key"]}
        pred_i = len(toks) - 1
    if pred_i is not None:
        v = toks[pred_i]
        if "adj" not in f.get("predicate", {}):
            f["verb"] = v["key"]
            for m in v["marks"]:
                if m == "ongoing":
                    f["aspect"] = "ongoing"
                elif m == "completed":
                    f["aspect"] = "completed"
                elif m == "past":
                    f["tense"] = "past"
                elif m in ("honorific", "humble"):
                    f["register"] = m
                elif m.startswith("mode:"):
                    f["relation"] = m[5:].replace("-q", "")
        before, j, after = toks[:pred_i], pred_i - 1, toks[pred_i + 1:]
        while j >= 0 and before[j].get("key") in (g.key("negative"), g.key("never"), g.key("future"), *modal_inv):
            k = before[j]["key"]
            if k == g.key("future"):
                f["tense"] = "future"
            elif k in modal_inv:
                f["modal"] = modal_inv[k]
            else:
                f["negative"] = "never" if k == g.key("never") else True
            j -= 1
        toks = before[: j + 1]
    # content clause: ... comp CLAUSE VERB
    comp = [i for i, t in enumerate(toks) if t.get("key") == g.key("comp")]
    if comp:
        f["content"] = _clause(rd, toks[comp[0] + 1:], "", embedded=True)
        toks = toks[: comp[0]]
    # noun phrases and adverbs, left to right, before and after the predicate
    unmarked = {"before": [], "after": []}
    for side, seq in (("before", toks), ("after", after)):
        pending = None
        while seq:
            t = seq[0]
            pos = rd.pos.get(t.get("key"), "")
            if t.get("key") in rd.word_marker:          # a preposition: it marks the phrase after it
                pending = rd.word_marker[t["key"]][0]
                seq = seq[1:]
                continue
            if "adverbial" in t["marks"]:
                f.setdefault("adverbs", []).append({"manner": t["key"]})
                seq = seq[1:]
                continue
            if pos == "adverb" and not t["marks"]:
                f.setdefault("adverbs", []).append(t["key"])
                seq = seq[1:]
                continue
            n, used, mark = _np(rd, seq)
            if used < len(seq) and seq[used].get("key") in rd.word_marker and rd.word_marker[seq[used]["key"]][1] == "after":
                mark = rd.word_marker[seq[used]["key"]][0]   # a postposition closes the phrase before it
                used += 1
            seq = seq[max(used, 1):]
            mark = mark or pending
            pending = None
            if mark == "object":
                f["object"] = n
            elif mark == "toward":
                f["goal"] = n
            else:
                unmarked[side].append(n)
    order = unmarked["before"] + unmarked["after"]
    if f.get("type") == "wh" and not f.get("verb") and "predicate" not in f and "np" not in f["wh"]:
        if order:
            f["subject"] = order.pop(0)
        f["wh"]["role"] = "predicate"
    elif unmarked["before"] and "subject" not in f:
        f["subject"] = unmarked["before"].pop(0)        # the first unmarked phrase before the predicate
        order = unmarked["before"] + unmarked["after"]
    if order and not f.get("verb") and "predicate" not in f and f.get("subject") and f.get("type") != "wh":
        f["predicate"] = {"noun": order.pop(0)}
        return _tidy(f)
    if order and "object" not in f:
        n = order.pop(0)
        indef = g.m.get("object", {}).get("drop_if_indefinite")
        f["object"] = dict(n, definite=False) if indef else n
    if f.get("type") == "wh" and "role" not in f["wh"]:
        w = f["wh"]["word"]
        f["wh"]["role"] = ({"where": "location", "when": "time", "why": "reason", "how": "manner", "how-many": "count"}
                           .get(w) or ("patient" if f.get("subject") and not f.get("object") else "subject"))
    if f.get("type") is None and not f.get("subject") and f.get("verb") and punct != "?" and not embedded:
        f["type"] = "command"
    if not f.get("verb") and "predicate" not in f and f.get("type") not in ("wh",):
        words = [t.get("key") or t.get("name") for t in core]
        return {"type": "fragment", "words": words, **({"evidence": f["evidence"]} if f.get("evidence") else {})}
    return _tidy(f)


def _tidy(f):
    return {k: v for k, v in f.items() if v not in (None, [], {}) and DEFAULTS.get(k) != v}


def normalize(f):
    """A frame without its default values, for comparing two frames."""
    if isinstance(f, dict):
        out = {k: normalize(v) for k, v in f.items() if DEFAULTS.get(k) != v and v not in (None, [], {}, False)
               and not (k == "definite" and v is True)}
        return out
    if isinstance(f, list):
        return [normalize(x) for x in f]
    return f
