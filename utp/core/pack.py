"""UTP language packs.

A pack is a folder with one pack.json. It names the language family's data files
(paths relative to the pack's root), its derivation settings, its phonotactic
policy, any language-specific helpers (orthography, reading aloud), and its
typology profile. The core only ever reads a pack's files: it never writes to
them, so a pack can point at a language's live working files safely.
"""
import csv
import importlib.util
import json
import pathlib

from .lexicon import Deriver, piecewise
from .phonotactics import Phonotactics
from .sca import SoundLaws

PACKS = pathlib.Path(__file__).resolve().parent.parent / "packs"


def _load_function(path, name):
    spec = importlib.util.spec_from_file_location(f"utp_pack_{path.stem}_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, name)


class Pack:
    def __init__(self, name_or_dir):
        d = pathlib.Path(name_or_dir)
        self.dir = (d if d.is_dir() else PACKS / str(name_or_dir)).resolve()
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
    def typology(self):
        return self.meta.get("typology", {})


def available():
    return sorted(p.parent.name for p in PACKS.glob("*/pack.json"))
