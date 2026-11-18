"""UTP speech: speak any pack's words through a local Kokoro-FastAPI server.

Kokoro reads English spelling as English, so a Vulcan word typed as text comes out
wrong. Instead the UTP sends phonemes: the pack's own reading of the word (Vulcan's
IPA), mapped onto the symbols Kokoro can voice, to Kokoro-FastAPI's
POST /dev/generate_from_phonemes. Human languages go through the ordinary
OpenAI-compatible POST /v1/audio/speech with a voice for that language.

Everything here is optional and stdlib-only: with no server running, phonemes()
still works (and `utp.py say --dry` shows what would be sent).

  UTP_KOKORO_URL   default http://localhost:8880
"""
import json
import os
import pathlib
import urllib.request

VOCAB = set(json.loads((pathlib.Path(__file__).with_name("kokoro_vocab.json")).read_text())["symbols"])
# Kokoro's voices for the languages it speaks (Kokoro-82M v1.0); any other voice name can be passed
LANGUAGE_VOICES = {"english": "af_heart", "british english": "bf_emma", "spanish": "ef_dora", "french": "ff_siwis",
                   "hindi": "hf_alpha", "italian": "if_sara", "japanese": "jf_alpha", "portuguese": "pf_dora",
                   "chinese": "zf_xiaobei", "mandarin": "zf_xiaobei"}
# IPA symbols Kokoro lacks, and the nearest it can say. A pack's "speech" -> "map" overrides these.
DEFAULT_MAP = {"tʃ": "ʧ", "dʒ": "ʤ", "ts": "ʦ", "dz": "ʣ", "ɬ": "ʃl", "ʍ": "hw", "ɡ": "ɡ", "g": "ɡ",
               "ʼ": "ʔ", "'": "ʔ", "-": " "}


def _longest(text, table):
    keys = sorted(table, key=len, reverse=True)
    out, i = [], 0
    while i < len(text):
        for k in keys:
            if text.startswith(k, i):
                out.append(table[k])
                i += len(k)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def phonemes(pack, form):
    """(phoneme string for Kokoro, symbols that had to be dropped)."""
    cfg = pack.meta.get("speech", {}) if pack else {}
    reading = pack.helper("reading") if pack else None
    if cfg.get("from", "reading" if reading else "spelling") == "reading" and reading:
        words = []
        for w in form.split():
            core, punct = w.rstrip(".,?!:;"), w[len(w.rstrip(".,?!:;")):]   # Kokoro uses ? and . for intonation
            pieces = [p for p in core.split("-") if p]
            if all(reading(p) for p in pieces):
                words.append(reading(core) + punct)
            else:                                   # names the reading skips (Saavik): read from the spelling
                words.append("".join(reading(p) or _longest(p.lower(), cfg.get("sounds", {})) for p in pieces) + punct)
        ipa = " ".join(words)
    else:
        ipa = _longest(form.lower(), cfg.get("sounds", {}))
    ipa = _longest(ipa, {**DEFAULT_MAP, **cfg.get("map", {})})
    if cfg.get("stress", "first") == "first":
        ipa = " ".join("ˈ" + w if w and w[0] != "ˈ" else w for w in ipa.split(" "))
    kept = "".join(ch for ch in ipa if ch in VOCAB)
    dropped = sorted({ch for ch in ipa if ch not in VOCAB})
    return kept, dropped


class Kokoro:
    def __init__(self, url=None, timeout=60):
        self.url = (url or os.environ.get("UTP_KOKORO_URL", "http://localhost:8880")).rstrip("/")
        self.timeout = timeout

    def _post(self, path, payload):
        req = urllib.request.Request(self.url + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return r.read()

    def available(self):
        try:
            urllib.request.urlopen(self.url + "/v1/audio/voices", timeout=3).read()
            return True
        except Exception:
            return False

    def say_phonemes(self, ph, voice="am_michael"):
        """WAV bytes for a phoneme string (Kokoro-FastAPI /dev/generate_from_phonemes)."""
        return self._post("/dev/generate_from_phonemes", {"phonemes": ph, "voice": voice})

    def say_text(self, text, voice="af_heart"):
        """WAV bytes for ordinary text in a language Kokoro speaks (/v1/audio/speech)."""
        return self._post("/v1/audio/speech", {"model": "kokoro", "input": text, "voice": voice,
                                               "response_format": "wav"})

    def say_word(self, pack, form, voice=None):
        ph, dropped = phonemes(pack, form)
        return self.say_phonemes(ph, voice or pack.meta.get("speech", {}).get("voice", "am_michael")), ph, dropped
