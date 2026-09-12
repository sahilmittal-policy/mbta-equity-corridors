#!/usr/bin/env python
"""Derive observed runtimes, trip counts and on-time performance by route.

    python scripts/02_service_performance.py

Requires ``data/raw/raw_arrival_departure_times.csv`` from the MBTA transit
performance feed. Writes ``data/processed/service_performance_rebuilt.csv``.

The feed is large. If it is split by month, concatenate first or pass a glob
with ``--input``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _bootstrap  # noqa: F401  (must precede eng_corridors imports)
import pandas as pd

from eng_corridors.config import PROCESSED, RAW_FILES
from eng_corridors.indices import add_indices
from eng_corridors.service import load_arrival_departure, route_service_table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_FILES["arrivals"])
    parser.add_argument(
        "--out", type=Path, default=PROCESSED / "service_performance_rebuilt.csv"
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Missing {args.input}. See data/README.md.", file=sys.stderr)
        return 1

    print(f"Loading {args.input} ...")
    events = load_arrival_departure(args.input)
    print(f"  {len(events):,} timepoint events")

    print("Reconstructing trip runtimes and on-time performance ...")
    table = route_service_table(events)
    table = add_indices(table)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    print(f"\nWrote {args.out}  ({len(table)} routes)")

    worst = table.dropna(subset=["sdi"]).nlargest(10, "sdi")
    print("\nWorst 10 routes by Service Deficit Index:")
    with pd.option_context("display.float_format", "{:.2f}".format):
        print(
            worst[
                ["route_id", "avg_peak_runtime_min", "otp_peak", "sdi"]
            ].to_string(index=False)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
