"""Join Retraction Watch to OpenAlex and build one row per retracted paper.

Every modelling choice about which retractions count lives here:
  * only notices whose nature is "Retraction" (not corrections or expressions of concern)
  * a paper retracted more than once keeps its earliest retraction
  * retract-and-replace notices are dropped: the DOI keeps pointing at a valid paper
  * notices whose date Retraction Watch marks as unknown are dropped
  * duplicates created by publisher error, and papers withdrawn to publish elsewhere,
    are dropped: the content itself was never called into question
Each paper gets one reason group, by priority, from the Retraction Watch reasons.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
YEARS = list(range(2012, 2026))  # OpenAlex counts_by_year starts in 2012; 2026 is partial

DROP_REASONS = [
    "Retract and Replace",
    "Date of Article and/or Notice Unknown",
    "Duplication of Content through Error by Journal/Publisher",
    "Withdrawn to Publish in Different Journal",
]

# first matching group wins; order is the priority
REASON_GROUPS = [
    ("misconduct / image problems", ["Falsification/Fabrication", "Manipulation of", "Misconduct",
                                     "Duplication of/in Image", "Concerns/Issues about Image",
                                     "Ethical Violations by Author", "False/Forged Authorship"]),
    ("honest error", ["Error in", "Results Not Reproducible", "Contamination of"]),
    ("paper mill / fake review", ["Paper Mill", "Compromised Peer Review", "Fake Peer Review",
                                  "Computer-Aided Content", "Rogue Editor"]),
    ("plagiarism / duplicate publication", ["Plagiarism", "Duplication of", "Euphemisms for"]),
]


def reason_group(reasons):
    for name, keys in REASON_GROUPS:
        if any(k in reasons for k in keys):
            return name
    return "other / unstated"


def load_rw():
    d = pd.read_csv(DATA / "rw.csv", encoding="utf-8", low_memory=False)
    d = d[d.RetractionNature == "Retraction"].copy()
    d["doi"] = d.OriginalPaperDOI.str.strip().str.lower()
    d = d[d.doi.str.startswith("10.", na=False)]
    d["ret_date"] = pd.to_datetime(d.RetractionDate, format="%m/%d/%Y %H:%M", errors="coerce")
    d["Reason"] = d.Reason.fillna("")
    d = d.dropna(subset=["ret_date"]).sort_values("ret_date")
    # reasons from every notice on the DOI, date from the earliest
    reasons = d.groupby("doi").Reason.agg(";".join)
    first = d.drop_duplicates("doi", keep="first").set_index("doi")
    first["Reason"] = reasons
    out = pd.DataFrame({
        "ret_year": first.ret_date.dt.year,
        "rw_subject": first.Subject,
        "country": first.Country,
        "paywalled_notice": first.Paywalled.eq("Yes"),
        "reasons": first.Reason,
    })
    out["dropped"] = out.reasons.apply(lambda r: any(k in r for k in DROP_REASONS))
    out["reason_group"] = out.reasons.apply(reason_group)
    return out.reset_index()


def counts_matrix(df):
    """Wide citations-per-year matrix, columns 2012..2025, zeros where OpenAlex lists none."""
    rows = [json.loads(c) for c in df["counts"]]
    m = np.zeros((len(df), len(YEARS)), dtype=float)
    for i, r in enumerate(rows):
        for y, c in r.items():
            y = int(y)
            if y in YEARS:
                m[i, YEARS.index(y)] = c
    return pd.DataFrame(m, columns=[f"c{y}" for y in YEARS], index=df.index)


def build():
    rw = load_rw()
    oa = pd.read_parquet(DATA / "retracted_openalex.parquet")
    df = oa.merge(rw, on="doi", how="inner")
    n_join = len(df)
    df = df[~df.dropped].drop(columns="dropped")
    # a paper cannot be retracted before it was published
    df = df[df.ret_year >= df.pub_year]
    df = pd.concat([df.drop(columns="counts"), counts_matrix(df)], axis=1)
    df.to_parquet(DATA / "papers.parquet", index=False)
    print(f"OpenAlex retracted works: {len(oa):,}; joined to a Retraction Watch retraction: "
          f"{n_join:,}; kept: {len(df):,}")
    print(df.reason_group.value_counts().to_string())

    pool = pd.read_parquet(DATA / "controls_openalex.parquet") if (DATA / "controls_openalex.parquet").exists() else None
    if pool is not None:
        pool = pool[~pool.doi.isin(rw.doi)]  # belt and braces: no retracted paper as a control
        # each band was sampled at a fixed size; weight back to the population it came from
        popn = pd.read_csv(DATA / "control_population.csv")
        n = pool.groupby(["pub_year", "band"]).size().rename("sampled").reset_index()
        w = popn.merge(n, on=["pub_year", "band"])
        w["weight"] = w.population / w.sampled
        pool = pool.merge(w[["pub_year", "band", "weight"]], on=["pub_year", "band"], how="left")
        pool = pd.concat([pool.drop(columns="counts"), counts_matrix(pool)], axis=1)
        pool.to_parquet(DATA / "controls.parquet", index=False)
        print(f"control pool: {len(pool):,}")


if __name__ == "__main__":
    build()
