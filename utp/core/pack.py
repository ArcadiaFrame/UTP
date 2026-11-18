"""UTP language packs.

A pack is a folder with one pack.json. It names the language family's data files
(paths relative to the pack's root), its derivation settings, its phonotactic
policy, any language-specific helpers (orthography, reading aloud), and its
typology profile. The core only ever reads a pack's files: it never writes to
them, so a pack can point at a language's live working files safely.
"""
import csv
import os
import importlib.util
import json
import pathlib

from .lexicon import Deriver, piecewise
from .phonotactics import Phonotactics
from .sca import SoundLaws

PACKS = pathlib.Path(__file__).resolve().parent.parent / "packs"
REPO = PACKS.parent.parent
LANGUAGES = pathlib.Path(os.environ.get("UTP_LANGUAGES", REPO / "languages"))     # languages made with utp.py new


def _load_function(path, name):
    spec = importlib.util.spec_from_file_location(f"utp_pack_{path.stem}_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, name)


class Pack:
    def __init__(self, name_or_dir):
        d = pathlib.Path(name_or_dir)
        if not (d.is_dir() and (d / "pack.json").exists()):
            d = next((base / str(name_or_dir) for base in (PACKS, LANGUAGES)
                      if (base / str(name_or_dir) / "pack.json").exists()), PACKS / str(name_or_dir))
        self.dir = d.resolve()
        self.id = self.dir.name
        self.meta = json.loads((self.dir / "pack.json").read_text())
        self.name = self.meta["name"]
        self.root = (self.dir / self.meta.get("root", ".")).resolve()
        self.laws = SoundLaws(json.loads(self.path("sound_laws").read_text()))
        self.phonotactics = Phonotactics(self.laws.proto, self.meta.get("phonotactics"))
        self._helpers = {}

    def path(self, key):
        return (self.root / self.meta["files"][key]).resolve()

    def helper(self, key):
        """A language-specific function named in pack.json "helpers" (e.g. orthography)."""
        if key not in self._helpers:
            h = self.meta.get("helpers", {}).get(key)
            self._helpers[key] = _load_function(self.root / h["module"], h["function"]) if h else None
        return self._helpers[key]

    def rows(self, key="lexicon"):
        with open(self.path(key), newline="") as f:
            return list(csv.DictReader(f))

    def deriver(self, rows=None):
        d = Deriver(self.laws, self.meta["derivation"], self.helper("orthography"))
        d.index(rows if rows is not None else self.rows())
        return d

    def spell(self, form):
        """A raw standard-branch form in the pack's spelling standard."""
        fn = self.helper("orthography")
        return piecewise(fn, form) if fn else form

    @property
    def home(self):
        """The language's own folder: where its Lab, course, docs and batches live."""
        return (self.root / self.meta.get("home", ".")).resolve() if "home" in self.meta else self.dir

    @property
    def buildable(self):
        return "build" in self.meta

    def learning(self, key):
        """Path of the language's Lab or course page (pack.json "learning"), or None."""
        rel = self.meta.get("learning", {}).get(key)
        return (self.home / rel).resolve() if rel else None

    @property
    def typology(self):
        return self.meta.get("typology", {})


def available():
    """Every pack: the engine's own (utp/packs) and the languages made with utp.py new (languages/)."""
    names = {p.parent.name for p in PACKS.glob("*/pack.json")} | {p.parent.name for p in LANGUAGES.glob("*/pack.json")}
    return sorted(names)
