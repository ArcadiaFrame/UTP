"""Web search through your own SearXNG, and pages fetched into a language's private library.

  search(query)        results from SearXNG's JSON API: [{title, url, content, engine, tier}]
  suggest_tier(url)    a first guess at a source's tier from its site (you can always change it)
  fetch(url)           (title, text) of a page; MediaWiki sites (Memory Alpha, Memory Beta, Wikipedia,
                       fandom wikis) are read through their API, which gives the article without menus
  test(url)            does SearXNG answer, and with JSON?

SearXNG answers programs only when JSON is on in its settings.yml:
    search:
      formats: [html, json]
Set the address in Settings > Web search, or UTP_SEARXNG. Nothing here runs unless you search.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from .library import html_text

UA = "UTP-workshop/1 (+https://github.com/ArcadiaFrame/UTP)"
MAX_BYTES = 6 * 1024 * 1024
TIER_SITES = [
    ("canon", ("memory-alpha.fandom.com", "memory-alpha.org", "startrek.com", "chakoteya.net", "st-minutiae.com",
               "trekcore.com")),
    ("licensed", ("memory-beta.fandom.com", "modiphius.net", "simonandschuster.com")),
    ("fan", ("fandom.com", "fanlore.org", "archiveofourown.org", "fanfiction.net", "reddit.com", "trekbbs.com",
             "frathwiki.com", "blogspot.com", "tumblr.com", "worldanvil.com")),
    ("science", ("wikipedia.org", "wiktionary.org", "wals.info", "glottolog.org", "doi.org", "jstor.org",
                 "ncbi.nlm.nih.gov", "sciencedirect.com", "springer.com", "nature.com", "arxiv.org", "britannica.com",
                 ".edu", "plos.org", "pnas.org", "cambridge.org", "oup.com")),
]


class SearchError(Exception):
    pass


def address(cfg=None):
    from . import config as C
    return (os.environ.get("UTP_SEARXNG") or (cfg or C.load()).get("search", {}).get("searxng") or "").rstrip("/")


def suggest_tier(url):
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    for tier, sites in TIER_SITES:
        if any(host == s or host.endswith("." + s) or (s.startswith(".") and host.endswith(s)) for s in sites):
            return tier
    return "fan"


def _get(url, timeout=20, accept="*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise SearchError(f"{url}: larger than {MAX_BYTES // 1024 // 1024} MB")
            return data, r.headers.get("Content-Type", ""), r.geturl()
    except urllib.error.HTTPError as e:
        hint = " (the site refuses programs: open it in your browser, save the page, and drop the file into Sources)" \
            if e.code in (401, 403, 429, 503) else ""
        raise SearchError(f"{url} answered {e.code}{hint}") from None
    except (urllib.error.URLError, OSError) as e:
        raise SearchError(f"no answer from {url}: {getattr(e, 'reason', e)}") from None


def search(query, n=10, url=None, categories="general", page=1):
    base = (url or address()).rstrip("/")
    if not base:
        raise SearchError("no SearXNG address: set it in Settings > Web search")
    q = urllib.parse.urlencode({"q": query, "format": "json", "categories": categories, "pageno": page})
    data, ctype, _ = _get(f"{base}/search?{q}", accept="application/json")
    try:
        out = json.loads(data)
    except ValueError:
        raise SearchError("SearXNG answered, but not with JSON: add json to search: formats in its settings.yml") from None
    seen, res = set(), []
    for r in out.get("results", []):
        u = r.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        res.append({"title": r.get("title") or u, "url": u, "content": (r.get("content") or "")[:400],
                    "engine": r.get("engine") or ", ".join(r.get("engines", [])), "tier": suggest_tier(u)})
        if len(res) >= n:
            break
    return res


def test(url=None):
    try:
        res = search("language", n=3, url=url)
        return {"ok": True, "results": len(res), "url": (url or address())}
    except SearchError as e:
        return {"ok": False, "problem": str(e), "url": (url or address())}


WIKI = re.compile(r"^/(?:wiki|w)/(.+)$")


def _mediawiki(url):
    """(title, text) through a MediaWiki site's api.php, or None if the page is not a wiki article."""
    u = urllib.parse.urlparse(url)
    m = WIKI.match(u.path)
    if not m:
        return None
    page = urllib.parse.unquote(m.group(1))
    api = f"{u.scheme}://{u.netloc}/{'w/' if u.netloc.endswith('wikipedia.org') else ''}api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": page, "prop": "text", "format": "json", "redirects": 1, "disabletoc": 1})
    try:
        data, _, _ = _get(api, accept="application/json")
        j = json.loads(data)["parse"]
    except (SearchError, ValueError, KeyError):
        return None
    markup = j["text"]["*"] if isinstance(j["text"], dict) else j["text"]
    markup = re.sub(r'<(table|div)[^>]*class="[^"]*(navbox|infobox|toc|mw-references|reflist|printfooter)[^"]*".*?</\1>',
                    "", markup, flags=re.S)
    return j.get("title") or page.replace("_", " "), html_text(markup)


def fetch(url):
    """(title, text, final url) for a web page."""
    if not re.match(r"^https?://", url or ""):
        raise SearchError("only http and https addresses")
    wiki = _mediawiki(url)
    if wiki and wiki[1].strip():
        return wiki[0], _tidy(wiki[1]), url
    data, ctype, final = _get(url)
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        import tempfile
        from .library import read_text
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(data)
            f.flush()
            return urllib.parse.unquote(url.rsplit("/", 1)[-1]), _tidy(read_text(f.name)), final
    text = data.decode(_charset(ctype) or "utf-8", "replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    body = re.search(r"<(main|article)[^>]*>(.*?)</\1>", text, re.S | re.I)
    content = html_text(body.group(2) if body and len(body.group(2)) > 500 else text) if "html" in ctype or "<html" in text[:500].lower() else text
    return (html_text(title.group(1)).strip() if title else final), _tidy(content), final


def _charset(ctype):
    m = re.search(r"charset=([\w-]+)", ctype or "")
    return m.group(1) if m else None


def _tidy(text):
    text = re.sub(r"\[edit\]|\[\d+\]", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def add_url(lib, url, tier=None, title=None):
    """Fetch a page into a library. Returns (citation id, passages, title)."""
    t, text, final = fetch(url)
    if len(text) < 80:
        raise SearchError(f"{url}: almost no text on the page (it may need a browser: save it and drop the file in)")
    doc, n = lib.add_text(text, title or t, tier or suggest_tier(final), "web", url=final)
    return f"{lib.prefix}{doc}", n, title or t
