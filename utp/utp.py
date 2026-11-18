"""UTP command line. Everything works offline; the model and speech commands need a local server.

Language packs
  python3 utp/utp.py packs                     list language packs
  python3 utp/utp.py tree vulcan               family tree of branches
  python3 utp/utp.py derive vulcan "*sehaik"   a proto form in every branch, law by law
  python3 utp/utp.py root vulcan kthalak       is this a legal root of the proto-language?
  python3 utp/utp.py profile vulcan [branch]   the typology profile
  python3 utp/utp.py card vulcan               grammar card (markdown, for people and models)
  python3 utp/utp.py open vulcan               design questions not yet decided

Building a language (packs with a "build" section; the Vulcan pack is read-only)
  python3 utp/utp.py build sample              the whole dictionary: lexicon.csv, check report, dictionaries
  python3 utp/utp.py stats sample
  python3 utp/utp.py export vulcan ./knowledge   dictionary, English index and grammar card for a chat app

Sentences (phase 2: the interlingua)
  python3 utp/utp.py render vulcan frame.json  a language-neutral meaning frame in the pack's grammar
  python3 utp/utp.py parse vulcan "Fa tu lish-pil?"   a sentence back to its frame

Models and speech (optional, local)
  python3 utp/utp.py context vulcan "how do I say the teacher came"   dictionary entries + grammar card to paste
  python3 utp/utp.py propose sample [--n 40]   a model proposes derivations; writes proposals.csv to review
  python3 utp/utp.py curate sample [--n 200]   a model flags template meanings that make no sense
  python3 utp/utp.py apply sample proposals.csv   apply the rows you marked approve=yes, then rebuild
  python3 utp/utp.py say vulcan "Sik tok nash-ve kon" [--voice bm_george] [--out x.wav] [--dry]
  python3 utp/tutor.py drill|talk ...         lessons (see tutor.py)
"""
import argparse
import csv
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from utp.core import Pack, available  # noqa: E402


def cmd_build(pack, a):
    from utp.core.builder import Builder, BuildRefused
    try:
        rows, errors, warnings = Builder(pack).build()
    except BuildRefused as e:
        print(f"Not built: {e}.")
        return 1
    out = Builder(pack).out
    print(f"{len(rows)} entries, {len(errors)} errors, {len(warnings)} warnings -> {out}")
    for e in errors[:20]:
        print("  ", *e)
    return 1 if errors else 0


