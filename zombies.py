"""The ranked list: retracted papers still being cited, and who cites them.

Takes every paper retracted by 2022 (so at least three full years have passed), ranks
by citations received in 2025, and for the top TOP asks OpenAlex for two things:
  * every citing work grouped by year, back to publication (OpenAlex's per-year counts
    stop at 2012)
  * the citing works whose title or abstract mentions retraction ("retract*"), which
    are papers that know what they are citing: studies of retraction, commentaries,
    replications. Everything else is at best unflagged in the abstract.
Two API calls per paper.

Writes tables/top_zombies.csv and out/zombie_history.json.
"""
import json
from pathlib import Path

import pandas as pd

import openalex as oa

ROOT = Path(__file__).parent
TOP = 150
LAST = 2025


def by_year(work_id, extra=""):
    f = f"cites:{work_id}" + (f",{extra}" if extra else "")
    d = oa.get("/works", filter=f, group_by="publication_year")
    return {int(g["key"]): g["count"] for g in d["group_by"] if g["key"].isdigit()}


def main():
    papers = pd.read_parquet(ROOT / "data" / "papers.parquet")
    cand = papers[papers.ret_year <= LAST - 3].sort_values(["c2025", "cited_by_count"], ascending=False).head(TOP)
    rows, hist = [], {}
    for r in cand.itertuples():
        try:
            allc = by_year(r.work_id)
            aware = by_year(r.work_id, "title_and_abstract.search.exact:retract*")
        except oa.BudgetExhausted as e:
            print(f"{e}; stopping after {len(rows)} papers")
            break
        post = sum(c for y, c in allc.items() if r.ret_year < y <= LAST)
        post_aware = sum(c for y, c in aware.items() if r.ret_year < y <= LAST)
        pre = sum(c for y, c in allc.items() if y < r.ret_year)
        peak_year = max(allc, key=allc.get) if allc else None
        rows.append({
            "work_id": r.work_id, "doi": r.doi, "title": r.title, "journal": r.source,
            "field": r.field, "pub_year": int(r.pub_year), "ret_year": int(r.ret_year),
            "reason_group": r.reason_group,
            "cites_before_retraction": pre,
            "cites_year_before": allc.get(r.ret_year - 1, 0),
            "cites_2025": allc.get(LAST, 0),
            "cites_after_retraction": post,
            "after_retraction_mentioning_retraction": post_aware,
            "share_mentioning_retraction": post_aware / post if post else None,
            "peak_year": peak_year,
            "years_since_retraction": LAST - int(r.ret_year),
        })
        hist[r.work_id] = {"all": allc, "aware": aware}
    df = pd.DataFrame(rows).sort_values(["cites_2025", "cites_after_retraction"], ascending=False)
    df.insert(0, "rank", range(1, len(df) + 1))
    (ROOT / "tables").mkdir(exist_ok=True)
    df.to_csv(ROOT / "tables" / "top_zombies.csv", index=False, encoding="utf-8")
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "zombie_history.json").write_text(json.dumps(hist))
    print(f"{len(df)} papers; API calls {oa.state['calls']}, budget left ${oa.state['remaining_usd']}")


if __name__ == "__main__":
    main()
