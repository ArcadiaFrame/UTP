"""UTP settings: one file, read by every tool, the app and the desktop shell.

~/.utp/config.json (or $UTP_HOME/config.json), readable only by its owner because it can hold API keys.

  connections   models you can use: {id, name, provider (ollama | openai | anthropic), url, model}
  secrets       API keys, by connection id (never sent to a page; the app only learns whether one is set)
  roles         which connection does what: "chat" (the app's chat, Lab tutor, tutor.py) and
                "build" (expand, sentences, topics, propose, curate)
  speech        Kokoro-FastAPI address and default voice
  paths         where languages are kept, and extra folders to show in the app's file list
  app           port, and whether starting the app opens a browser or the desktop window
  desktop       the Python the desktop window should run (blank: find it)

Environment variables still win, for scripts and tests: UTP_LLM_PROVIDER, UTP_LLM_URL, UTP_LLM_MODEL,
UTP_LLM_KEY (or ANTHROPIC_API_KEY / OPENAI_API_KEY), UTP_KOKORO_URL, UTP_LANGUAGES.
"""
import copy
import json
import os
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
PROVIDERS = {
    "ollama": {"label": "Ollama", "url": "http://localhost:11434/v1", "model": "qwen3.5:9b", "key": False},
    "openai": {"label": "OpenAI-compatible", "url": "https://api.openai.com/v1", "model": "gpt-4o-mini", "key": True},
    "anthropic": {"label": "Anthropic", "url": "https://api.anthropic.com", "model": "claude-sonnet-5-5", "key": True},
}
ROLES = {"chat": "Chat, the Lab's tutor and tutor.py", "build": "Growing languages: expand, sentences, topics, propose"}
DEFAULTS = {
    "version": 2,
    "connections": [{"id": "local", "name": "Ollama on this machine", "provider": "ollama",
                     "url": PROVIDERS["ollama"]["url"], "model": PROVIDERS["ollama"]["model"]}],
    "secrets": {},
    "roles": {"chat": "local", "build": "local"},
    "speech": {"url": "http://localhost:8880", "voice": ""},
    "paths": {"languages": "", "workspaces": []},
    "app": {"port": 8765, "open": "auto", "theme": "system",    # open: auto = the desktop window if installed, else the browser
            "layout": "auto", "year": 2371, "sounds": False,     # layout: auto, desktop, padd; year: for the stardate
            "palette": "amber-blue", "shape": "cut"},           # the Terminal theme: amber-blue, amber, blue; cut, square, rounded
    "library": {"embed_connection": "", "embed_model": ""},     # meaning-based search for sources (optional)
    "search": {"searxng": ""},                                  # your SearXNG, for finding sources on the web (optional)
    "desktop": {"python": ""},
}


def home():
    return pathlib.Path(os.environ.get("UTP_HOME") or pathlib.Path.home() / ".utp")


def path():
    return home() / "config.json"


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _migrate(old):
    """Version 1 kept one provider, url, model and keys by provider; make that a connection."""
    if "connections" in old or not any(k in old for k in ("provider", "url", "model", "keys")):
        return old
    prov = old.get("provider", "ollama")
    conns, secrets = [], {}
    for p, key in (old.get("keys") or {}).items():
        if p in PROVIDERS and p != prov and key:
            conns.append({"id": p, "name": PROVIDERS[p]["label"], "provider": p, "url": PROVIDERS[p]["url"],
                          "model": PROVIDERS[p]["model"]})
            secrets[p] = key
    main = {"id": "default", "name": PROVIDERS.get(prov, {}).get("label", prov), "provider": prov,
            "url": old.get("url") or PROVIDERS.get(prov, {}).get("url", ""),
            "model": old.get("model") or PROVIDERS.get(prov, {}).get("model", "")}
    if (old.get("keys") or {}).get(prov):
        secrets["default"] = old["keys"][prov]
    new = {k: v for k, v in old.items() if k not in ("provider", "url", "model", "keys")}
    new.update(connections=[main] + conns, secrets=secrets, roles={"chat": "default", "build": "default"})
    return new


def load():
    try:
        raw = json.loads(path().read_text())
    except Exception:
        raw = {}
    cfg = _merge(DEFAULTS, _migrate(raw))
    if raw.get("connections"):
        cfg["connections"] = raw["connections"]          # a saved list replaces the default one, never merges
    ids = [c["id"] for c in cfg["connections"]]
    for role in ROLES:
        if cfg["roles"].get(role) not in ids:
            cfg["roles"][role] = ids[0] if ids else ""
    return cfg


def save(cfg):
    path().parent.mkdir(parents=True, exist_ok=True)
    tmp = path().with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=1, ensure_ascii=False))
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    tmp.replace(path())
    return cfg


