"""Phase 2: language-neutral frames against the Vulcan phrasebook.

  python3 utp/tests/test_interlingua.py

For each phrasebook line below, a frame written in no language must:
  1. render to the phrasebook's own template, key for key
  2. realize to the phrasebook's Vulcan text, where the phrasebook gives it
  3. parse back from that text to the same frame (or, where Vulcan itself is
     ambiguous, to a frame that renders the same sentence)
Then the same frames render in Romulan (rank endings, no evidentials) and in the
SVO sample language, and parse back there too.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from utp.core import Pack  # noqa: E402
from utp.core import interlingua as I  # noqa: E402

S1, S2, S3, P1, P2 = {"pron": "1sg"}, {"pron": "2sg"}, {"pron": "3sg"}, {"pron": "1pl"}, {"pron": "2hon"}
CASES = [
    ("p08", "{thanks}.", "Chaya.", {"type": "fragment", "words": ["thanks"]}),
    ("p10", "{nash-ve} {apologize}.", "Nash-veh keshir.", {"subject": S1, "verb": "apologize"}),
    ("p11", "{request} {again} {say}.", "Kor kir pokok.", {"type": "request", "adverbs": ["again"], "verb": "say"}),
    ("p12", "{request} {slow}-{adverbial} {speak}.", "Kor yeikuf-fu stariben.",
     {"type": "request", "adverbs": [{"manner": "slow"}], "verb": "speak"}),
    ("p15", "{nash-ve} {not} {understand}.", "Nash-veh suhk haska.", {"subject": S1, "negative": True, "verb": "understand"}),
    ("p21", "{nash-ve} {language} {your}-{object-wizh} {learn}-{ongoing}.", "Nash-veh sitvokhhol sau-wizh haumok-pil.",
     {"subject": S1, "object": {"head": "language", "poss": "2sg"}, "verb": "learn", "aspect": "ongoing"}),
    ("p55", "{ev-seen}.", "Ho.", {"type": "fragment", "words": [], "evidence": "seen"}),
    ("p22", "{what} {name} {your}?", "Wakli gor sau?",
     {"type": "wh", "wh": {"word": "what", "role": "predicate"}, "subject": {"head": "name", "poss": "2sg"}}),
    ("p23", "{name} {my} Sorel.", "Gor keru Sorel.", {"subject": {"head": "name", "poss": "1sg"}, "predicate": {"noun": {"name": "Sorel"}}}),
    ("p24", "{where} {tu} {go}-{ongoing}?", "Fa tu lish-pil?",
     {"type": "wh", "wh": {"word": "where", "role": "location"}, "subject": S2, "verb": "go", "aspect": "ongoing"}),
    ("p25", "{gishun}?", "Ghishun?", {"type": "wh", "wh": {"word": "why", "role": "predicate"}}),
    ("p26", "{when} {dungi} {tu} {come}?", "Tun dungi tu sarlah?",
     {"type": "wh", "wh": {"word": "when", "role": "time"}, "subject": S2, "verb": "come", "tense": "future"}),
    ("p27", "{who} {ish-ve}?", "Thuh ish-veh?", {"type": "wh", "wh": {"word": "who", "role": "predicate"}, "subject": S3}),
    ("p28", "{how-many} {hour}-{plural}?", "Ar-ok' varen-k'oo?",
     {"type": "wh", "wh": {"word": "how-many", "role": "count", "np": {"head": "hour", "plural": True}}}),
    ("p29", "{how} {work} {your}?", "Ar hukhnu sau?",
     {"type": "wh", "wh": {"word": "how", "role": "predicate"}, "subject": {"head": "work", "poss": "2sg"}}),
    ("p30", "{work} {my} {well}.", "Hukhnu keru ta.", {"subject": {"head": "work", "poss": "1sg"}, "predicate": {"adj": "well"}}),
    ("p31", "{kup} {tu} {nash-ve}-{object-wizh} {help}?", "Kup tu nash-veh-wizh neru?",
     {"type": "yes-no", "modal": "ability", "subject": S2, "object": S1, "verb": "help"}),
    ("p32", "{nash-ve} {kup} {help}.", "Nash-veh kup neru.", {"subject": S1, "modal": "ability", "verb": "help"}),
    ("p33", "{request} {nash-ve}-{object-wizh} {follow}.", "Kor nash-veh-wizh kokin.", {"type": "request", "object": S1, "verb": "follow"}),
    ("p34", "{hortative} {go}.", "Thu lish.", {"type": "hortative", "verb": "go"}),
    ("p35", "{not} {go}.", "Suhk lish.", {"type": "command", "negative": True, "verb": "go"}),
    ("p36", "{question} {tu} {tea} {want}?", "Kuth tu sakam dawru?",
     {"type": "yes-no", "subject": S2, "object": {"head": "tea", "definite": False}, "verb": "want"}),
    ("p37", "{nash-ve} {here} {wait}-{ongoing}.", "Nash-veh tan patak-pil.",
     {"subject": S1, "adverbs": ["here"], "verb": "wait", "aspect": "ongoing"}),
    ("p38", "{ish-ve} {comp} {come}-{past-un} {say}-{past-un}.", "Ish-veh meen sarlah-un pokok-un.",
     {"subject": S3, "content": {"verb": "come", "tense": "past"}, "verb": "say", "tense": "past"}),
    ("p39", "{ish-ve} {come}-{past-un} {ev-reported}.", "Ish-veh sarlah-un k'en.",
     {"subject": S3, "verb": "come", "tense": "past", "evidence": "reported"}),
    ("p40", "{if} {tu} {come}, {we} {kal-toh} {dungi} {play}.", "K'u tu sarlah, ekh kal-toh dungi nol.",
     {"condition": {"subject": S2, "verb": "come"}, "subject": P1, "object": {"head": "kal-toh", "definite": False},
      "verb": "play", "tense": "future"}),
    ("p45", "{we} {now} {eat}-{ongoing}.", "Ekh tir sokzha-pil.", {"subject": P1, "adverbs": ["now"], "verb": "eat", "aspect": "ongoing"}),
    ("p56", "{nash-ve} {work}-{ongoing}-{past-un}.", "Nash-veh hukhnu-pil-un.",
     {"subject": S1, "verb": "work", "aspect": "ongoing", "tense": "past"}),
    ("p59", "{nash-ve} {hungry}.", "Nash-veh tuhkukhuk.", {"subject": S1, "predicate": {"adj": "hungry"}}),
    ("p60", "{request} {tea}-{object-wizh} {pour}.", "Kor sakam-wizh ke'ik.", {"type": "request", "object": {"head": "tea"}, "verb": "pour"}),
    ("p66", "{what} {sensor}-{plural} {see}-{past-un}?", "Wakli nalsowash-k'oo kosha-un?",
     {"type": "wh", "wh": {"word": "what", "role": "patient"}, "subject": {"head": "sensor", "plural": True},
      "verb": "see", "tense": "past"}),
    ("p67", "{ship} {new} {here}{toward} {come}-{ongoing} {ev-seen}.", "Shelek kaun tanfi sarlah-pil ho.",
     {"subject": {"head": "ship", "mods": ["new"]}, "goal": {"head": "here"}, "verb": "come", "aspect": "ongoing",
      "evidence": "seen"}),
    ("p68", "{question} {dangerous}?", "Kuth boruk?", {"type": "yes-no", "predicate": {"adj": "dangerous"}}),
    ("p70", "{shield}-{object-wizh} {activate}.", "Haushmik-wizh tekak-kar.", {"type": "command", "object": {"head": "shield"}, "verb": "activate"}),
    ("p74", "{signal} {perfect-ki}{send}.", "Skak ki'suluv.", {"subject": {"head": "signal"}, "verb": "send", "aspect": "completed"}),
    ("p78", "{anger} {in} {nash-ve} {noting}.", "Sik tok nash-veh kon.", {"predicate": {"emotion": "anger", "experiencer": S1}, "noted": True}),
    ("p80", "{younger-sibling} {my} {nash-ve}-{object-wizh} {taunt}-{past-un}.", "Tasas keru nash-veh-wizh ikik-un.",
     {"subject": {"head": "younger-sibling", "poss": "1sg"}, "object": S1, "verb": "taunt", "tense": "past"}),
    ("p82", "{nash-ve} {younger-sibling} {my}-{object-wizh} {forgive}.", "Nash-veh tasas keru-wizh ral.",
     {"subject": S1, "object": {"head": "younger-sibling", "poss": "1sg"}, "verb": "forgive"}),
    ("p103", "{vocative} {aunt-uncle}, {welcome}.", None, {"vocative": {"head": "aunt-uncle"}, "type": "fragment", "words": ["welcome"]}),
    ("p107", "{niece-nephew} {your} {be}ish.", None, {"subject": S1, "predicate": {"noun": {"head": "niece-nephew", "poss": "2sg"}}}),
    ("p108", "{grandparent} {house}{toward} {arrive}-{past-un} {ev-reported}.", None,
     {"subject": {"head": "grandparent"}, "goal": {"head": "house"}, "verb": "arrive", "tense": "past", "evidence": "reported"}),
    ("p109", "{hortative} {grandparent}-{object-wizh} {greet}.", None, {"type": "hortative", "object": {"head": "grandparent"}, "verb": "greet"}),
    ("p112", "{family} {our} {strong}.", None, {"subject": {"head": "family", "poss": "1pl"}, "predicate": {"adj": "strong"}}),
    ("p125", "{tu} {feverish} {ev-inferred}.", None, {"subject": S2, "predicate": {"adj": "feverish"}, "evidence": "inferred"}),
    ("p134", "{thanks}, {vocative} {healer}.", None,
     {"type": "fragment", "words": ["thanks"], "vocative": {"head": "healer"}, "vocative_last": True}),
    ("p147", "{defendant} {secret}-{object-wizh} {steal}-{past-un} {ev-seen}.", None,
     {"subject": {"head": "defendant"}, "object": {"head": "secret"}, "verb": "steal", "tense": "past", "evidence": "seen"}),
    ("p216", "{attraction} {in} {nash-ve} {noting}.", None, {"predicate": {"emotion": "attraction", "experiencer": S1}, "noted": True}),
    ("p221", "{attraction} {in} {ish-ve} {also} {ev-inferred}.", None,
     {"predicate": {"emotion": "attraction", "experiencer": S3}, "adverbs": ["also"], "evidence": "inferred"}),
    ("p224", "{confidant} {your} {be}ish.", None, {"subject": S1, "predicate": {"noun": {"head": "confidant", "poss": "2sg"}}}),
    ("p239", "{kup} {nash-ve} {spar}-{humble}?", None,
     {"type": "yes-no", "modal": "ability", "subject": S1, "verb": "spar", "register": "humble"}),
    ("ex1", "{nash-ve} {not} {know}-{humble}.", None, {"subject": S1, "negative": True, "verb": "know", "register": "humble"}),
    ("ex2", "{vocative} {mentor}, {request} {tu} {speak}-{honorific}.", None,
     {"vocative": {"head": "mentor"}, "type": "request", "subject": S2, "verb": "speak", "register": "honorific"}),
]
SAMPLE = [  # frames for the SVO sample language (its dictionary has no Vulcan culture words)
    {"subject": {"head": "mother", "poss": "1sg"}, "object": {"head": "fish", "mods": ["big"]}, "verb": "eat", "tense": "past"},
    {"type": "wh", "wh": {"word": "where", "role": "location"}, "subject": S2, "verb": "go", "aspect": "ongoing"},
    {"type": "yes-no", "subject": S2, "object": {"head": "water"}, "verb": "want"},
    {"subject": S1, "goal": {"head": "house"}, "verb": "go", "tense": "future", "negative": True},
    {"type": "request", "object": {"head": "water"}, "verb": "give"},
    {"subject": {"head": "child", "plural": True}, "verb": "sleep", "aspect": "ongoing"},
    {"type": "wh", "wh": {"word": "who", "role": "subject"}, "object": {"head": "dog"}, "verb": "see", "tense": "past"},
]


def main():
    v, s = Pack("vulcan"), Pack("sample")
    if not s.path("lexicon").exists():                  # the sample is rebuilt on a fresh clone
        from utp.core.builder import Builder
        Builder(s).build()
        s = Pack("sample")
    report, fails = [], 0
    tmpl_ok = text_ok = frame_ok = same_ok = 0
    texts = 0
    for cid, want, vulcan, frame in CASES:
        got = I.render_template(v, frame)
        txt = I.realize(v, got)
        back = I.parse(v, txt)
        again = I.render(v, back)
        tmpl_ok += got == want
        if vulcan:
            texts += 1
            text_ok += txt == vulcan
        frame_ok += I.normalize(back) == I.normalize(frame)
        same_ok += again == txt
        if got != want or (vulcan and txt != vulcan) or again != txt:
            fails += 1
            report.append(f"  {cid}: template {got!r} (want {want!r}); text {txt!r}; parsed {json.dumps(back)} -> {again!r}")
    n = len(CASES)
    report.insert(0, f"[{'PASS' if tmpl_ok == n else 'FAIL'}] Vulcan: {tmpl_ok}/{n} frames render the phrasebook's own template")
    report.insert(1, f"[{'PASS' if text_ok == texts else 'FAIL'}] Vulcan: {text_ok}/{texts} realize to the phrasebook's Vulcan text")
    report.insert(2, f"[{'PASS' if same_ok == n else 'FAIL'}] Vulcan: {same_ok}/{n} parse back to a frame that says the same sentence")
    report.insert(3, f"[INFO] Vulcan: {frame_ok}/{n} parse back to the identical frame (the rest are Vulcan's own ambiguities, below)")
    amb = [cid for cid, _, _, fr in CASES if I.normalize(I.parse(v, I.render(v, fr))) != I.normalize(fr)]
    report.insert(4, f"       ambiguous by design: {amb}")

    rom_ok = 0
    for cid, _, _, frame in CASES:
        fr = dict(frame, relation="up") if frame.get("type") != "fragment" else frame
        txt = I.render(v, fr, "romulan")
        back = I.parse(v, txt, "romulan")
        good = "?" not in txt.replace("?", "", txt.endswith("?")) and I.render(v, back, "romulan") == txt
        rom_ok += good
        if not good:
            report.append(f"  romulan {cid}: {txt!r}")
    no_ev = all(" ho" not in I.render(v, dict(f, relation="up"), "romulan").lower() for _, _, _, f in CASES if f.get("evidence") == "seen")
    fails += rom_ok != n or not no_ev
    report.append(f"[{'PASS' if rom_ok == n and no_ev else 'FAIL'}] Romulan: {rom_ok}/{n} same frames render with rank endings, "
                  f"no evidentials, and parse back")

    s_ok = 0
    for fr in SAMPLE:
        txt = I.render(s, fr)
        back = I.parse(s, txt)
        good = "?" not in txt[:-1] and I.normalize(back) == I.normalize(fr)
        s_ok += good
        if not good:
            report.append(f"  sample: {txt!r} -> {json.dumps(back)}")
    fails += s_ok != len(SAMPLE)
    report.append(f"[{'PASS' if s_ok == len(SAMPLE) else 'FAIL'}] SVO sample language: {s_ok}/{len(SAMPLE)} frames render and parse back identically")
    report.append("Example, one frame in three grammars:")
    fr = SAMPLE[0]
    report += [f"  vulcan:  {I.render(v, fr)}", f"  romulan: {I.render(v, dict(fr, relation='up'), 'romulan')}",
               f"  sample:  {I.render(s, fr)}"]
    print("\n".join(report))
    print("ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
