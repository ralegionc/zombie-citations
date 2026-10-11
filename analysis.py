"""Does retraction slow citations, and how long do retracted papers stay cited?

Design
  * Treated: papers retracted in 2015-2023 that drew at least MIN_BASE citations a year
    in the two years before retraction (their baseline B). OpenAlex citations by year
    start in 2012, so 2015 is the first retraction year with three years before it.
  * Controls: for each treated paper, every non-retracted paper in the sampled pool from
    the same publication year and OpenAlex field whose citations in the three years
    before the retraction year lie within CALIPER on a log scale. Pool papers carry
    sampling weights (the pool was drawn in fixed-size citation bands), so the weighted
    controls stand for the population of non-retracted papers with that history. If
    the field has too few, the match falls back to any field in the same year. Controls
    get the treated paper's retraction year as a pseudo-retraction year, so the two are
    compared over the same calendar years.
  * Event study: aggregate citations at each year relative to retraction, divided by the
    treated papers' aggregate baseline. The ratio of treated to control flow is the share
    of expected citations a retracted paper still receives.
  * Half-life after death: time from the retraction year until a paper's yearly
    citations first fall to half its own baseline, interpolated between years,
    Kaplan-Meier over papers and censored at 2025. The same clock run on the controls
    shows how fast papers fade when nothing happens to them.

Writes out/*.csv and out/results.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build import YEARS

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "out"
LAST = 2025
RET_YEARS = (2015, 2023)
MIN_BASE = 3
CALIPER = 0.35  # RMS distance in log1p citations per year over the three pre-years
MAX_CONTROLS = 60
MIN_CONTROLS = 3
EVENT = list(range(-3, 11))
N_BOOT = 400
SEED = 7

FIELD_GROUPS = {
    "Molecular & cell biology": ["Biochemistry, Genetics and Molecular Biology", "Immunology and Microbiology",
                                 "Pharmacology, Toxicology and Pharmaceutics"],
    "Medicine": ["Medicine", "Nursing", "Dentistry", "Health Professions", "Veterinary"],
    "Neuroscience & psychology": ["Neuroscience", "Psychology"],
    "Engineering & computing": ["Engineering", "Computer Science", "Decision Sciences", "Energy",
                                "Materials Science", "Chemical Engineering"],
    "Physical & earth sciences": ["Chemistry", "Physics and Astronomy", "Mathematics",
                                  "Earth and Planetary Sciences", "Environmental Science"],
    "Agriculture & ecology": ["Agricultural and Biological Sciences"],
    "Social sciences & business": ["Social Sciences", "Business, Management and Accounting",
                                   "Economics, Econometrics and Finance", "Arts and Humanities"],
}
FIELD_TO_GROUP = {f: g for g, fs in FIELD_GROUPS.items() for f in fs}


def counts(df):
    return df[[f"c{y}" for y in YEARS]].to_numpy(dtype=float)


def at(m, years):
    """m[i, years[i]] for a vector of calendar years; NaN outside 2012..LAST."""
    idx = np.asarray(years) - YEARS[0]
    ok = (idx >= 0) & (idx < len(YEARS))
    out = np.full(len(idx), np.nan)
    out[ok] = m[np.arange(len(idx))[ok], idx[ok]]
    return out


def baseline(m, R):
    return (at(m, R - 2) + at(m, R - 1)) / 2


def event_matrix(m, R):
    """Rows: papers; columns: years relative to R in EVENT; NaN where not yet observed."""
    return np.column_stack([at(m, R + k) for k in EVENT])


def treated_set(papers, min_base=MIN_BASE, ret_years=RET_YEARS):
    t = papers[papers.ret_year.between(*ret_years) & papers.pub_year.between(2000, 2022)].copy()
    t["B"] = baseline(counts(t), t.ret_year.to_numpy())
    t = t[t.B >= min_base].copy()
    t["field_group"] = t.field.map(FIELD_TO_GROUP).fillna("Other")
    return t.reset_index(drop=True)


def match(treated, pool, caliper=CALIPER, fallback=True):
    """Caliper matching on the three pre-retraction years.

    Returns a frame of (t, c, w): treated row, pool row, weight. Weights are the pool's
    sampling weights, normalised to sum to one within each treated paper.
    """
    pm = np.log1p(counts(pool))
    tm = np.log1p(counts(treated))
    pw = pool.weight.to_numpy()
    by_cell = {k: g.index.to_numpy() for k, g in pool.groupby(["pub_year", "field"])}
    by_year = {k: g.index.to_numpy() for k, g in pool.groupby("pub_year")}
    rows, how = [], []
    for i, r in enumerate(treated.itertuples()):
        cols = [r.ret_year - d - YEARS[0] for d in (3, 2, 1)]
        target = tm[i, cols]
        level = "unmatched"
        for name, cand in (("same field", by_cell.get((r.pub_year, r.field))),
                           ("any field", by_year.get(r.pub_year))):
            if cand is None or (name == "any field" and not fallback):
                continue
            dist = np.sqrt(((pm[np.ix_(cand, cols)] - target) ** 2).mean(axis=1))
            near = np.argsort(dist)[:MAX_CONTROLS]
            near = near[dist[near] <= caliper]
            if len(near) >= MIN_CONTROLS:
                w = pw[cand[near]]
                rows += [(i, c, x) for c, x in zip(cand[near], w / w.sum())]
                level = name
                break
        how.append(level)
    return pd.DataFrame(rows, columns=["t", "c", "w"]), pd.Series(how).value_counts()


def synthetic(pairs, cm, n):
    """Weighted mean of each treated paper's controls, row by row."""
    out = np.zeros((n, cm.shape[1]))
    np.add.at(out, pairs.t.to_numpy(), cm * pairs.w.to_numpy()[:, None])
    return out


