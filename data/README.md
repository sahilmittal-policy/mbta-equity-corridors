# Data

## Layout

```
data/
├── processed/   Results from the submitted analysis. Committed.
├── reference/   Values digitised from the deck. Committed, labelled.
└── raw/         Challenge inputs. Not committed — see below.
```

## `processed/` — the submitted results

Transcribed verbatim from the policy memo and the working project document.
These are the original analysis outputs, not regenerated numbers.

| File | Contents |
| --- | --- |
| `eng_corridor_metrics.csv` | Everything about Routes 23, 28 and 66: TDI, boardings, equity volume, runtimes, trips, revenue hours, OTP, near-rail share. The input to the fiscal model. |
| `route_equity_scorecard.csv` | Top 15 routes by equity-volume score, with TDI. |
| `service_performance.csv` | Peak runtime and on-time performance for the top equity routes. |
| `operating_service_levels.csv` | Runtime, trips and revenue hours per weekday. Operating cost is derived in code rather than stored. |
| `bus_rail_connectivity.csv` | Share of each route's boardings at stops within 400 m of rail. |
| `lodes_wage_shares.csv` | Earnings-band composition, residence and workplace sides. |
| `lodes_sector_shares.csv` | Top 10 NAICS sectors, corridor vs rest of state. |

**One column name is a warning.** `route_equity_scorecard.csv` has
`avg_weekday_boardings_uncorrected`. Partway through the event the team found
boardings had been overstated by roughly 4x and recalculated everything
downstream, but the corrected values were written down only for the three ENG
routes. The ranking is unaffected; the absolute values in that column should not
be cited. Full explanation in `docs/reproducibility.md`.

## `raw/` — not committed

The challenge datasets were provided under the event's data terms and are not
redistributed. Scripts `01` and `02` expect these filenames:

| Expected file | What it is | Where to get it |
| --- | --- | --- |
| `bus_ridership_by_stop_route.csv` | Boardings by route and stop, Fall 2023 | [MBTA Open Data Portal](https://mbta-massdot.opendata.arcgis.com/datasets/adbe3a94edcd44259cfee2621ed9f3a7_0/explore) |
| `mbta_network.gpkg` | Bus and rail stop/route geometry | [MassGIS](https://gis.data.mass.gov/maps/86e2b8d6fcf94ee2832dbb6758ee03d5/about) |
| `demographics.gpkg` | Block-group demographics | Organiser-supplied; ACS equivalent described in `docs/data-sources.md` |
| `raw_arrival_departure_times.csv` | Timepoint events with scheduled vs actual | [MBTA transit-performance](https://github.com/mbta/transit-performance) |
| `ma_rac_S000_JT00_2022.csv.gz` | LODES residence area characteristics | [LEHD](https://lehd.ces.census.gov/data/) |
| `ma_wac_S000_JT00_2022.csv.gz` | LODES workplace area characteristics | [LEHD](https://lehd.ces.census.gov/data/) |
| `tl_2020_25_tabblock20.shp` | Massachusetts 2020 census blocks | [TIGER/Line](https://catalog.data.gov/dataset/tiger-line-shapefile-current-state-massachusetts-2020-census-block) |

If you substitute your own demographics layer, update `config.TDI_COMPONENTS` to
match its column names.

Scripts write to `*_rebuilt.csv` so a rebuild sits alongside the submitted
results and can be diffed against them rather than silently replacing them.

**You do not need any of this** to run the fiscal model, the tests, or the
figures. Those work from a clean clone.
