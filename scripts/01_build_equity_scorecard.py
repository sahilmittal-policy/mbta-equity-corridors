#!/usr/bin/env python
"""Rank every MBTA bus route by transit dependence and equity volume.

    python scripts/01_build_equity_scorecard.py

Requires the challenge geodata in ``data/raw/``:

    bus_ridership_by_stop_route.csv
    mbta_network.gpkg          (layer: bus_stops_gtfs)
    demographics.gpkg          (layer: blockgroup)

Writes ``data/processed/route_equity_scorecard_rebuilt.csv``. The suffix is
deliberate: it sits alongside the submitted scorecard rather than overwriting
it, so a rebuild can be diffed against what was actually handed to the judges.

Expect several minutes. There is one spatial join per route.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _bootstrap  # noqa: F401  (must precede eng_corridors imports)

from eng_corridors.config import CORRIDOR_BUFFER_M, PROCESSED, RAW_FILES
from eng_corridors.spatial import (
    build_route_tdi_table,
    load_bus_stops,
    load_demographics,
    load_weekday_bus_ridership,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--buffer-m", type=int, default=CORRIDOR_BUFFER_M)
    parser.add_argument(
        "--out",
        type=Path,
        default=PROCESSED / "route_equity_scorecard_rebuilt.csv",
    )
    args = parser.parse_args()

    missing = [
        str(p)
        for key, p in RAW_FILES.items()
        if key in {"ridership", "network", "demographics"} and not p.exists()
    ]
    if missing:
        print("Missing raw inputs:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        print("\nSee data/README.md for where to get them.", file=sys.stderr)
        return 1

    print("Loading ridership ...")
    bus_weekday = load_weekday_bus_ridership(RAW_FILES["ridership"])

    print("Loading stop geometries ...")
    stops = load_bus_stops(RAW_FILES["network"])

    print("Loading block-group demographics ...")
    dem = load_demographics(RAW_FILES["demographics"])

    print(f"Building TDI for every route at {args.buffer_m} m ...")
    table = build_route_tdi_table(bus_weekday, stops, dem, args.buffer_m)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    print(f"\nWrote {args.out}  ({len(table)} routes)")
    print("\nTop 10 by equity-volume score:")
    print(
        table.head(10)[
            ["route_id", "tdi", "avg_weekday_boardings", "equity_volume_score"]
        ].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
