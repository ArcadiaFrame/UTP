"""UTP tutor: drills with spaced repetition, and conversation practice, with speech.

  python3 utp/tutor.py drill vulcan                 words due today (Leitner boxes), typed answers
  python3 utp/tutor.py drill vulcan --reverse       see the word, recall the meaning
  python3 utp/tutor.py talk vulcan                  conversation with a local model as tutor
  python3 utp/tutor.py talk --language Spanish      the same for a human language the model knows
  options: --speak (Kokoro), --n 20 (cards per drill), --level beginner|intermediate|advanced,
           --era Tribal (drill one era), --field kinship

The method follows the order that works for a human learner: sounds first (every
card can be heard), core vocabulary before later vocabulary (the oldest roots come
first), then sentences in conversation, with every new word looked up in the
dictionary so the model never invents vocabulary.
Progress is kept in ~/.utp/progress/. Nothing here needs the internet.
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utp.core import Pack  # noqa: E402
from utp.core.llm import LLM, context, grammar_card, section  # noqa: E402
from utp.core.speech import LANGUAGE_VOICES, Kokoro  # noqa: E402

HOME = pathlib.Path.home() / ".utp"
INTERVALS = [0, 1, 3, 7, 21, 60]          # days before a card in box n comes back


def today():
    return datetime.date.today()


class Deck:
    def __init__(self, name):
        self.path = HOME / "progress" / f"{name}.json"
        self.cards = json.loads(self.path.read_text()) if self.path.exists() else {}

    def due(self, keys, n, new_limit):
        t = today().isoformat()
        old = [k for k in keys if k in self.cards and self.cards[k]["due"] <= t][:n]
        new = [k for k in keys if k not in self.cards][:max(0, min(new_limit, n - len(old)))]
        return old + new

    def grade(self, key, ok):
        box = self.cards.get(key, {"box": 0})["box"]
        box = min(box + 1, len(INTERVALS) - 1) if ok else 0
        self.cards[key] = {"box": box, "due": (today() + datetime.timedelta(days=INTERVALS[box])).isoformat()}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.cards, indent=1))


class Voice:
    """Speak through Kokoro if it is running; otherwise stay silent and say so once."""
    def __init__(self, on, pack=None, language=None, voice=None, out=print):
        self.k, self.pack, self.language, self.voice, self.out = Kokoro(), pack, language, voice, out
        self.on = on and self.k.available()
        if on and not self.on:
            out(f"(Kokoro is not answering at {self.k.url}: continuing without sound)")

    def say(self, text):
        if not self.on or not text:
            return None
        try:
            if self.pack:
                wav, _, _ = self.k.say_word(self.pack, text, self.voice)
            else:
                wav = self.k.say_text(text, self.voice or LANGUAGE_VOICES.get((self.language or "").lower(), "af_heart"))
        except Exception as e:
            self.out(f"(speech failed: {e})")
            return None
        return play(wav)


def play(wav):
    f = HOME / "audio" / "last.wav"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(wav)
    for cmd in (["afplay"], ["aplay", "-q"], ["paplay"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]):
        if shutil.which(cmd[0]):
            subprocess.run(cmd + [str(f)], check=False)
            break
    return f


def norm(s):
    return re.sub(r"[^\w'\- ]", "", s.lower()).strip()


def drill(pack, args, inp=input, out=print):
    std = pack.meta["derivation"]["standard"]
    era_rank = {e["id"]: e["rank"] for e in pack.meta.get("eras", [])}
    rows = [r for r in pack.rows() if r.get(std) and r.get("field") != "grammar"
            and (not args.era or r.get("era") == args.era) and (not args.field or r.get("field") == args.field)]
    rows.sort(key=lambda r: (era_rank.get(r.get("era"), 9), r.get("kind") == "compound", r["id"]))
    by = {r["key"]: r for r in rows}
    deck = Deck(f"{pack.dir.name}{'-reverse' if args.reverse else ''}")
    keys = deck.due([r["key"] for r in rows], args.n, args.n)
    voice = Voice(args.speak, pack, out=out)
    right = 0
    out(f"{len(keys)} cards due. Type the answer; an empty line shows it. Type /quit to stop.\n")
    for k in keys:
        r = by[k]
        if args.reverse:
            out(f"  {r[std]}")
            voice.say(r[std])
            a = inp("  meaning? ")
            if a.strip() == "/quit":
                break
            out(f"  = {r['gloss']}  ({r['pos']}{', built from ' + r['parts'] if r.get('parts') else ''})")
            ok = bool(a.strip()) and (norm(a) in norm(r["gloss"]) or inp("  right? [y/n] ").lower().startswith("y"))
        else:
            out(f"  {r['gloss']}  ({r['pos']})")
            a = inp("  word? ")
            if a.strip() == "/quit":
                break
            ok = norm(a) == norm(r[std])
            out(f"  {'yes' if ok else 'answer:'} {r[std]}{'  built from ' + r['parts'] if r.get('parts') else ''}")
            voice.say(r[std])
        right += ok
        deck.grade(k, ok)
    deck.save()
    out(f"\n{right} of {len(keys)} right. Progress saved.")
    return right


def parse_turn(text):
    """The tutor answers in labelled lines; TARGET is the line to speak."""
    lines = {m.group(1).upper(): m.group(2).strip() for m in re.finditer(r"^\s*(TARGET|GLOSS|ENGLISH|NOTE)\s*:\s*(.*)$", text, re.M)}
    return lines


def talk(args, inp=input, out=print, llm=None):
    llm = llm or LLM()
    pack = Pack(args.pack) if args.pack else None
    if not llm.available():
        out(f"No language model is answering at {llm.url}. Start Ollama (or set UTP_LLM_URL) and try again.")
        return 1
    lang = pack.meta.get("language", pack.name) if pack else args.language
    system = section("Tutor").replace("{LANGUAGE}", lang).replace("{LEVEL}", args.level)
    if pack:
        system += "\n\n" + grammar_card(pack)
        rows = pack.rows()
    messages = [{"role": "system", "content": system}]
    voice = Voice(args.speak, pack, args.language, out=out)
    out(f"Conversation practice in {lang} ({args.level}). Write in {lang} or English. /quit to stop, /again to hear it again.\n")
    last = ""
    first = "Begin the lesson: greet me and ask one simple question."
    while True:
        user = first if first else inp("you: ")
        if user.strip() == "/quit":
            break
        if user.strip() == "/again":
            voice.say(last)
            continue
        turn = list(messages)
        if pack:
            turn.append({"role": "system", "content": "Look these up; use no word that is not in them:\n"
                                                      + context(pack, user + " " + last, rows, limit=30)})
        turn.append({"role": "user", "content": user})
        reply = llm.chat(turn, temperature=0.6)
        messages += [{"role": "user", "content": user}, {"role": "assistant", "content": reply}]
        parts = parse_turn(reply)
        out("tutor: " + (reply if not parts else "\n       ".join(f"{k.lower()}: {v}" for k, v in parts.items())))
        last = parts.get("TARGET", "")
        voice.say(last)
        first = None
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["drill", "talk"])
    ap.add_argument("pack", nargs="?")
    ap.add_argument("--language")
    ap.add_argument("--reverse", action="store_true")
    ap.add_argument("--speak", action="store_true")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--era")
    ap.add_argument("--field")
    ap.add_argument("--level", default="beginner")
    args = ap.parse_args(argv)
    if args.mode == "drill":
        if not args.pack:
            ap.error("drill needs a pack (human languages: use talk --language)")
        drill(Pack(args.pack), args)
        return 0
    if not args.pack and not args.language:
        ap.error("talk needs a pack or --language")
    return talk(args)


if __name__ == "__main__":
    sys.exit(main())
