"""Download the inputs.

1. The Retraction Watch database, published openly by Crossref (67 MB CSV).
2. Every OpenAlex work flagged as retracted with at least 10 citations, with its
   citations per year (about 150 API calls).
3. A random pool of non-retracted articles for each publication year, in four
   citation bands, to draw matched controls from, plus the population size of each
   band so the sample can be weighted back (about 170 API calls).

Usage: python fetch.py [rw|retracted|controls|all]
"""
import json
import sys
from pathlib import Path

import pandas as pd
import requests

import openalex as oa

DATA = Path(__file__).parent / "data"
RW_URL = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv"
SELECT = "id,doi,title,publication_year,type,cited_by_count,counts_by_year,primary_topic,primary_location"
CONTROL_YEARS = range(2000, 2023)
BANDS = [("10-49", 2), ("50-199", 2), ("200-999", 2), (">999", 1)]  # (cited_by_count, pages)


def fetch_rw():
    out = DATA / "rw.csv"
    if out.exists():
        print("rw.csv already present")
        return
    r = requests.get(RW_URL, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"rw.csv {len(r.content) / 1e6:.0f} MB")


def flatten(w):
    topic = w.get("primary_topic") or {}
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return {
        "work_id": oa.short_id(w["id"]),
        "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower() or None,
        "title": w.get("title"),
        "pub_year": w.get("publication_year"),
        "type": w.get("type"),
        "cited_by_count": w.get("cited_by_count"),
        "field": (topic.get("field") or {}).get("display_name"),
        "domain": (topic.get("domain") or {}).get("display_name"),
        "source_id": oa.short_id(src.get("id")),
        "source": src.get("display_name"),
        "counts": json.dumps({c["year"]: c["cited_by_count"] for c in w.get("counts_by_year", [])}),
    }


def fetch_retracted():
    rows = [flatten(w) for w in oa.cursor_pages("is_retracted:true,cited_by_count:>9", SELECT)]
    df = pd.DataFrame(rows).drop_duplicates("work_id")
    df.to_parquet(DATA / "retracted_openalex.parquet", index=False)
    print(f"retracted works: {len(df):,}")


def fetch_controls():
    rows = []
    for year in CONTROL_YEARS:
        for band, pages in BANDS:
            f = f"publication_year:{year},is_retracted:false,type:article|review,cited_by_count:{band}"
            for page in range(1, pages + 1):
                d = oa.get("/works", filter=f, select=SELECT, sample=200 * pages,
                           seed=year, per_page=200, page=page)
                rows += [flatten(w) | {"band": band} for w in d["results"]]
        print(f"controls {year}: {len(rows):,} so far, budget left ${oa.state['remaining_usd']}")
    df = pd.DataFrame(rows).drop_duplicates("work_id")
    df.to_parquet(DATA / "controls_openalex.parquet", index=False)
    print(f"control pool: {len(df):,}")
    # how many papers each band holds in the population, to weight the sample back
    pop = []
    for band, _ in BANDS:
        f = f"is_retracted:false,type:article|review,cited_by_count:{band}"
        d = oa.get("/works", filter=f, group_by="publication_year")
        pop += [{"pub_year": int(g["key"]), "band": band, "population": g["count"]}
                for g in d["group_by"] if g["key"].isdigit() and int(g["key"]) in CONTROL_YEARS]
    pd.DataFrame(pop).to_csv(DATA / "control_population.csv", index=False)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    try:
        if step in ("rw", "all"):
            fetch_rw()
        if step in ("retracted", "all"):
            fetch_retracted()
        if step in ("controls", "all"):
            fetch_controls()
    except oa.BudgetExhausted as e:
        print(e)
        sys.exit(2)
    print(f"API calls this run: {oa.state['calls']}, budget left: ${oa.state['remaining_usd']}")