def cmd_apply(pack, a):
    from utp.core.builder import Builder
    b = Builder(pack)                       # refuses packs that cannot be built (Vulcan)
    rows = list(csv.DictReader(open(a.file, newline="")))
    yes = [r for r in rows if r.get("approve", "").strip().lower() in ("y", "yes", "1", "true")]
    if rows and "parts" in rows[0]:
        lex = {r["key"]: r for r in pack.rows()}
        path = pack.dir / b.cfg.get("meanings", "meanings.csv")
        fields = ["key", "gloss", "pos", "field", "era", "kind", "parts", "notes"]
        new = not path.exists()
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new:
                w.writeheader()
            for r in yes:
                base = lex.get(r["key"], {})
                w.writerow({"key": r["key"], "gloss": base.get("gloss", r.get("gloss", "")), "pos": base.get("pos", ""),
                            "field": base.get("field", ""), "era": base.get("era", ""), "kind": "compound",
                            "parts": r["parts"], "notes": "Built: " + r.get("basis", "")})
        print(f"{len(yes)} derivations added to {path.name}. Run: utp.py build {a.pack}")
    else:
        path = pack.dir / b.cfg.get("exclude", "exclude.txt")
        with open(path, "a") as f:
            f.writelines(r["key"] + "\n" for r in yes)
        print(f"{len(yes)} meanings added to {path.name}. Run: utp.py build {a.pack}")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("pack", nargs="?")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--voice")
    ap.add_argument("--out")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--n", type=int)
    a = ap.parse_args(argv)
    a.file = a.rest[0] if a.rest else None
    if a.cmd == "packs":
        for name in available():
            print(f"{name:12} {Pack(name).name}")
        return 0
    pack = Pack(a.pack)
    text = " ".join(a.rest)
    if a.cmd == "tree":
        for b in pack.laws.branches:
            print(f"{' > '.join(pack.laws.lineage(b)):32} {pack.laws.data['branches'][b].get('label', b)}")
    elif a.cmd == "derive":
        std = pack.meta["derivation"]["standard"]
        for b in pack.laws.branches:
            res, trace = pack.laws.apply(text, b, trace=True)
            print(f"{b:11} {pack.spell(res) if b == std else res:16} {' ; '.join(' > '.join(t) for t in trace)}")
    elif a.cmd == "root":
        ok, why = pack.phonotactics.check(text.lstrip("*"))
        print("legal" if ok else f"not legal: {why}")
        return 0 if ok else 1
    elif a.cmd == "profile":
        prof = pack.typology
        print(json.dumps(prof.get(text) if text else prof, indent=2, ensure_ascii=False))
    elif a.cmd == "card":
        from utp.core.llm import grammar_card
        print(grammar_card(pack))
    elif a.cmd == "open":
        for q in pack.meta.get("open_questions", []):
            print(f"- {q['id']}: {q['question']}\n    {q['proposal']}")
    elif a.cmd == "build":
        return cmd_build(pack, a)
    elif a.cmd == "stats":
        from utp.core.builder import Builder
        print((Builder(pack).out / "stats.json").read_text())
    elif a.cmd == "export":
        from utp.core.builder import write_dictionaries
        from utp.core.llm import grammar_card
        out = pathlib.Path(a.file or "utp-export") / pack.dir.name
        src = {pack.path(k).parent for k in pack.meta["files"]} | {
            (pack.root / h["module"]).resolve().parent for h in pack.meta.get("helpers", {}).values()}
        import os
        home = pathlib.Path(os.path.commonpath([str(d) for d in src]))   # the language's own folder (vulcan-conlang)
        if "build" not in pack.meta and (home == out.resolve() or home in out.resolve().parents
                                         or out.resolve() in home.parents):
            print("Refusing to write among the pack's source files; choose another folder.")
            return 1
        std = pack.meta["derivation"]["standard"]
        write_dictionaries(pack.rows(), std, pack.meta.get("language", pack.name), out)
        (out / "grammar-card.md").write_text(grammar_card(pack))
        (out / "README.md").write_text(f"# {pack.meta.get('language', pack.name)}: knowledge files\n\n"
                                       "Load these into a chat app's knowledge collection with the system prompt in "
                                       "utp/LLM-INSTRUCTIONS.md (Translator and writer).\n")
        print(f"wrote dictionary.md, english.md, grammar-card.md -> {out}")
    elif a.cmd == "context":
        from utp.core.llm import context
        print(context(pack, text))
    elif a.cmd in ("propose", "curate"):
        from utp.core import llm as L
        model = L.LLM()
        if not model.available():
            print(f"No model answering at {model.url} (set UTP_LLM_URL / UTP_LLM_MODEL).")
            return 1
        from utp.core.builder import Builder
        out = Builder(pack).out / f"{'proposals' if a.cmd == 'propose' else 'curation'}.csv"
        if a.cmd == "propose":
            ok, bad = L.propose(pack, pack.rows(), model, limit=a.n or 40, out=out)
            print(f"{len(ok)} valid proposals, {len(bad)} rejected -> {out}. Mark approve=yes, then: utp.py apply {a.pack} {out}")
        else:
            flags = L.curate(pack, pack.rows(), model, limit=a.n or 200, out=out)
            print(f"{len(flags)} meanings flagged -> {out}. Mark approve=yes, then: utp.py apply {a.pack} {out}")
    elif a.cmd == "apply":
        cmd_apply(pack, a)
    elif a.cmd == "say":
        from utp.core.speech import Kokoro, phonemes
        ph, dropped = phonemes(pack, text)
        print(f"phonemes: {ph}" + (f"   (dropped: {''.join(dropped)})" if dropped else ""))
        if a.dry:
            return 0
        k = Kokoro()
        voice = a.voice or pack.meta.get("speech", {}).get("voice", "am_michael")
        try:
            wav = k.say_phonemes(ph, voice)
        except Exception as e:
            print(f"Kokoro did not answer at {k.url}: {e}")
            return 1
        path = pathlib.Path(a.out or "utp-say.wav")
        path.write_bytes(wav)
        print(f"wrote {path} ({len(wav)} bytes, voice {voice})")
    elif a.cmd in ("render", "parse"):
        from utp.core import interlingua as I
        if a.cmd == "render":
            frame = json.loads(pathlib.Path(a.file).read_text()) if a.file and pathlib.Path(a.file).exists() else json.loads(text)
            print(I.render(pack, frame))
        else:
            print(json.dumps(I.parse(pack, text), indent=2, ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
