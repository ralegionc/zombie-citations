import numpy as np
import pandas as pd
import pytest

import analysis as A
from build import YEARS, reason_group


def ev_row(values):
    """An event-time row from a dict {k: citations}; NaN elsewhere."""
    return np.array([values.get(k, np.nan) for k in A.EVENT], dtype=float)


def test_crossing_interpolates_between_years():
    # baseline 10, half is 5: year 0 has 9, year 1 has 1 -> crosses half a year into year 0..1
    ev = np.array([ev_row({-1: 10, 0: 9, 1: 1, 2: 1})])
    t, hit = A.crossing_times(ev, np.array([10.0]))
    assert hit[0]
    assert t[0] == pytest.approx(0.5)


def test_crossing_censored_at_last_observed_year():
    ev = np.array([ev_row({-1: 10, 0: 10, 1: 9, 2: 8})])
    t, hit = A.crossing_times(ev, np.array([10.0]))
    assert not hit[0]
    assert t[0] == 2


def test_crossing_immediate_when_already_below_half():
    ev = np.array([ev_row({-1: 2, 0: 1})])
    t, hit = A.crossing_times(ev, np.array([10.0]))
    assert hit[0] and t[0] == 0


def test_kaplan_meier_median_without_censoring():
    time = np.array([1.0, 2.0, 3.0, 4.0])
    hit = np.ones(4, bool)
    _, med = A.kaplan_meier(time, hit)
    assert med == 2.0


def test_kaplan_meier_censoring_and_weights():
    # two censored at 1 drop out of the risk set; the weighted event at 2 dominates
    time = np.array([1.0, 1.0, 2.0, 3.0])
    hit = np.array([False, False, True, True])
    _, med = A.kaplan_meier(time, hit, np.array([1, 1, 3, 1.0]))
    assert med == 2.0
    _, med = A.kaplan_meier(np.array([5.0]), np.array([False]))
    assert med == np.inf


def test_flow_ignores_unobserved_years():
    ev = np.array([[2.0, np.nan], [4.0, 4.0]])
    base = np.array([2.0, 4.0])
    np.testing.assert_allclose(A.flow(ev, base), [1.0, 1.0])


def test_at_returns_nan_outside_years():
    m = np.arange(len(YEARS), dtype=float)[None, :]
    assert A.at(m, [2012])[0] == 0
    assert np.isnan(A.at(m, [2011])[0]) and np.isnan(A.at(m, [2026])[0])


@pytest.mark.parametrize("reasons,group", [
    ("Falsification/Fabrication of Data;Plagiarism of Text;", "misconduct / image problems"),
    ("Duplication of/in Image;", "misconduct / image problems"),
    ("Error in Data;Paper Mill;", "honest error"),
    ("Paper Mill;Plagiarism of Text;", "paper mill / fake review"),
    ("Duplication of/in Article;", "plagiarism / duplicate publication"),
    ("Notice - Limited or No Information;", "other / unstated"),
])
def test_reason_priority(reasons, group):
    assert reason_group(reasons) == group


def frame(rows, **extra):
    df = pd.DataFrame([{f"c{y}": v for y, v in zip(YEARS, r)} for r in rows])
    for k, v in extra.items():
        df[k] = v
    return df


def test_match_picks_close_controls_and_reweights():
    # one treated paper retracted in 2018 with a flat 10 a year before
    flat = [10] * len(YEARS)
    treated = frame([flat], pub_year=2010, field="Medicine", ret_year=2018, B=10.0)
    pool = frame([flat, flat, [11] * len(YEARS), [100] * len(YEARS)],
                 pub_year=2010, field="Medicine", weight=[1.0, 1.0, 2.0, 1.0])
    pairs, how = A.match(treated, pool)
    assert set(pairs.c) == {0, 1, 2}  # the 100-a-year paper is outside the caliper
    assert pairs.w.sum() == pytest.approx(1.0)
    assert pairs.set_index("c").w[2] == pytest.approx(0.5)
    assert how["same field"] == 1


def test_study_shows_no_effect_when_treated_equals_controls():
    rng = np.random.default_rng(0)
    rows = rng.poisson(20, size=(5, len(YEARS))).astype(float)
    treated = frame([rows[0]], pub_year=2010, field="Medicine", ret_year=2018,
                    B=(rows[0][YEARS.index(2016)] + rows[0][YEARS.index(2017)]) / 2)
    pool = frame([rows[0]] * 4, pub_year=2010, field="Medicine", weight=1.0)
    pairs, _ = A.match(treated, pool)
    st = A.Study(treated, pool, pairs)
    _, _, ratio = st.effect(np.arange(1))
    observed = ~np.isnan(ratio)
    np.testing.assert_allclose(ratio[observed], 1.0)
