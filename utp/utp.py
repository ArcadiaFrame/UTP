"""UTP command line. Everything works offline; the model commands need a model (local or hosted).

The app (chat, files, Labs and courses in one window)
  python3 utp/utp.py app [--port 8765]         open the UTP app in your browser (or use desktop/ for Electron)

New languages
  python3 utp/utp.py new nerani --language "Nerani" --order SOV --branches high,low \
        --eras Ancient,Old,Middle,Modern --consonants "p t k m n s l r w y h sh" --vowels "a e i o u"
                                               folder, settings, first dictionary, Lab and course in languages/nerani/

Growing a language with a model (nothing joins the language until you approve it)
  python3 utp/utp.py topics nerani [--ai]      what to grow next
  python3 utp/utp.py expand nerani "weather and the sky" [--n 30]   a checked batch -> languages/nerani/batches/
  python3 utp/utp.py apply nerani <batch.csv>  add the rows marked approve=yes, rebuild everything
  python3 utp/utp.py sentences nerani "greetings" [--n 10]   course sentences, checked by a round trip
  python3 utp/utp.py lab nerani | course nerani   regenerate the Lab or course page

The workshop: building from sources, or from nothing (the steps in utp/METHOD.md)
  python3 utp/utp.py sources nerani add notes.md scripts/*.txt --tier canon [--title ...] [--shared]
  python3 utp/utp.py sources nerani paste --tier author --title "My notes"    text from the keyboard or a pipe
  python3 utp/utp.py sources nerani                        list the sources; search with: sources nerani search "ice"
  python3 utp/utp.py sources nerani remove 3 | embed       remove source S3 | meaning-based search vectors
  python3 utp/utp.py sources nerani web "Andorian antennae"        search the web with your SearXNG
  python3 utp/utp.py sources nerani url https://... [--tier canon] fetch pages into the private library
        tiers: author, canon, licensed, fan, science. Sources stay on this computer (not in git), except
        files you put in <language>/sources/public/, which are published with the language.
  python3 utp/utp.py audit nerani [--query "words in Nerani"] [--max 240]   attested words, checked against sources
  python3 utp/utp.py attest nerani "ushaan" --gloss duel --cite S1.3        add one by hand
  python3 utp/utp.py design nerani [--n 3]                draft the next design questions, then answer them here
  python3 utp/utp.py design nerani --decide body B [--reason "..."] | --ask "Is there a military register?"
  python3 utp/utp.py sounds nerani [--accept [--force] | --check]   proto-forms and sound laws that produce the
        attested words; --accept remakes every generated root until words have been approved (--force: always)

Settings (also on the app's Settings page; saved in ~/.utp/config.json)
  python3 utp/utp.py config                    show the settings
  python3 utp/utp.py config --name "Claude" --provider anthropic --model claude-sonnet-5-5 --key sk-ant-... [--role build]
  python3 utp/utp.py config --name "Desktop" --provider ollama --url http://desktop.local:11434/v1 --model qwen3.5:9b --role chat
        a named connection, added or changed; --role chat|build|both picks what it does (default: both)
  python3 utp/utp.py config --languages ~/Conlangs --workspace ~/Writing --kokoro http://localhost:8880 \
        --searxng http://localhost:8080      your SearXNG, for finding sources on the web
  python3 utp/utp.py models [--role build]     the models a connection's server offers
  python3 utp/utp.py shortcut                  a desktop and menu shortcut that opens the app with a double-click

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
  python3 utp/utp.py say vulcan "Sik tok nash-veh kon" [--voice bm_george] [--out x.wav] [--dry]
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
    if not a.dry:                              # the language's Lab, course and grammar card follow every build
        from utp.core import learn
        from utp.core.llm import grammar_card
        pack = Pack(pack.dir)
        (pack.home / "docs").mkdir(exist_ok=True)
        (pack.home / "docs" / "grammar-card.md").write_text(grammar_card(pack))
        for p in learn.build_all(pack, rows):
            print(f"wrote {p}")
    return 1 if errors else 0


def model_or_fail(role="build"):
    from utp.core.models import Model
    m = Model(role=role)
    if not m.available():
        print(f"No model answering: {m}. Set one with: utp.py config --provider ... (see utp.py --help)")
        return None
    return m


def cmd_workshop(a):
    from utp.core import workshop as W
    from utp.core.library import TIERS, Sources
    if not a.pack:
        print(f"usage: utp.py {a.cmd} <language> ...")
        return 2
    pack = Pack(a.pack)
    if a.cmd == "sources":
        verb, args = (a.rest[0] if a.rest else "list"), a.rest[1:]
        src = Sources(pack.home)
        try:
            if verb == "add":
                lib = src.lib(a.shared)
                for f in args:
                    doc, n = lib.add_file(f, a.tier or "canon", a.title if len(args) == 1 else None)
                    print(f"{lib.prefix}{doc}: {f} ({n} passages)" if n else f"{f}: already in the library as {lib.prefix}{doc}")
            elif verb == "paste":
                text = sys.stdin.read()
                doc, n = src.lib(a.shared).add_text(text, a.title or "Pasted text", a.tier or "author")
                print(f"S{doc}: {n} passages")
            elif verb == "search":
                for h in src.search(" ".join(args), k=a.n or 8):
                    print(f"[{h['id']}] {h['tier']}: {h['title']}\n  {h['text'][:300].replace(chr(10), ' ')}\n")
            elif verb == "web":
                from utp.core import websearch as WS
                have = {d["url"] for d in src.docs() if d.get("url")}
                try:
                    for i, r in enumerate(WS.search(" ".join(args), n=a.n or 10), 1):
                        print(f"{i:2}. [{r['tier']}] {r['title']}{'  (in the library)' if r['url'] in have else ''}\n    {r['url']}\n    {r['content'][:200]}")
                except WS.SearchError as e:
                    print(e)
                    return 1
                print(f"Add pages with: utp.py sources {a.pack} url <address> [--tier canon|licensed|fan|science|author]")
            elif verb == "url":
                from utp.core import websearch as WS
                for u_ in args:
                    try:
                        cid, n, title = WS.add_url(src.lib(a.shared), u_, a.tier, a.title if len(args) == 1 else None)
                        print(f"{cid}: {title} ({n} passages)" if n else f"{u_}: already in the library as {cid}")
                    except WS.SearchError as e:
                        print(e)
            elif verb == "remove":
                for d in args:
                    lib = src.libs["G" if d.upper().startswith("G") else "S"]
                    lib.remove(int(d.lstrip("SGsg")))
                    print(f"removed {d}")
            elif verb == "embed":
                from utp.core.library import embedder
                model, name = embedder()
                if not model:
                    print("Meaning-based search is off: set an embedding model in Settings > Sources (for example "
                          "nomic-embed-text on Ollama).")
                    return 1
                for lib in src.libs.values():
                    lib.embed(model, name)
            elif verb == "show":
                for c in args:
                    p = src.passage(c)
                    print(f"[{c}] {p['tier']}: {p['title']}\n{p['text']}\n" if p else f"{c}: not in the library")
            else:
                docs = src.docs()
                for d in docs:
                    print(f"  {d['cite']:5} {d['tier']:9} {d['passages']:4} passages  {d['title']}")
                print(f"{len(docs)} sources, {src.count()} passages. Tiers: {', '.join(TIERS)}")
        finally:
            src.close()
        return 0
    if a.cmd == "attest":
        if not a.file:
            print('usage: utp.py attest <language> "<form>" --gloss ... --cite S1.2')
            return 2
        branches, std = W._branches(pack)
        row = {k: "" for k in W.ATTESTED}
        row.update({"form": a.file, "gloss": a.gloss or "", "kind": a.kind or "word", "branch": a.branch or std,
                    "cite": a.cite or "", "evidence": a.evidence or "", "status": "attested", "tier": a.tier or ""})
        if row["cite"]:
            src = Sources(pack.home)
            try:
                why = W.check_word(src, row)
                p = src.passage(row["cite"].split()[0])
                if p:
                    row["tier"], row["source"] = row["tier"] or p["tier"], p["title"]
            finally:
                src.close()
            if why:
                print(f"Not added: {why}")
                return 1
        rows = W.read_attested(pack)
        W.merge_attested(rows, [row])
        print(f"{a.file} -> {W.write_attested(pack, rows)}")
        return 0
    if a.cmd == "design":
        if a.ask:
            q = W.ask(pack, a.ask)
            print(f"added {q['id']}: {q['question']}")
            return 0
        if a.decide:
            choice = a.rest[0] if a.rest else ""
            q = W.decide(pack, a.decide, choice, a.reason or "")
            print(f"{q['id']}: {q.get('answer') or q['status']} -> DESIGN.md")
            return 0
        state = W.read_decisions(pack)
        if not any(q["options"] for q in state["questions"] if q["status"] == "open"):
            model = model_or_fail()
            if not model:
                return 1
            W.draft(pack, model, n=a.n or 3)
            state = W.read_decisions(pack)
        for q in [q for q in state["questions"] if q["status"] == "open" and q["options"]]:
            print(f"\n{q['id']}: {q['question']}")
            for o in q["options"]:
                tag = " (recommended)" if o["id"] == q.get("recommended") else ""
                cites = f" [{', '.join(o['cites'])}]" if o["cites"] else " [invention]"
                print(f"  {o['id']}. {o['label']}{tag}{cites}\n     {o['argument']}")
            if not sys.stdin.isatty():
                continue
            ans = input("Choose a letter, write your own answer, 'skip', or press Enter to leave it open: ").strip()
            if ans:
                reason = input("Why? (optional) ").strip() if ans.lower() != "skip" else ""
                q = W.decide(pack, q["id"], ans, reason)
                print(f"  -> {q.get('answer') or q['status']}")
        done = sum(q["status"] == "decided" for q in W.read_decisions(pack)["questions"])
        print(f"\n{done} decided. DESIGN.md: {pack.home / 'DESIGN.md'}")
        return 0
    if a.cmd == "audit":
        if a.check:
            probs = W.check_attested(pack)
            for f, why in probs:
                print(f"  {f}: {why}")
            print(f"{len(probs)} attested words not borne out by their sources")
            return 1 if probs else 0
        model = model_or_fail()
        if not model:
            return 1
        added, rejected = W.audit(pack, model, query=a.query, max_passages=a.max or 240)
        for r in rejected:
            print(f"  rejected {r['form']}: {r['why']}")
        print(f"{added} new attested words -> {W.attested_path(pack)}")
        return 0
    if a.cmd == "sounds":
        if a.check:
            res = W.check_sounds(pack)
        elif a.accept:
            words, tests = W.accept_sounds(pack, fresh=True if a.force else None)
            print(f"sound_laws.json updated; {words} attested words joined meanings.csv; {tests} tests. "
                  f"Rebuild with: utp.py build {a.pack}")
            return 0
        else:
            model = model_or_fail()
            if not model:
                return 1
            prop = W.propose_sounds(pack, model)
            res = prop["fit"]
            print(prop["notes"])
        for r in res:
            print(f"  {'ok ' if r['ok'] else 'NO '} {r['proto'] or '?':16} -> {r['got'] or '?':16} {r['form']} ({r['branch']}) {r['why'] if not r['ok'] else ''}")
        print(f"{sum(r['ok'] for r in res)}/{len(res)} attested words produced by the laws"
              + ("" if a.check else f". Accept with: utp.py sounds {a.pack} --accept"))
        return 0
    return 2


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
    for opt in ("language", "order", "branches", "eras", "consonants", "vowels", "about",
                "provider", "model", "key", "url", "page", "name", "role", "languages", "workspace", "kokoro"):
        ap.add_argument(f"--{opt}")
    for opt in ("tier", "title", "query", "gloss", "cite", "kind", "decide", "reason", "ask", "evidence", "branch", "searxng"):
        ap.add_argument(f"--{opt}")
    ap.add_argument("--max", type=int)
    ap.add_argument("--shared", action="store_true")
    ap.add_argument("--accept", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--ai", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    a.file = a.rest[0] if a.rest else None
    if a.cmd == "packs":
        for name in available():
            print(f"{name:12} {Pack(name).name}")
        return 0
    if a.cmd == "app":
        from utp.app import server
        return server.main(["--port", str(a.port), "--open"] + (["--language", a.pack] if a.pack else []))
    if a.cmd in ("config", "models"):
        from utp.core import config as C, models as M
        if a.cmd == "config":
            if any((a.provider, a.model, a.key is not None, a.url, a.name)):
                roles = ["chat", "build"] if (a.role or "both") == "both" else [a.role]
                if a.name:
                    cid = next((c["id"] for c in C.load()["connections"] if c["name"] == a.name), None)
                    base = C.connection(cid) if cid else {}
                    prov = a.provider or base.get("provider") or "ollama"
                    same = prov == base.get("provider")
                    cid = C.upsert_connection({"id": cid, "name": a.name, "provider": prov,
                                               "url": a.url or (base.get("url") if same else ""),
                                               "model": a.model or (base.get("model") if same else "")}, key=a.key)
                    C.update({"roles": {r: cid for r in roles}})
                else:
                    cfg = {k: v for k, v in (("provider", a.provider), ("model", a.model), ("url", a.url)) if v}
                    if a.key is not None:
                        cfg["keys"] = {a.provider or M.Model().provider: a.key}
                    M.save_config(cfg)
            patch = {}
            if a.languages:
                patch["paths"] = {"languages": str(pathlib.Path(a.languages).expanduser().resolve())}
            if a.workspace:
                ws = C.load()["paths"]["workspaces"] + [{"name": pathlib.Path(a.workspace).name,
                                                         "path": str(pathlib.Path(a.workspace).expanduser().resolve())}]
                patch.setdefault("paths", {})["workspaces"] = ws
            if a.kokoro:
                patch["speech"] = {"url": a.kokoro}
            if a.searxng is not None:
                patch["search"] = {"searxng": a.searxng.rstrip("/")}
            if patch:
                C.update(patch)
            pub = C.public()
            print(f"settings: {pub['config_path']}")
            for c in pub["connections"]:
                roles = [r for r, v in pub["roles"].items() if v == c["id"]]
                print(f"  {c['name']:24} {c['provider']:10} {c['model']:24} {c['url']}"
                      f"{'  key set' if c['key_set'] else ''}{'  [' + ', '.join(roles) + ']' if roles else ''}")
            print(f"  languages: {pub['languages_dir']}")
            for w in pub["paths"]["workspaces"]:
                print(f"  workspace: {w['path']}")
            print(f"  speech:    {pub['speech']['url']}")
            print(f"  search:    {pub.get('search', {}).get('searxng') or '(no SearXNG set: utp.py config --searxng http://...)'}")
            if pub["env_overrides"]:
                print(f"  (overridden by environment: {', '.join(pub['env_overrides'])})")
            return 0
        try:
            print("\n".join(M.Model(role=a.role or "chat").models()))
            return 0
        except M.ModelError as e:
            print(e)
            return 1
    if a.cmd in ("sources", "audit", "attest", "design", "sounds"):
        return cmd_workshop(a)
    if a.cmd == "shortcut":
        from utp.app import launch
        for line in launch.install_shortcuts():
            print(line)
        return 0
    if a.cmd == "new":
        from utp.core import newlang
        try:
            home = newlang.create(a.pack, language=a.language, order=a.order or "SOV",
                                  branches=(a.branches or "standard").split(","),
                                  eras=(a.eras or "Ancient,Old,Middle,Modern").split(","),
                                  consonants=a.consonants or newlang.DEFAULT_CONSONANTS,
                                  vowels=a.vowels or newlang.DEFAULT_VOWELS, about=a.about or "", force=a.force)
        except (ValueError, FileExistsError) as e:
            print(f"Not created: {e}")
            return 1
        print(f"created {home}")
        if not a.dry:
            rows, errors, warnings = newlang.first_build(home)
            print(f"first build: {len(rows)} entries, {len(errors)} errors -> {home / 'build'}; Lab and course written")
            print(f"next: edit {home / 'DESIGN.md'}, then python3 {home / 'open.py'}")
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
        head = open(a.file).readline()
        if "status" in head and "kind" in head:          # a batch from utp.py expand
            from utp.core import expand as X
            added, errors = X.apply_batch(pack, a.file)
            print(f"{added} words added, {len(errors)} build errors")
            for e in errors[:20]:
                print("  ", *e)
            return 1 if errors else 0
        cmd_apply(pack, a)
    elif a.cmd in ("expand", "sentences", "topics"):
        from utp.core import expand as X
        if a.cmd == "topics" and not a.ai:
            print("\n".join(X.suggest_topics(pack)))
            return 0
        model = model_or_fail()
        if not model:
            return 1
        if a.cmd == "topics":
            print("\n".join(X.suggest_topics(pack, model)))
        elif a.cmd == "expand":
            path, rows = X.propose_batch(pack, text, model, n=a.n or 30)
            ok = sum(r["status"] == "proposed" for r in rows)
            print(f"{ok} proposals to review, {len(rows) - ok} rejected with reasons -> {path}")
            print(f"Mark approve=yes on the rows to keep, then: utp.py apply {a.pack} {path}")
        else:
            ok, bad = X.propose_sentences(pack, text, model, n=a.n or 10)
            path, added = X.add_sentences(pack, [dict(s, topic=text) for s in ok])
            for s in ok:
                print(f"  {s['v']}   {s['en']}")
            for s in bad:
                print(f"  rejected: {s['en']} ({s['why']})")
            print(f"{added} sentences added -> {path}")
            from utp.core import learn
            learn.build_course(pack)
    elif a.cmd in ("lab", "course"):
        from utp.core import learn
        out = learn.build_lab(pack) if a.cmd == "lab" else learn.build_course(pack)
        print(f"wrote {out}" if out else f"{pack.id} has its own course (see its folder)")
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
