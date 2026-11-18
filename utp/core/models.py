"""One model connection for the whole UTP: Anthropic, OpenAI-compatible servers, and Ollama.

Every tool (expand, propose, the tutor, the app's chat, the Lab's tutor panel) talks to a
model through Model, so switching between a hosted model and a local one is one setting.

  provider   url (default)                     key
  ollama     http://localhost:11434/v1         none          local, offline
  openai     https://api.openai.com/v1         required      also LM Studio (http://localhost:1234/v1),
                                                             llama.cpp, vLLM, Open WebUI (…/api)
  anthropic  https://api.anthropic.com         required      Claude

Settings are read in this order, first found wins:
  1. arguments to Model(...)
  2. environment: UTP_LLM_PROVIDER, UTP_LLM_URL, UTP_LLM_MODEL, UTP_LLM_KEY
     (ANTHROPIC_API_KEY / OPENAI_API_KEY are used as the key for their provider)
  3. ~/.utp/config.json  {"provider": ..., "url": ..., "model": ..., "keys": {"anthropic": ..., "openai": ...}}
     (the app's Settings screen writes this file, readable only by you)
  4. the defaults: Ollama on this machine
Standard library only.
"""
import http.client
import json
import os
import pathlib
import re
import urllib.error
import urllib.request

CONFIG = pathlib.Path(os.environ.get("UTP_HOME", pathlib.Path.home() / ".utp")) / "config.json"
PROVIDERS = {
    "ollama": {"url": "http://localhost:11434/v1", "model": "qwen3.5:9b", "key": False},
    "openai": {"url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "key": True},
    "anthropic": {"url": "https://api.anthropic.com", "model": "claude-sonnet-5-5", "key": True},
}
ANTHROPIC_VERSION = "2023-06-01"
THINK = re.compile(r"<think>.*?</think>", re.S)


class ModelError(Exception):
    pass


def load_config():
    try:
        return json.loads(CONFIG.read_text())
    except Exception:
        return {}


def save_config(cfg):
    """Write the settings file, readable only by its owner (it may hold API keys)."""
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    old = load_config()
    keys = {**old.get("keys", {}), **{k: v for k, v in cfg.get("keys", {}).items() if v}}
    for k, v in cfg.get("keys", {}).items():
        if v == "":                                   # an explicit empty string removes a key
            keys.pop(k, None)
    merged = {**old, **{k: v for k, v in cfg.items() if k != "keys"}, "keys": keys}
    CONFIG.write_text(json.dumps(merged, indent=1))
    try:
        os.chmod(CONFIG, 0o600)
    except OSError:
        pass
    return merged


def public_config():
    """Settings for display: which keys are set, never the keys themselves."""
    m = Model()
    cfg = load_config()
    return {"provider": m.provider, "url": m.url, "model": m.model,
            "keys": {p: bool(cfg.get("keys", {}).get(p) or os.environ.get(f"{p.upper()}_API_KEY"))
                     for p in ("anthropic", "openai")},
            "providers": PROVIDERS}


class Model:
    def __init__(self, url=None, model=None, key=None, provider=None, timeout=300):
        cfg = load_config()
        env = os.environ
        self.provider = (provider or env.get("UTP_LLM_PROVIDER") or cfg.get("provider")
                         or ("anthropic" if "anthropic.com" in (url or env.get("UTP_LLM_URL", "")) else "ollama"))
        if self.provider not in PROVIDERS:
            raise ModelError(f"unknown provider '{self.provider}' (use {', '.join(PROVIDERS)})")
        d = PROVIDERS[self.provider]
        same = cfg.get("provider", self.provider) == self.provider     # a saved url/model belongs to its provider
        self.url = (url or env.get("UTP_LLM_URL") or (cfg.get("url") if same else None) or d["url"]).rstrip("/")
        self.model = model or env.get("UTP_LLM_MODEL") or (cfg.get("model") if same else None) or d["model"]
        self.key = (key or env.get("UTP_LLM_KEY") or env.get(f"{self.provider.upper()}_API_KEY")
                    or cfg.get("keys", {}).get(self.provider, ""))
        self.timeout = timeout

    def __repr__(self):
        return f"Model({self.provider}, {self.model} @ {self.url})"

    # ---------- transport ----------
    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.provider == "anthropic":
            h.update({"x-api-key": self.key, "anthropic-version": ANTHROPIC_VERSION})
        elif self.key:
            h["Authorization"] = f"Bearer {self.key}"
        return h

    def _open(self, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.url + path, data=data, headers=self._headers())
        try:
            return urllib.request.urlopen(req, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            raise ModelError(f"{self.provider} answered {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise ModelError(f"no answer from {self.url}: {e.reason}") from None
        except (OSError, http.client.HTTPException) as e:
            raise ModelError(f"no answer from {self.url}: {e}") from None

    def _json(self, path, payload=None):
        with self._open(path, payload) as r:
            return json.loads(r.read())

    # ---------- what the tools use ----------
    def models(self):
        """Model names the server offers."""
        out = self._json("/v1/models" if self.provider == "anthropic" else "/models")
        return [m.get("id") or m.get("name") for m in out.get("data", out.get("models", []))]

    def available(self):
        if PROVIDERS[self.provider]["key"] and not self.key:
            return False
        try:
            self.models()
            return True
        except Exception:
            return False

    def _anthropic_body(self, messages, temperature, max_tokens, stream=False):
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        turns = []
        for m in messages:
            if m["role"] == "system":
                continue
            if turns and turns[-1]["role"] == m["role"]:          # the Messages API wants turns to alternate
                turns[-1]["content"] += "\n\n" + m["content"]
            else:
                turns.append({"role": m["role"], "content": m["content"]})
        body = {"model": self.model, "max_tokens": max_tokens, "messages": turns, "temperature": temperature}
        if system:
            body["system"] = system
        if stream:
            body["stream"] = True
        return body

    def chat(self, messages, json_mode=False, temperature=0.3, max_tokens=4096):
        """messages: [{"role": "system"|"user"|"assistant", "content": text}] -> reply text."""
        if self.provider == "anthropic":
            out = self._json("/v1/messages", self._anthropic_body(messages, temperature, max_tokens))
            text = "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")
        else:
            payload = {"model": self.model, "messages": messages, "temperature": temperature, "stream": False}
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            out = self._json("/chat/completions", payload)
            text = out["choices"][0]["message"]["content"] or ""
        return THINK.sub("", text).strip()               # reasoning models put their thinking in <think>

    def stream(self, messages, temperature=0.5, max_tokens=4096):
        """Yield the reply in pieces as the model writes it."""
        if self.provider == "anthropic":
            r = self._open("/v1/messages", self._anthropic_body(messages, temperature, max_tokens, stream=True))
        else:
            r = self._open("/chat/completions", {"model": self.model, "messages": messages,
                                                 "temperature": temperature, "stream": True})
        thinking = False
        with r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    ev = json.loads(data)
                except ValueError:
                    continue
                if self.provider == "anthropic":
                    if ev.get("type") == "error":
                        raise ModelError(ev.get("error", {}).get("message", "stream error"))
                    piece = ev.get("delta", {}).get("text", "") if ev.get("type") == "content_block_delta" else ""
                else:
                    ch = (ev.get("choices") or [{}])[0]
                    piece = (ch.get("delta") or {}).get("content") or ""
                if not piece:
                    continue
                if "<think>" in piece:                        # hide a local reasoning model's thinking
                    thinking = True
                    piece = piece.split("<think>")[0]
                if thinking:
                    if "</think>" not in piece:
                        continue
                    thinking, piece = False, piece.split("</think>", 1)[1]
                if piece:
                    yield piece

    def chat_json(self, messages):
        text = self.chat(messages, json_mode=True, temperature=0.2)
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except ValueError:
            return {}
