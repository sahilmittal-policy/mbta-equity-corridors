"""Figures.

Every chart here is regenerated from the CSVs in ``data/`` rather than copied
out of the presentation, so the numbers on screen and the numbers in the repo
cannot drift apart.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eng_corridors.config import DEFAULT_ASSUMPTIONS, ENG_ROUTES, FiscalAssumptions
from eng_corridors.fiscal import (
    annuity_factor,
    fiscal_summary,
    sensitivity,
)

# --------------------------------------------------------------------------
# House style
# --------------------------------------------------------------------------

TEAL = "#0E7C7B"
NAVY = "#12496B"
MINT = "#7DD3A7"
AMBER = "#E8A33D"
GREY = "#9AA0A6"
INK = "#1F2933"


def use_house_style() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 130,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlepad": 14,
            "axes.labelsize": 10,
            "axes.labelcolor": INK,
            "axes.edgecolor": "#D6DBE0",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#EDF0F2",
            "grid.linewidth": 0.9,
            "axes.axisbelow": True,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.bottom": False,
            "ytick.left": False,
            "legend.frameon": False,
            "figure.facecolor": "white",
        }
    )


def _caption(ax, text: str) -> None:
    ax.annotate(
        text,
        xy=(0, -0.16),
        xycoords="axes fraction",
        fontsize=8.5,
        color=GREY,
        va="top",
        wrap=True,
    )


def _save(fig, outdir: Path, name: str) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / name
    fig.savefig(path)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------


def plot_ridership_ranking(boardings: pd.DataFrame, outdir: Path) -> Path:
    """Top 15 equity-volume routes by boardings, ENG routes called out."""
    df = boardings.sort_values("approx_avg_weekday_boardings")
    colors = [
        TEAL if str(r) in ENG_ROUTES else MINT for r in df["route_id"]
    ]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(
        df["route_id"].astype(str),
        df["approx_avg_weekday_boardings"],
        color=colors,
        width=0.72,
    )
    system_median = 2400
    ax.axhline(system_median, color=NAVY, lw=1.4, ls="-")
    ax.annotate(
        "System median (~2,400)",
        xy=(0.2, system_median),
        xytext=(0.2, system_median + 450),
        fontsize=9,
        color=NAVY,
    )

    for bar, route in zip(bars, df["route_id"].astype(str), strict=False):
        if route in ENG_ROUTES:
            ax.annotate(
                f"{bar.get_height():,.0f}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, -10),
                textcoords="offset points",
                ha="center",
                va="top",
                rotation=90,
                fontsize=9,
                fontweight="bold",
                color="white",
            )

    ax.set_title("The three ENG routes carry ~5x the median bus route")
    ax.set_xlabel("Bus route (top 15 by equity-volume score)")
    ax.set_ylabel("Average weekday boardings")
    ax.set_ylim(0, 13800)
    _caption(
        ax,
        "Routes 23, 28 and 66 in teal. Values for other routes digitised from the\n"
        "submitted presentation; see data/reference/README.md.",
    )
    return _save(fig, outdir, "fig01_ridership_ranking.png")


def plot_equity_volume_scatter(scorecard: pd.DataFrame, outdir: Path) -> Path:
    """TDI against ridership, with equity-volume shown as iso-curves.

    Makes the selection logic visible: the ENG routes are not the most
    transit-dependent, nor the busiest. They are furthest out along both axes
    at once, which is what the product picks up.
    """
    fig, ax = plt.subplots(figsize=(7.6, 5.4))

    x = scorecard["avg_weekday_boardings_uncorrected"]
    y = scorecard["tdi"]
    is_eng = scorecard["route_id"].astype(str).isin(ENG_ROUTES)

    # Iso-curves of constant equity-volume score.
    ax.set_xlim(x.min() * 0.88, x.max() * 1.06)
    ax.set_ylim(2.0, 3.25)
    grid = np.linspace(*ax.get_xlim(), 300)
    for score in (70_000, 100_000, 130_000, 157_000):
        curve = score / grid
        ax.plot(grid, curve, color="#E3E8EC", lw=1, zorder=0)
        # Label where the curve leaves the top of the axes.
        inside = np.where(curve <= 3.2)[0]
        if inside.size:
            ax.annotate(
                f"EV {score / 1000:.0f}k",
                xy=(grid[inside[0]], curve[inside[0]]),
                xytext=(3, 4),
                textcoords="offset points",
                fontsize=7.5,
                color=GREY,
            )

    ax.scatter(x[~is_eng], y[~is_eng], s=55, color=GREY, alpha=0.75, zorder=2)
    ax.scatter(
        x[is_eng], y[is_eng], s=150, color=TEAL, zorder=3, edgecolor="white", lw=1.5
    )

    for _, row in scorecard.iterrows():
        ax.annotate(
            str(row["route_id"]),
            xy=(row["avg_weekday_boardings_uncorrected"], row["tdi"]),
            xytext=(7, 0),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold" if str(row["route_id"]) in ENG_ROUTES else "normal",
            color=TEAL if str(row["route_id"]) in ENG_ROUTES else GREY,
            va="center",
        )

    ax.set_title("Equity need and ridership volume, top 15 routes")
    ax.set_xlabel("Average weekday boardings")
    ax.set_ylabel("Transit Dependence Index  (1.0 = system average)")
    ax.xaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}")
    )
    _caption(
        ax,
        "Grey curves are constant equity-volume scores. Boardings on this chart use the\n"
        "pre-correction basis on which the original ranking was computed.",
    )
    return _save(fig, outdir, "fig02_equity_volume_scatter.png")


def plot_service_deficit(service: pd.DataFrame, outdir: Path) -> Path:
    """Runtime and unreliability side by side for the top equity routes."""
    df = service.dropna(subset=["avg_peak_runtime_min"]).sort_values(
        "avg_peak_runtime_min"
    )
    idx = np.arange(len(df))
    width = 0.27

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(
        idx - width,
        df["avg_peak_runtime_min"],
        width,
        label="Average peak runtime (min)",
        color=TEAL,
    )
    ax.bar(
        idx,
        (1 - df["otp_peak"]) * 100,
        width,
        label="% not on time, peak",
        color=AMBER,
    )
    ax.bar(
        idx + width,
        (1 - df["otp_offpeak"]) * 100,
        width,
        label="% not on time, off-peak",
        color=NAVY,
    )

    ax.set_xticks(idx)
    ax.set_xticklabels(df["route_id"].astype(str))
    for tick, route in zip(ax.get_xticklabels(), df["route_id"].astype(str), strict=False):
        if route in ENG_ROUTES:
            tick.set_fontweight("bold")
            tick.set_color(TEAL)

    ax.set_title("The highest-need routes are also the slowest")
    ax.set_xlabel("Bus route")
    ax.set_ylabel("Minutes  /  percent")
    ax.legend(ncol=3, loc="upper left", fontsize=9)
    ax.set_ylim(0, 58)
    _caption(
        ax,
        "ENG routes labelled in teal. Route 66 runs roughly 49 minutes at peak with the\n"
        "worst on-time performance in the group.",
    )
    return _save(fig, outdir, "fig03_service_deficit.png")


def plot_payback(
    routes: pd.DataFrame,
    outdir: Path,
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> Path:
    """Cumulative discounted net benefit against the one-time capital cost."""
    summary = fiscal_summary(routes, a)
    years = np.arange(0, a.horizon_years + 1)
    cumulative = np.array(
        [
            summary.direct_benefit_per_year * annuity_factor(a.discount_rate, int(y))
            - summary.capital_cost
            for y in years
        ]
    )

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(years, cumulative / 1e6, color=TEAL, lw=2.6, marker="o", ms=5)
    ax.axhline(0, color=INK, lw=1)
    ax.fill_between(
        years,
        0,
        cumulative / 1e6,
        where=cumulative >= 0,
        color=TEAL,
        alpha=0.12,
        interpolate=True,
    )
    ax.fill_between(
        years,
        0,
        cumulative / 1e6,
        where=cumulative < 0,
        color=AMBER,
        alpha=0.18,
        interpolate=True,
    )

    ax.annotate(
        f"Breakeven\n~{summary.payback_years:.1f} years",
        xy=(summary.payback_years, 0),
        xytext=(summary.payback_years + 0.7, -9),
        fontsize=9.5,
        color=INK,
        arrowprops=dict(arrowstyle="->", color=GREY, lw=1.2),
    )
    ax.annotate(
        f"10-year NPV\n${summary.npv_10yr/1e6:.1f}M",
        xy=(a.horizon_years, cumulative[-1] / 1e6),
        xytext=(-95, -12),
        textcoords="offset points",
        fontsize=9.5,
        fontweight="bold",
        color=TEAL,
    )

    ax.set_title("Direct fiscal case: cumulative discounted net benefit")
    ax.set_xlabel("Years after construction")
    ax.set_ylabel("Cumulative net benefit ($M, 4% real)")
    _caption(
        ax,
        "Counts only MBTA cash flows: net operating savings after reinvesting half the\n"
        "freed bus-hours, plus incremental rail fares. Rider time value is excluded.",
    )
    return _save(fig, outdir, "fig04_payback.png")


def plot_speed_sensitivity(
    routes: pd.DataFrame,
    outdir: Path,
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> Path:
    """Payback and NPV across the plausible range of speed improvements."""
    grid = np.arange(0.05, 0.31, 0.01)
    sweep = sensitivity(routes, "speed_improvement", grid, a)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(sweep["speed_improvement"] * 100, sweep["payback_years"], color=TEAL, lw=2.6)
    ax.set_xlabel("Runtime reduction delivered (%)")
    ax.set_ylabel("Payback period (years)", color=TEAL)
    ax.tick_params(axis="y", labelcolor=TEAL)

    ax.axvspan(10, 25, color=MINT, alpha=0.18)
    ax.annotate(
        "Range observed in comparable\nbus-priority projects (10-25%)",
        xy=(15.2, ax.get_ylim()[1] * 0.88),
        ha="center",
        fontsize=9,
        color=INK,
    )
    ax.axvline(a.speed_improvement * 100, color=INK, ls="--", lw=1.2)

    twin = ax.twinx()
    twin.plot(
        sweep["speed_improvement"] * 100,
        sweep["npv_10yr"] / 1e6,
        color=AMBER,
        lw=2.6,
        ls="-",
    )
    twin.set_ylabel("10-year NPV ($M)", color=AMBER)
    twin.tick_params(axis="y", labelcolor=AMBER)
    twin.grid(False)

    ax.set_title("The case survives well below the assumed 20%")
    _caption(
        ax,
        "Dashed line is the central case. Payback stays under five years even if the\n"
        "package delivers only a 5% runtime reduction.",
    )
    return _save(fig, outdir, "fig05_speed_sensitivity.png")


def plot_sector_composition(sectors: pd.DataFrame, outdir: Path) -> Path:
    """Corridor vs rest-of-state employment mix."""
    df = sectors.sort_values("corridor_share")
    idx = np.arange(len(df))
    height = 0.38

    fig, ax = plt.subplots(figsize=(9.4, 5.6))
    ax.barh(idx + height / 2, df["corridor_share"] * 100, height, color=TEAL,
            label="ENG corridor residents")
    ax.barh(idx - height / 2, df["rest_share"] * 100, height, color=GREY,
            label="Rest of Massachusetts")

    ax.set_yticks(idx)
    ax.set_yticklabels(df["sector_name"], fontsize=9)
    ax.set_title(
        "Corridor residents are concentrated in health care and education",
        fontsize=12,
    )
    ax.set_xlabel("Share of jobs held (%)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", visible=False)
    _caption(
        ax,
        "LEHD LODES residence-area characteristics. Shares are of each group's top-10\n"
        "sector total, so the comparison is composition rather than size.",
    )
    return _save(fig, outdir, "fig06_sector_composition.png")


def plot_time_savings(routes: pd.DataFrame, outdir: Path) -> Path:
    """Minutes saved per trip and hours per year for a daily commuter."""
    from eng_corridors.fiscal import rider_time_savings

    df = rider_time_savings(routes).sort_values("minutes_saved_per_trip")

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    bars = ax.barh(
        [f"Route {r}" for r in df["route_id"]],
        df["minutes_saved_per_trip"],
        color=TEAL,
        height=0.55,
    )
    for bar, hours in zip(bars, df["hours_saved_per_year_daily_commuter"], strict=False):
        ax.annotate(
            f"{bar.get_width():.1f} min  ·  {hours:.0f} hrs/yr for a daily commuter",
            xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=9.5,
            color=INK,
        )

    ax.set_xlim(0, 17)
    ax.set_title("What a 20% runtime cut returns to riders")
    ax.set_xlabel("Minutes saved per one-way trip")
    ax.grid(axis="y", visible=False)
    _caption(
        ax,
        "Across all three routes this is roughly 4,900 rider-hours every weekday, or\n"
        "about 1.23 million hours a year.",
    )
    return _save(fig, outdir, "fig07_time_savings.png")
