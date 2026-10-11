"""The four figures, written to figures/."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).parent
OUT, FIG = ROOT / "out", ROOT / "figures"

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
CONTROL, RETRACTED = "#2a78d6", "#eb6834"  # categorical slots 1 and 2
MUTED = "#b9b8b3"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "font.family": "DejaVu Sans",
})


def headline():
    es = pd.read_csv(OUT / "event_study.csv")
    res = json.loads((OUT / "results.json").read_text())
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for col, color, label in (("control", CONTROL, "matched papers that were never retracted"),
                              ("treated", RETRACTED, "retracted papers")):
        ax.fill_between(es.k, es[f"{col}_lo"], es[f"{col}_hi"], color=color, alpha=0.15, lw=0)
        ax.plot(es.k, es[col], color=color, lw=2.2, marker="o", ms=5,
                markeredgecolor=SURFACE, markeredgewidth=1.2, label=label)
    ax.axvline(0, color=INK2, lw=1, ls=(0, (3, 3)))
    ax.text(0.12, 1.42, "retraction\nyear", color=INK2, fontsize=9, va="top")
    ax.axhline(1, color=MUTED, lw=1)
    k4 = es.set_index("k").loc[4]
    ax.annotate("", xy=(4, k4.treated + 0.03), xytext=(4, k4.control - 0.03),
                arrowprops=dict(arrowstyle="<->", color=INK2, lw=1))
    share = res["share_kept_3to5y"]
    ax.text(4.2, (k4.treated + k4.control) / 2,
            f"3 to 5 years on, retracted papers\nstill get {share:.0%} of the citations\nthey would have had",
            color=INK, fontsize=9.5, va="center")
    last = es[es.k == es.k.max()].iloc[0]
    ax.text(last.k + 0.15, last.treated, f"{last.treated:.0%}", color=INK2, fontsize=9, va="center")
    ax.set_xlabel("years since the retraction year")
    ax.set_ylabel("citations per year, relative to the 2 years before")
    ax.set_xticks(es.k)
    ax.set_ylim(0, 1.5)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.legend(frameon=False, loc="upper right", fontsize=9.5)
    ax.set_title(f"Retraction cuts citations fast, but never to zero\n"
                 f"{res['n_matched']:,} papers retracted 2015-2023, each compared with matched papers\n"
                 "from the same publication year and field", loc="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_zombie_curve.png", dpi=160)
    plt.close(fig)


def dot_panel(ax, df, est, lo, hi, color, fmt):
    y = np.arange(len(df))
    ax.hlines(y, df[lo], df[hi], color=color, lw=2, alpha=0.45)
    ax.plot(df[est], y, "o", color=color, ms=8, markeredgecolor=SURFACE, markeredgewidth=1.5)
    span = ax.get_xlim()[1] if ax.get_xlim()[1] > 1.5 else 0.6
    for yi, v, h in zip(y, df[est], df[hi]):
        ax.text(max(h, v) + span * 0.015, yi, fmt(v), va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(y)
    ax.grid(axis="y", visible=False)


def by_group(fname, out, title, label_col="group"):
    df = pd.read_csv(OUT / fname)
    df = pd.concat([df[df.group != "All fields"].sort_values("share_kept_3to5y"), df[df.group == "All fields"]])
    df["label"] = [f"{g} ({n:,})" for g, n in zip(df.group, df.n)]
    df.loc[df.group == "All fields", "label"] = f"All ({df[df.group == 'All fields'].n.iloc[0]:,})"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 0.55 * len(df) + 1.8), sharey=True,
                                 gridspec_kw={"width_ratios": [1.1, 1]})
    dot_panel(a1, df, "share_kept_3to5y", "share_lo", "share_hi", RETRACTED, lambda v: f"{v:.0%}")
    a1.set_yticklabels(df.label)
    a1.set_xlim(0, max(0.6, df.share_hi.max() + 0.05))
    a1.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    a1.set_title("share of expected citations still received\n3 to 5 years after retraction",
                 loc="left", fontsize=10, color=INK)
    y = np.arange(len(df))
    ctrl = df.control_half_life.clip(upper=10)
    a2.plot(ctrl, y, "o", color=CONTROL, ms=8, markeredgecolor=SURFACE, markeredgewidth=1.5,
            label="matched, never retracted")
    dot_panel(a2, df, "half_life", "half_life_lo", "half_life_hi", RETRACTED, lambda v: f"{v:.1f}")
    a2.plot([], [], "o", color=RETRACTED, ms=8, label="retracted")
    a2.set_xlim(0, max(6.5, ctrl.max() + 0.5))
    a2.set_title("half-life: years until yearly citations\nfirst fall to half their old rate",
                 loc="left", fontsize=10, color=INK)
    a2.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.06 * 8 / len(df)), ncol=2)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / out, dpi=160)
    plt.close(fig)


def zombies(n=12):
    top = pd.read_csv(ROOT / "tables" / "top_zombies.csv").head(n)
    hist = json.loads((OUT / "zombie_history.json").read_text())
    fig, axes = plt.subplots(3, 4, figsize=(13, 8.2))
    for ax, r in zip(axes.flat, top.itertuples()):
        h = {int(k): v for k, v in hist[r.work_id]["all"].items()}
        years = np.arange(r.pub_year, 2026)
        vals = np.array([h.get(y, 0) for y in years])
        colors = [MUTED if y <= r.ret_year else RETRACTED for y in years]
        ax.bar(years, vals, color=colors, width=0.8)
        ax.axvline(r.ret_year + 0.5, color=INK, lw=1)
        title = r.title.replace("RETRACTED ARTICLE: ", "").replace("RETRACTED: ", "").replace("Retracted: ", "")
        title = title[:40] + ("..." if len(title) > 40 else "")
        ax.set_title(f"#{r.rank} {title}\n{r.journal[:30]}, retracted {r.ret_year}",
                     fontsize=8.2, loc="left", color=INK)
        ax.text(0.02, 0.97, f"{r.cites_after_retraction:,} cites since", transform=ax.transAxes,
                fontsize=8, va="top", color=INK2)
        ax.tick_params(labelsize=7.5)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        ax.grid(axis="x", visible=False)
    fig.suptitle("The most-cited retracted papers in 2025: citations per year, grey up to the "
                 "retraction year, orange after", x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_top_zombies.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    headline()
    by_group("by_field.csv", "fig2_by_field.png", "By field")
    by_group("by_reason.csv", "fig3_by_reason.png", "By reason for retraction")
    zombies()
    print("figures written")