def flow(ev, base):
    """Aggregate citations at each event year over aggregate baseline, on rows observed."""
    obs = ~np.isnan(ev)
    num = np.where(obs, ev, 0).sum(axis=0)
    den = (obs * base[:, None]).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / den


def crossing_times(ev, base):
    """Years after the retraction year until citations first reach half the baseline.

    Linear interpolation between yearly counts, starting from year -1. Returns (time,
    observed): unobserved crossings are censored at the last year with data.
    """
    half = base / 2
    j0 = EVENT.index(-1)
    time = np.zeros(len(ev))
    hit = np.zeros(len(ev), bool)
    for i in range(len(ev)):
        prev = ev[i, j0]
        if prev <= half[i]:
            time[i], hit[i] = 0.0, True
            continue
        last = -1
        for j in range(j0 + 1, len(EVENT)):
            v = ev[i, j]
            if np.isnan(v):
                break
            k = EVENT[j]
            if v <= half[i]:
                time[i] = max(0.0, (k - 1) + (prev - half[i]) / (prev - v))
                hit[i] = True
                break
            prev, last = v, k
        if not hit[i]:
            time[i] = max(last, 0)
    return time, hit


def kaplan_meier(time, hit, w=None, grid=np.arange(0, 10.01, 0.25)):
    w = np.ones(len(time)) if w is None else w
    order = np.argsort(time)
    time, hit, w = time[order], hit[order], w[order]
    at_risk = w.sum()
    s, surv_t, surv_s = 1.0, [0.0], [1.0]
    for tt in np.unique(time):
        here = time == tt
        d = (w * (here & hit)).sum()
        if at_risk > 0 and d > 0:
            s *= 1 - d / at_risk
            surv_t.append(tt)
            surv_s.append(s)
        at_risk -= w[here].sum()
    surv_t, surv_s = np.array(surv_t), np.array(surv_s)
    curve = surv_s[np.searchsorted(surv_t, grid, side="right") - 1]
    below = np.where(surv_s <= 0.5)[0]
    median = float(surv_t[below[0]]) if len(below) else np.inf
    return curve, median


