#!/usr/bin/env python
"""Run the ENG corridor cost-benefit model and print every intermediate step.

    python scripts/03_fiscal_model.py
    python scripts/03_fiscal_model.py --speed-improvement 0.15
    python scripts/03_fiscal_model.py --sensitivity speed_improvement

Needs no raw data. Reads ``data/processed/eng_corridor_metrics.csv`` and the
assumptions in ``eng_corridors.config``.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import _bootstrap  # noqa: F401  (must precede eng_corridors imports)
import numpy as np
import pandas as pd

from eng_corridors.config import DEFAULT_ASSUMPTIONS, PROCESSED, FiscalAssumptions
from eng_corridors.fiscal import (
    capital_cost,
    fiscal_summary,
    operating_savings,
    rail_revenue,
    rider_time_savings,
    sensitivity,
)

SWEEPS = {
    "speed_improvement": np.arange(0.05, 0.31, 0.05),
    "reinvestment_share": np.arange(0.0, 1.01, 0.25),
    "cost_per_bus_revenue_hour": np.arange(250, 331, 20),
    "ridership_uplift": np.arange(0.05, 0.26, 0.05),
    "discount_rate": np.arange(0.02, 0.09, 0.02),
}


def rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes", type=Path, default=PROCESSED / "eng_corridor_metrics.csv")
    parser.add_argument("--speed-improvement", type=float)
    parser.add_argument("--reinvestment-share", type=float)
    parser.add_argument("--cost-per-hour", type=float)
    parser.add_argument("--discount-rate", type=float)
    parser.add_argument("--sensitivity", choices=sorted(SWEEPS))
    parser.add_argument("--out", type=Path, help="write the summary to CSV")
    args = parser.parse_args()

    overrides = {
        k: v
        for k, v in {
            "speed_improvement": args.speed_improvement,
            "reinvestment_share": args.reinvestment_share,
            "cost_per_bus_revenue_hour": args.cost_per_hour,
            "discount_rate": args.discount_rate,
        }.items()
        if v is not None
    }
    a = FiscalAssumptions(**{**asdict(DEFAULT_ASSUMPTIONS), **overrides})

    routes = pd.read_csv(args.routes)
    pd.set_option("display.float_format", "{:,.2f}".format)

    rule("Assumptions")
    for key, value in asdict(a).items():
        marker = "  <-- overridden" if key in overrides else ""
        print(f"  {key:<32} {value}{marker}")

    rule("Capital cost")
    print(
        f"  {a.corridor_miles:.0f} mi x ${a.capital_cost_per_mile_musd}M/mi "
        f"x {a.soft_cost_multiplier} soft costs = ${capital_cost(a) / 1e6:.2f}M"
    )

    rule("Bucket 1 - operating savings")
    print(operating_savings(routes, a).to_string(index=False))

    rule("Bucket 2 - rail fare revenue")
    for key, value in rail_revenue(routes, a).items():
        print(f"  {key:<34} {value:,.2f}")

    rule("Bucket 3 - rider time")
    print(rider_time_savings(routes, a).to_string(index=False))

    summary = fiscal_summary(routes, a)
    rule("Headline")
    print(summary)

    if args.sensitivity:
        rule(f"Sensitivity: {args.sensitivity}")
        sweep = sensitivity(routes, args.sensitivity, SWEEPS[args.sensitivity], a)
        money = {
            "net_om_savings_per_year": "net_om_savings_$M",
            "rail_revenue_per_year": "rail_revenue_$M",
            "direct_benefit_per_year": "direct_benefit_$M",
            "npv_10yr": "npv_10yr_$M",
        }
        for column in money:
            sweep[column] = sweep[column] / 1e6
        sweep["rider_hours_per_year"] = sweep["rider_hours_per_year"] / 1e6
        sweep = sweep.rename(
            columns={**money, "rider_hours_per_year": "rider_hours_M"}
        )
        print(sweep.to_string(index=False))

        if args.sensitivity == "speed_improvement":
            print(
                "\n  Note: rail revenue is flat across this sweep because the\n"
                "  model holds the ridership uplift at a fixed 15% rather than\n"
                "  tying it to the speed gain. See docs/reproducibility.md."
            )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        summary.to_frame().to_csv(args.out, index=False)
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
