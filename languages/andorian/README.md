# Andorian

Made with the UTP. Every file below is generated from `pack.json`, `sound_laws.json` and `meanings.csv`.

| Do this | Command (from the repository's top folder) |
|---|---|
| Open the app on this language | double-click `Open Andorian.command` (macOS) or `Open Andorian.bat` (Windows), or `python3 languages/andorian/open.py` |
| Rebuild the dictionary, Lab and course | `python3 utp/utp.py build andorian` |
| Ask a model for a batch of new words on a topic | `python3 utp/utp.py expand andorian "kinship and the household" --n 40` |
| Approve a batch (mark `approve` = yes in the CSV), then | `python3 utp/utp.py apply andorian languages/andorian/batches/<file>.csv` |
| Ask a model for course sentences | `python3 utp/utp.py sentences andorian "greetings" --n 12` |
| Grammar card for any chat model | `python3 utp/utp.py card andorian` |
| Add sources (scripts, notes, wiki pages, papers) | `python3 utp/utp.py sources andorian add <files> --tier canon` |
| Find the words the sources already use | `python3 utp/utp.py audit andorian` |
| Work through the design questions | `python3 utp/utp.py design andorian` |
| Sound laws that produce the attested words | `python3 utp/utp.py sounds andorian`, then `--accept` |

Files: `build/dictionary.md` and `build/english.md` (the dictionaries), `build/check_report.md`,
`docs/grammar-card.md`, `lab/index.html` (open in any browser; the tutor needs the app),
`course/index.html`, `batches/` (proposals waiting for review).

Design notes that every model prompt reads: `DESIGN.md`. How the steps fit together: `utp/METHOD.md`.
