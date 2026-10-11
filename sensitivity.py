"""Rerun the main estimates, changing one choice at a time.

For each variant: how many papers, the share of expected citations retracted papers
still get 3-5 years after retraction, the pre-retraction gap between treated and
controls, and the half-life after death for treated and controls.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import analysis as A

ROOT = Path(__file__).parent

VARIANTS = [
    ("main analysis", {}),
    ("baseline at least 5 a year", {"min_base": 5}),
    ("baseline at least 10 a year", {"min_base": 10}),
    ("tighter caliper (0.2)", {"caliper": 0.2}),
    ("looser caliper (0.5)", {"caliper": 0.5}),
    ("same-field controls only", {"fallback": False}),
    ("retracted 2015-2020 only", {"ret_years": (2015, 2020)}),
    ("retracted 2018-2023 only", {"ret_years": (2018, 2023)}),
]


def summarise(name, st):
    idx = np.arange(len(st.base))
    rt, rc, ratio = st.effect(idx)
    pre = ratio[A.EVENT.index(-1)]
    share = A.ratio_at(st, idx)
    return {"variant": name, "n": len(idx),
            "share_kept_3to5y": share,
            "pre_gap_k-1": pre,
            "share_kept_pre_adjusted": share / pre,
            "half_life": st.half_life(idx)[1],
            "control_half_life": st.control_half_life(idx)[1]}


def main():
    papers = pd.read_parquet(A.DATA / "papers.parquet")
    pool = pd.read_parquet(A.DATA / "controls.parquet").reset_index(drop=True)
    rows = []
    for name, kw in VARIANTS:
        _, st, _, _ = A.run(papers, pool, **kw)
        rows.append(summarise(name, st))
        print(rows[-1])
    df = pd.DataFrame(rows)
    (ROOT / "tables").mkdir(exist_ok=True)
    df.to_csv(ROOT / "tables" / "sensitivity.csv", index=False)
    print(df.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
