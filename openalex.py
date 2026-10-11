"""Small OpenAlex client: polite, cached, and aware of the daily budget.

Without a key OpenAlex allows about $0.10 of calls a day (1,000 list calls). Set
OPENALEX_API_KEY to raise that. Every response is cached on disk by URL, so a rerun
after the budget resets picks up where the last one stopped.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import requests

BASE = "https://api.openalex.org"
CACHE = Path(__file__).parent / "data" / "cache"
MAILTO = os.environ.get("OPENALEX_MAILTO", "")
API_KEY = os.environ.get("OPENALEX_API_KEY", "")


class BudgetExhausted(RuntimeError):
    pass


_session = requests.Session()
state = {"calls": 0, "remaining_usd": None}


def _key(path, params):
    blob = path + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha1(blob.encode()).hexdigest()


def get(path, **params):
    """GET an OpenAlex endpoint, returning parsed JSON. Cached forever by URL."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{_key(path, params)}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    q = dict(params)
    if MAILTO:
        q["mailto"] = MAILTO
    if API_KEY:
        q["api_key"] = API_KEY
    for attempt in range(6):
        r = _session.get(BASE + path, params=q, timeout=60)
        rem = r.headers.get("X-RateLimit-Remaining-USD")
        if rem is not None:
            state["remaining_usd"] = float(rem)
        if r.status_code == 429:
            if state["remaining_usd"] is not None and state["remaining_usd"] < 0.0002:
                raise BudgetExhausted("OpenAlex daily budget used up; rerun after it resets")
            time.sleep(2 ** attempt)
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        state["calls"] += 1
        data = r.json()
        f.write_text(json.dumps(data), encoding="utf-8")
        return data
    raise RuntimeError(f"OpenAlex kept failing for {path} {params}")


def cursor_pages(filter_, select, per_page=200):
    """Yield every result for a filter, paging with a cursor."""
    cursor = "*"
    while cursor:
        d = get("/works", filter=filter_, select=select, per_page=per_page, cursor=cursor)
        yield from d["results"]
        cursor = d["meta"].get("next_cursor")
        if not d["results"]:
            break


def short_id(url):
    return url.rsplit("/", 1)[-1] if url else None
