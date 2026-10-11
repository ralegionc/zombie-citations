"""Print every number quoted in the README, from the files in out/ and tables/."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT, TAB = ROOT / "out", ROOT / "tables"


def main():
    res = json.loads((OUT / "results.json").read_text())
    es = pd.read_csv(OUT / "event_study.csv").set_index("k")
    field = pd.read_csv(OUT / "by_field.csv")
    reason = pd.read_csv(OUT / "by_reason.csv")
    sens = pd.read_csv(TAB / "sensitivity.csv")
    top = pd.read_csv(TAB / "top_zombies.csv")

    print("# Zombie citations: numbers\n")
    print(f"- retracted papers with 10+ citations joined to Retraction Watch: {res['n_papers']:,}")
    print(f"- analysis set (retracted 2015-2023, 3+ citations a year before): {res['n_treated']:,}, "
          f"matched {res['n_matched']:,}; match levels {res['match_levels']}; "
          f"distinct controls {res['n_controls_used']:,}")
    print(f"- citations to papers in years after their retraction, 2013-2025: "
          f"{res['post_retraction_citations_2013_2025']:,}")
    print(f"- citations in 2025 to papers retracted by 2022: "
          f"{res['citations_2025_to_papers_retracted_by_2022']:,}, spread over "
          f"{res['papers_retracted_by_2022_cited_in_2025']:,} of {res['papers_retracted_by_2022']:,} papers")
    print(f"- half-life after retraction: {res['half_life_years']:.2f} years "
          f"(matched controls {res['control_half_life_years']:.2f})")
    lo, hi = res["share_kept_3to5y_ci"]
    print(f"- share of expected citations kept 3-5 years on: {res['share_kept_3to5y']:.1%} ({lo:.1%} to {hi:.1%})")
    print(f"- matched retracted papers (retracted by 2022) cited in 2025 at or above their old rate: "
          f"{res['frac_matched_retracted_by_2022_still_at_baseline_2025']:.1%}")

    print("\n## Event study (citations relative to the two years before)\n")
    print(es[["n", "treated", "control", "ratio", "ratio_lo", "ratio_hi"]].round(3).to_markdown())
    print("\n## By field\n")
    cols = ["group", "n", "share_kept_3to5y", "share_lo", "share_hi", "half_life",
            "half_life_lo", "half_life_hi", "control_half_life"]
    print(field[cols].round(2).to_markdown(index=False))
    print("\n## By reason\n")
    print(reason[cols].round(2).to_markdown(index=False))
    print("\n## Sensitivity\n")
    print(sens.round(3).to_markdown(index=False))

    post = top.cites_after_retraction.sum()
    aware = top.after_retraction_mentioning_retraction.sum()
    print(f"\n## Top zombies ({len(top)} papers fetched)\n")
    print(f"- citations since retraction: {post:,}; from works mentioning retraction in title or "
          f"abstract: {aware:,} ({aware / post:.1%}); papers where none do: "
          f"{(top.after_retraction_mentioning_retraction == 0).sum()}")
    print(f"- peak citation year after the retraction year: {(top.peak_year > top.ret_year).sum()}; "
          f"cited more in 2025 than the year before retraction: "
          f"{(top.cites_2025 > top.cites_year_before).sum()}")
    show = ["rank", "title", "journal", "ret_year", "reason_group", "cites_year_before",
            "cites_2025", "cites_after_retraction", "share_mentioning_retraction"]
    t = top[show].head(15).copy()
    t["title"] = t.title.str.replace(r"^(RETRACTED( ARTICLE)?: |Retracted: |\[Retracted\] )", "", regex=True).str[:70]
    t["share_mentioning_retraction"] = (t.share_mentioning_retraction * 100).round(1)
    print(t.to_markdown(index=False))


if __name__ == "__main__":
    main()