class Study:
    """Everything the event study and half-lives need, aligned row by row."""

    def __init__(self, treated, pool, pairs):
        n = len(treated)
        R = treated.ret_year.to_numpy()
        pm = counts(pool)[pairs.c.to_numpy()]
        Rp = R[pairs.t.to_numpy()]
        self.c_ind_ev = event_matrix(pm, Rp)          # individual controls
        self.c_ind_base = baseline(pm, Rp)
        self.c_ind_t = pairs.t.to_numpy()
        self.c_ind_w = pairs.w.to_numpy()
        matched = np.bincount(self.c_ind_t, minlength=n) > 0
        t_ev = event_matrix(counts(treated), R)
        c_ev = synthetic(pairs, np.nan_to_num(self.c_ind_ev, nan=0.0), n)
        c_ev[np.isnan(t_ev)] = np.nan
        self.treated = treated[matched].reset_index(drop=True)
        remap = -np.ones(n, int)
        remap[matched] = np.arange(matched.sum())
        self.c_ind_t = remap[self.c_ind_t]
        self.t_ev, self.c_ev = t_ev[matched], c_ev[matched]
        self.base = self.treated.B.to_numpy()

    def effect(self, idx):
        rt = flow(self.t_ev[idx], self.base[idx])
        rc = flow(self.c_ev[idx], self.base[idx])
        return rt, rc, rt / rc

    def half_life(self, idx):
        t, h = crossing_times(self.t_ev[idx], self.base[idx])
        return kaplan_meier(t, h)

    def control_half_life(self, idx):
        sel = np.isin(self.c_ind_t, idx)
        ev = self.c_ind_ev[sel].copy()
        # controls are observed only as long as their treated paper is
        ev[np.isnan(self.t_ev[self.c_ind_t[sel]])] = np.nan
        t, h = crossing_times(ev, self.c_ind_base[sel])
        return kaplan_meier(t, h, self.c_ind_w[sel])


