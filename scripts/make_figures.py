#!/usr/bin/env python
"""Regenerate every figure in figures/ from the CSVs in data/.

    python scripts/make_figures.py [--outdir figures]

Needs no raw data. This is the script to run first if you want to see whether
the repo works.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401  (must precede eng_corridors imports)
import pandas as pd

from eng_corridors import viz
from eng_corridors.config import FIGURES, PROCESSED, REFERENCE


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=FIGURES)
    args = parser.parse_args()

    viz.use_house_style()

    eng = pd.read_csv(PROCESSED / "eng_corridor_metrics.csv")
    scorecard = pd.read_csv(PROCESSED / "route_equity_scorecard.csv")
    service = pd.read_csv(PROCESSED / "service_performance.csv")
    sectors = pd.read_csv(PROCESSED / "lodes_sector_shares.csv")
    boardings = pd.read_csv(REFERENCE / "top15_boardings_digitized.csv")

    written = [
        viz.plot_ridership_ranking(boardings, args.outdir),
        viz.plot_equity_volume_scatter(scorecard, args.outdir),
        viz.plot_service_deficit(service, args.outdir),
        viz.plot_payback(eng, args.outdir),
        viz.plot_speed_sensitivity(eng, args.outdir),
        viz.plot_sector_composition(sectors, args.outdir),
        viz.plot_time_savings(eng, args.outdir),
    ]

    for path in written:
        try:
            display = path.relative_to(Path.cwd())
        except ValueError:
            # Output directory outside the repo, e.g. a CI temp dir.
            display = path
        print(f"wrote {display}")


if __name__ == "__main__":
    main()
