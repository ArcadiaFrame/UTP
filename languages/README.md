# Languages

Each folder here is a language made with the UTP:

```
python3 utp/utp.py new <name> --language "<Name>" --order SOV|SVO --branches a,b --eras Oldest,...,Newest \
    --consonants "p t k ..." --vowels "a e i o u"
```

or **+ New** in the app. A language folder holds everything about it:

| File | What it is |
|---|---|
| `pack.json` | Every setting: branches, eras, sound shapes, grammar, speech, typology |
| `sound_laws.json` | The proto-language's sounds and each branch's sound changes |
| `meanings.csv` | The language's own meanings, beyond the universal registry (approved batches land here) |
| `DESIGN.md` | Who speaks it and what the words must respect; every model prompt reads it |
| `batches/` | Model-proposed words waiting for review (`utp.py expand`) |
| `build/` | The dictionary (`lexicon.csv`, `dictionary.md`, `english.md`) and its check report |
| `docs/grammar-card.md` | The grammar on one card, for people and models |
| `lab/index.html`, `course/index.html` | The Lab and course, rebuilt with the dictionary (not kept in git; the app builds them on first open) |
| `Open <Language>.command`, `Open <Language>.bat`, `open.py` | Double-click to open the UTP app on this language (macOS, Windows; `python3 open.py` anywhere). `--lab` or `--course` open those directly |

Vulcan lives in `vulcan-conlang/`, built by its own tools; the UTP reads it through `utp/packs/vulcan/`.