def boot(fn, idx, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    return [fn(rng.choice(idx, len(idx))) for _ in range(n)]


def event_table(st):
    idx = np.arange(len(st.base))
    est = st.effect(idx)
    b = np.array([np.stack(x) for x in boot(st.effect, idx)])  # (boot, 3, k)
    lo, hi = np.nanpercentile(b, [2.5, 97.5], axis=0)
    rows = []
    for j, k in enumerate(EVENT):
        rows.append({"k": k, "n": int((~np.isnan(st.t_ev[:, j])).sum()),
                     "treated": est[0][j], "treated_lo": lo[0][j], "treated_hi": hi[0][j],
                     "control": est[1][j], "control_lo": lo[1][j], "control_hi": hi[1][j],
                     "ratio": est[2][j], "ratio_lo": lo[2][j], "ratio_hi": hi[2][j]})
    return pd.DataFrame(rows)


def ratio_at(st, idx, ks=(3, 4, 5)):
    """Treated over control citations, pooled over years ks after retraction."""
    js = [EVENT.index(k) for k in ks]
    t, c = st.t_ev[idx][:, js], st.c_ev[idx][:, js]
    ok = ~np.isnan(t)
    return t[ok].sum() / c[ok].sum()


def group_table(st, col):
    rows = []
    for g, sub in st.treated.groupby(col):
        idx = sub.index.to_numpy()
        if len(idx) < 40:
            continue
        b = boot(lambda i: ratio_at(st, i), idx)
        curve, med = st.half_life(idx)
        bm = [m for _, m in boot(st.half_life, idx, n=200)]
        _, cmed = st.control_half_life(idx)
        j5 = EVENT.index(5)
        rows.append({col: g, "n": len(idx),
                     "n_3y": int((~np.isnan(st.t_ev[idx, EVENT.index(3)])).sum()),
                     "share_kept_3to5y": ratio_at(st, idx),
                     "share_lo": np.percentile(b, 2.5), "share_hi": np.percentile(b, 97.5),
                     "half_life": med, "half_life_lo": np.percentile(bm, 2.5),
                     "half_life_hi": np.percentile(bm, 97.5),
                     "control_half_life": cmed,
                     "still_above_half_5y": curve[20]})
    return pd.DataFrame(rows).sort_values("share_kept_3to5y")


def run(papers, pool, min_base=MIN_BASE, caliper=CALIPER, ret_years=RET_YEARS, fallback=True):
    treated = treated_set(papers, min_base, ret_years)
    pairs, quality = match(treated, pool, caliper, fallback)
    return treated, Study(treated, pool, pairs), pairs, quality


def main():
    OUT.mkdir(exist_ok=True)
    papers = pd.read_parquet(DATA / "papers.parquet")
    pool = pd.read_parquet(DATA / "controls.parquet").reset_index(drop=True)
    treated, st, pairs, quality = run(papers, pool)
    print(f"treated: {len(treated):,}; matched: {len(st.base):,}\n{quality.to_string()}")
    ess = pairs.groupby("t").w.apply(lambda w: 1 / (w ** 2).sum())
    print(f"controls per treated paper: median {pairs.groupby('t').size().median():.0f}, "
          f"median effective {ess.median():.1f}")

    es = event_table(st)
    es.to_csv(OUT / "event_study.csv", index=False)
    print(es.round(3).to_string(index=False))

    idx = np.arange(len(st.base))
    curve_t, med_t = st.half_life(idx)
    curve_c, med_c = st.control_half_life(idx)
    st.treated["all"] = "All fields"
    by_all = group_table(st, "all").rename(columns={"all": "group"})
    by_field = group_table(st, "field_group").rename(columns={"field_group": "group"})
    by_reason = group_table(st, "reason_group").rename(columns={"reason_group": "group"})
    by_field = pd.concat([by_all, by_field])
    by_reason = pd.concat([by_all, by_reason])
    by_field.to_csv(OUT / "by_field.csv", index=False)
    by_reason.to_csv(OUT / "by_reason.csv", index=False)
    print(by_field.round(2).to_string(index=False))
    print(by_reason.round(2).to_string(index=False))

    curves = {"grid": np.arange(0, 10.01, 0.25).tolist(), "All fields": {"treated": curve_t.tolist(), "control": curve_c.tolist()}}
    for g in FIELD_GROUPS:
        sub = st.treated.index[st.treated.field_group == g].to_numpy()
        if len(sub) >= 40:
            curves[g] = {"treated": st.half_life(sub)[0].tolist(), "control": st.control_half_life(sub)[0].tolist()}

    # every joined retracted paper, not just the analysis set
    allm = counts(papers)
    R = papers.ret_year.to_numpy()
    post = np.where(np.array(YEARS)[None, :] > R[:, None], allm, 0)
    old = (R <= LAST - 3)
    tm = st.treated
    res = {
        "n_papers": len(papers),
        "n_treated": len(treated),
        "n_matched": len(st.base),
        "match_levels": quality.to_dict(),
        "n_controls_used": int(pairs.c.nunique()),
        "half_life_years": med_t,
        "control_half_life_years": med_c,
        "share_kept_3to5y": float(by_all.share_kept_3to5y.iloc[0]),
        "share_kept_3to5y_ci": [float(by_all.share_lo.iloc[0]), float(by_all.share_hi.iloc[0])],
        "post_retraction_citations_2013_2025": int(post.sum()),
        "citations_2025_to_papers_retracted_by_2022": int(allm[old, -1].sum()),
        "papers_retracted_by_2022": int(old.sum()),
        "papers_retracted_by_2022_cited_in_2025": int((allm[old, -1] > 0).sum()),
        "frac_matched_retracted_by_2022_still_at_baseline_2025": float(
            ((tm.c2025 >= tm.B) & (tm.ret_year <= LAST - 3)).sum() / (tm.ret_year <= LAST - 3).sum()),
        "km_curves": curves,
    }
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=float))
    print({k: v for k, v in res.items() if k != "km_curves"})
    st.treated.assign(**{f"t{k}": st.t_ev[:, j] for j, k in enumerate(EVENT)},
                      **{f"s{k}": st.c_ev[:, j] for j, k in enumerate(EVENT)}
                      ).to_parquet(OUT / "treated_matched.parquet", index=False)


if __name__ == "__main__":
    main()
