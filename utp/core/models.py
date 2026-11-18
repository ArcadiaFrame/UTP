"""One model connection for the whole UTP: Anthropic, OpenAI-compatible servers, and Ollama.

Every tool (expand, propose, the tutor, the app's chat, the Lab's tutor panel) talks to a
model through Model, so switching between a hosted model and a local one is one setting.

  provider   url (default)                     key
  ollama     http://localhost:11434/v1         none          local, offline
  openai     https://api.openai.com/v1         required      also LM Studio (http://localhost:1234/v1),
                                                             llama.cpp, vLLM, Open WebUI (…/api)
  anthropic  https://api.anthropic.com         required      Claude

Settings (utp/core/config.py, ~/.utp/config.json) hold any number of connections, and say which one
chats and which one builds. Environment variables override them: UTP_LLM_PROVIDER, UTP_LLM_URL,
UTP_LLM_MODEL, UTP_LLM_KEY (or ANTHROPIC_API_KEY / OPENAI_API_KEY).
Standard library only.
"""
import http.client
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from . import config as C

PROVIDERS = C.PROVIDERS
ANTHROPIC_VERSION = "2023-06-01"
THINK = re.compile(r"<think>.*?</think>", re.S)


class ModelError(Exception):
    pass


def load_config():
    return C.load()


def save_config(cfg):
    """Older form {provider, url, model, keys: {provider: key}}: set the connection the roles use."""
    current = C.load()
    conn = C.connection(role="chat", cfg=current)
    prov = cfg.get("provider") or conn["provider"]
    same = prov == conn["provider"]
    new = {"id": conn["id"] if same else None, "name": conn["name"] if same else PROVIDERS[prov]["label"], "provider": prov,
           "url": cfg.get("url") or (conn["url"] if same else ""), "model": cfg.get("model") or (conn["model"] if same else "")}
    key = (cfg.get("keys") or {}).get(prov)
    cid = C.upsert_connection(new, key=key)
    C.update({"roles": {"chat": cid, "build": cid}})
    return public_config()


def public_config():
    return C.public()


class Model:
    def __init__(self, url=None, model=None, key=None, provider=None, timeout=300, connection=None, role="chat"):
        env = os.environ
        c = C.connection(connection, role)
        self.connection = c.get("id", "")
        self.provider = provider or env.get("UTP_LLM_PROVIDER") or (
            "anthropic" if "anthropic.com" in (url or env.get("UTP_LLM_URL", "")) else None) or c["provider"]
        if self.provider not in PROVIDERS:
            raise ModelError(f"unknown provider '{self.provider}' (use {', '.join(PROVIDERS)})")
        d = PROVIDERS[self.provider]
        same = self.provider == c["provider"]              # a connection's url, model and key belong to its provider
        self.url = (url or env.get("UTP_LLM_URL") or (c.get("url") if same else None) or d["url"]).rstrip("/")
        self.model = model or env.get("UTP_LLM_MODEL") or (c.get("model") if same else None) or d["model"]
        self.key = (key or env.get("UTP_LLM_KEY") or env.get(f"{self.provider.upper()}_API_KEY")
                    or (c.get("key") if same else "") or "")
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

    def needs_key(self):
        return C.needs_key(self.provider, self.url)

    def available(self):
        if self.needs_key() and not self.key:
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
