# Data sources

Every dataset used, what it provided, and where to get it.

Nothing in `data/raw/` is committed. The challenge datasets were provided under
the event's terms and some are large; the public equivalents are listed below.

---

## Transit operations

**MBTA Bus Ridership by Time Period, Season, Route/Line and Stop** — Fall 2023
Average weekday boardings by route and stop, split by time period. Source of
`avg_weekday_boardings` and, joined to stop geometry, of the near-rail boardings
share.
<https://mbta-massdot.opendata.arcgis.com/datasets/adbe3a94edcd44259cfee2621ed9f3a7_0/explore>

Relevant fields: `mode` (3 = bus), `route_id`, `stop_id`, `day_type_name`,
`ons_all_trips`, `average_ons`.

**MBTA Transit Performance System** — raw arrival/departure times, 2023
One row per timepoint event with `scheduled` and `actual` timestamps. Source of
observed runtimes, trips per weekday, and on-time performance.
<https://github.com/mbta/transit-performance>

Relevant fields: `route_id`, `direction_id`, `half_trip_id`, `service_date`,
`stop_id`, `scheduled`, `actual`.

**MBTA GTFS (2023)**
`routes.txt`, `trips.txt`, `stop_times.txt` for scheduled runtimes and trip
counts, used as a cross-check on the performance feed.
<https://www.mbta.com/developers/gtfs>

**MBTA Network GeoPackage**
Layers: `bus_routes_gtfs`, `bus_stops_gtfs`, `rapid_transit_routes`,
`rapid_transit_stops`, `commuter_rail_routes`, `commuter_rail_stops`. Source of
all stop geometry, corridor buffers and the 400 m rail buffers.
<https://gis.data.mass.gov/maps/86e2b8d6fcf94ee2832dbb6758ee03d5/about>

Provided by the organisers as `mbta_network.gpkg`. Reprojected to EPSG:26986
(NAD83 / Massachusetts Mainland, metres) before any buffering.

---

## Demographics

**Pre-processed block-group demographics** — `demographics.gpkg`
Provided by the organisers, built on ACS and the 2020 Census. Layers
`blockgroup` and `place`. Source of all four TDI components.

Fields used: `population_2020`, `vehicles_0inHousehold`,
`vehicles_householdTotal`, `income_200PercentPoverty`,
`race_hispanicOrNonWhite`, `commute_transit`, `commute_workersTotal`.

An equivalent can be assembled from ACS 5-year tables — B08201 (vehicles
available), C17002 (ratio of income to poverty level), B03002 (Hispanic or Latino
origin by race), B08301 (means of transportation to work) — but column names will
differ and `config.TDI_COMPONENTS` needs updating to match.

**US Census TIGER/Line, Massachusetts 2020 census blocks**
Block geometry for the LODES join.
<https://catalog.data.gov/dataset/tiger-line-shapefile-current-state-massachusetts-2020-census-block>

---

## Employment

**LEHD LODES, Massachusetts, 2019–2022**
Origin–Destination (OD), Residence Area Characteristics (RAC) and Workplace Area
Characteristics (WAC). Block-level job counts by NAICS sector (`CNS01`–`CNS20`)
and monthly earnings band (`CE01`–`CE03`).
<https://lehd.ces.census.gov/data/>

Used for the wage composition of corridor residents, the sector mix on both the
residence and workplace sides, and the job containment rate.

Note: block geocodes are 15-digit strings with meaningful leading zeros. Read
them as text. `jobs.load_lodes()` enforces this.

---

## Costs and benchmarks

**National Transit Database, 2022 operating expenses**
Source of the **$297 per bus revenue hour** figure. Large urban bus systems sit
in the $250–320 range.
<https://www.transit.dot.gov/ntd/data-product/2022-operating-expenses>

**City of Boston, Free Route 23, 28 and 29 Bus Program** — mid-program report
Fare-free pilot context and observed dwell-time reductions.
<https://www.boston.gov/departments/transportation/free-route-23-28-and-29-bus-program>

**Summer Street Bus/Truck Lane Pilot** — BTD, 2024
Boston-specific evidence on quick-build lane performance and enforcement.
<https://www.boston.gov/sites/default/files/file/2024/09/BTD_TTOC_Summer%20Street%20Report%202024%20Final.pdf>

**LivableStreets Alliance, *64 Hours: Closing the Bus Equity Gap*** (2019)
Source of the 64-hour racial gap in annual bus travel time.

**TransitMatters dashboard**
Used during the event to sanity-check route speeds and headways.
<https://dashboard.transitmatters.org/>

---

## Assumptions not drawn from a dataset

These are judgement calls, held in `config.FiscalAssumptions` with a source
comment on each.

| Assumption | Value | Basis |
| --- | --- | --- |
| Runtime reduction | 20% | Midpoint of the 10–25% range in comparable bus-priority projects |
| Quick-build cost | $0.5M/mile | Columbus Avenue and comparable quick-build benchmarks |
| Soft-cost multiplier | 1.30 | Signals, TSP hardware, stop works, design |
| Reinvestment share | 50% | Policy choice, not a measurement |
| Ridership uplift | 15% | Columbus Avenue and fare-free Route 28 experience |
| New-transfer conversion | 50% of near-rail | Conservative judgement; the weakest link in the model |
| Blended rail fare | $1.70 | After passes and discounts |
| Discount rate | 4% real | Standard for public infrastructure appraisal |
| Value of time | $10–20/hour | Reported as a band, excluded from payback |
| Weekday service days | 250 | Weekend service treated as upside |

---

## Licensing

MBTA open data is published under the MBTA's open data terms. Census and LEHD
products are US Government works in the public domain. NTD data is published by
the Federal Transit Administration. The pre-processed `demographics.gpkg` and
`mbta_network.gpkg` were supplied for the event and are not redistributed here.