def needs_key(provider, url):
    """Anthropic always needs a key; an OpenAI-compatible server does unless it is on this machine or the home
    network (LM Studio, llama.cpp, vLLM and Open WebUI at home usually take none); Ollama never does."""
    import urllib.parse
    if not PROVIDERS.get(provider, {}).get("key"):
        return False
    if provider == "anthropic":
        return True
    host = (urllib.parse.urlparse(url or "").hostname or "").lower()
    if host in ("localhost", "::1") or "." not in host or host.endswith((".local", ".lan", ".home", ".internal")):
        return False
    return not (host.startswith(("127.", "10.", "192.168.")) or any(host.startswith(f"172.{n}.") for n in range(16, 32)))


def public(cfg=None):
    """Settings safe to show: every connection with key_set true/false, never the key."""
    cfg = copy.deepcopy(cfg or load())
    secrets = cfg.pop("secrets", {})
    for c in cfg["connections"]:
        c["key_set"] = bool(secrets.get(c["id"]))
        c["needs_key"] = needs_key(c["provider"], c["url"])
    cfg["providers"], cfg["role_labels"], cfg["config_path"] = PROVIDERS, ROLES, str(path())
    cfg["languages_dir"] = str(languages_dir(cfg))
    cfg["env_overrides"] = sorted(k for k in ("UTP_SEARXNG", "UTP_LLM_PROVIDER", "UTP_LLM_URL", "UTP_LLM_MODEL", "UTP_LLM_KEY",
                                              "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "UTP_KOKORO_URL", "UTP_LANGUAGES")
                                  if os.environ.get(k))
    return cfg


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:40] or "connection"


def upsert_connection(conn, key=None, cfg=None):
    """Add or change a connection. key: None leaves it, "" removes it, text sets it."""
    cfg = cfg or load()
    prov = conn.get("provider", "ollama")
    if prov not in PROVIDERS:
        raise ValueError(f"provider must be one of {', '.join(PROVIDERS)}")
    cid = conn.get("id") or slug(conn.get("name") or prov)
    existing = next((c for c in cfg["connections"] if c["id"] == cid), None)
    if not conn.get("id") and existing:                       # a new connection whose name is taken: number it
        n = 2
        while any(c["id"] == f"{cid}-{n}" for c in cfg["connections"]):
            n += 1
        cid, existing = f"{cid}-{n}", None
    clean = {"id": cid, "name": conn.get("name") or PROVIDERS[prov]["label"], "provider": prov,
             "url": (conn.get("url") or PROVIDERS[prov]["url"]).rstrip("/"), "model": conn.get("model") or PROVIDERS[prov]["model"]}
    if existing:
        existing.update(clean)
    else:
        cfg["connections"].append(clean)
    if key is not None:
        if key:
            cfg["secrets"][cid] = key
        else:
            cfg["secrets"].pop(cid, None)
    save(cfg)
    return cid


def delete_connection(cid, cfg=None):
    cfg = cfg or load()
    if len(cfg["connections"]) <= 1:
        raise ValueError("keep at least one connection")
    cfg["connections"] = [c for c in cfg["connections"] if c["id"] != cid]
    cfg["secrets"].pop(cid, None)
    for role, v in cfg["roles"].items():
        if v == cid:
            cfg["roles"][role] = cfg["connections"][0]["id"]
    save(cfg)


def connection(cid=None, role="chat", cfg=None):
    """The connection to use (with its key), by id or by role."""
    cfg = cfg or load()
    cid = cid or cfg["roles"].get(role)
    c = next((c for c in cfg["connections"] if c["id"] == cid), None) or (cfg["connections"] or [None])[0]
    if not c:
        return {"id": "", "provider": "ollama", "url": PROVIDERS["ollama"]["url"], "model": PROVIDERS["ollama"]["model"], "key": ""}
    return {**c, "key": cfg["secrets"].get(c["id"], "")}


def update(patch):
    """Change the plain settings: roles, speech, paths, app, desktop (connections have their own calls)."""
    cfg = load()
    for section in ("roles", "speech", "paths", "app", "desktop", "library", "search"):
        if section in patch and isinstance(patch[section], dict):
            cfg[section] = _merge(cfg[section], patch[section])
    ws = cfg["paths"].get("workspaces", [])
    cfg["paths"]["workspaces"] = [w for w in ws if isinstance(w, dict) and w.get("path")]
    save(cfg)
    return cfg


def languages_dir(cfg=None):
    env = os.environ.get("UTP_LANGUAGES")
    if env:
        return pathlib.Path(env).expanduser()
    p = (cfg or load())["paths"].get("languages")
    return pathlib.Path(p).expanduser() if p else REPO / "languages"


def workspaces(cfg=None):
    """Extra folders shown in the app: [{name, path}] with unique, path-safe names."""
    out, seen = [], set()
    for w in (cfg or load())["paths"].get("workspaces", []):
        p = pathlib.Path(w["path"]).expanduser()
        name = slug(w.get("name") or p.name)
        while name in seen:
            name += "-2"
        seen.add(name)
        out.append({"name": name, "label": w.get("name") or p.name, "path": p})
    return out


def kokoro_url():
    return os.environ.get("UTP_KOKORO_URL") or load()["speech"].get("url") or "http://localhost:8880"
