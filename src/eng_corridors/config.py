"""Paths and modelling assumptions.

Every number the analysis assumes rather than measures lives here, with a
source. Nothing downstream should hard-code a constant.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
REFERENCE = DATA / "reference"
FIGURES = ROOT / "figures"

# Files expected in data/raw/ if you want to re-run the selection pipeline.
RAW_FILES = {
    "ridership": RAW / "bus_ridership_by_stop_route.csv",
    "network": RAW / "mbta_network.gpkg",
    "demographics": RAW / "demographics.gpkg",
    "arrivals": RAW / "raw_arrival_departure_times.csv",
    "lodes_rac": RAW / "ma_rac_S000_JT00_2022.csv.gz",
    "lodes_wac": RAW / "ma_wac_S000_JT00_2022.csv.gz",
    "blocks": RAW / "tl_2020_25_tabblock20.shp",
}

# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------

#: NAD83 / Massachusetts Mainland, in metres. Buffers are meaningless in 4326.
METRIC_CRS = "EPSG:26986"

#: Catchment radius around each bus stop for demographic aggregation.
CORRIDOR_BUFFER_M = 800

#: Radius around a rail station within which a bus stop counts as a feeder.
RAIL_BUFFER_M = 400

#: The three routes designated as the ENG corridor.
ENG_ROUTES = ("23", "28", "66")

# --------------------------------------------------------------------------
# Transit Dependence Index
# --------------------------------------------------------------------------

#: The four demographic components, mapped to their block-group numerator and
#: denominator columns in ``demographics.gpkg``.
TDI_COMPONENTS = {
    "pct_no_vehicle": ("vehicles_0inHousehold", "vehicles_householdTotal"),
    "pct_below_200fpl": ("income_200PercentPoverty", "population_2020"),
    "pct_nonwhite": ("race_hispanicOrNonWhite", "population_2020"),
    "pct_transit_commute": ("commute_transit", "commute_workersTotal"),
}

#: Component weights. The submitted analysis used equal weights; an earlier
#: draft weighted vehicle access and income more heavily. See
#: docs/reproducibility.md.
TDI_WEIGHTS = {
    "pct_no_vehicle": 0.25,
    "pct_below_200fpl": 0.25,
    "pct_nonwhite": 0.25,
    "pct_transit_commute": 0.25,
}

# --------------------------------------------------------------------------
# Service performance
# --------------------------------------------------------------------------

#: On-time if actual arrival is within this many minutes of schedule. Matches
#: the band MBTA uses in its own performance reporting.
OTP_THRESHOLD_MIN = 5

#: Hour-of-day bands applied to a trip's first timepoint departure.
TIME_PERIODS = {
    "am_peak": range(7, 10),
    "midday": range(10, 16),
    "pm_peak": range(16, 19),
}

#: Reference values for the Service Deficit Index, taken as the median across
#: the top equity-volume routes.
SDI_MEDIAN_RUNTIME_MIN = 34.0
SDI_MEDIAN_OTP = 0.74

# --------------------------------------------------------------------------
# Fiscal model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FiscalAssumptions:
    """Assumptions behind the cost-benefit case.

    Defaults reproduce the figures in the submitted memo. Every field can be
    overridden to run a sensitivity case:

    >>> FiscalAssumptions(speed_improvement=0.15)
    """

    #: Runtime reduction delivered by the full bus-priority package. Empirical
    #: range from comparable projects is 10-25%; 20% is the central case.
    speed_improvement: float = 0.20

    #: Fully-loaded MBTA bus operating cost per revenue hour. NTD 2022;
    #: large-system peers sit in the $250-320 band.
    cost_per_bus_revenue_hour: float = 297.0

    #: Weekday service days per year. Weekend service is upside, not counted.
    weekdays_per_year: int = 250

    #: Share of freed bus-hours ploughed back into frequency, recovery time and
    #: evening/weekend priority rather than banked as savings.
    reinvestment_share: float = 0.50

    #: Quick-build bus lane cost: paint, posts, signal software.
    capital_cost_per_mile_musd: float = 0.5

    #: Treated length: ~6 mi on the 23/28 spine plus ~4 mi of route 66.
    corridor_miles: float = 10.0

    #: Uplift for signals, TSP hardware, stop works and design.
    soft_cost_multiplier: float = 1.30

    #: Boardings uplift from faster, more reliable service. Consistent with the
    #: Columbus Avenue centre-running lanes and comparable pilots.
    ridership_uplift: float = 0.15

    #: Corridor-weighted share of boardings at stops within 400 m of rail.
    share_near_rail: float = 0.51

    #: Of the extra near-rail boardings, the share that become genuinely new
    #: rail transfers rather than trips that would have happened anyway.
    new_transfer_share: float = 0.50

    #: Blended average rail fare after passes and discounts.
    avg_rail_fare: float = 1.70

    #: Real discount rate for the NPV.
    discount_rate: float = 0.04

    #: NPV horizon in years.
    horizon_years: int = 10

    #: Low and high values of rider time, used as a range rather than a point
    #: estimate because these are not MBTA revenues.
    value_of_time_low: float = 10.0
    value_of_time_high: float = 20.0

    def __post_init__(self) -> None:
        if not 0 < self.speed_improvement < 1:
            raise ValueError("speed_improvement must be a fraction between 0 and 1")
        if not 0 <= self.reinvestment_share <= 1:
            raise ValueError("reinvestment_share must be between 0 and 1")
        if self.weekdays_per_year <= 0:
            raise ValueError("weekdays_per_year must be positive")


DEFAULT_ASSUMPTIONS = FiscalAssumptions()
