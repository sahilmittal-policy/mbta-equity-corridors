"""Observed runtimes and on-time performance from MBTA arrival/departure records.

The performance feed is one row per timepoint event, not per trip, so a trip's
runtime has to be reconstructed by grouping on ``half_trip_id`` and taking the
span between its first and last observed event. Two consequences worth knowing:

* A trip whose first or last timepoint was never recorded yields a runtime that
  is too short. Route 1 dropped out of the runtime table for exactly this
  reason and is reported as missing rather than as fast.
* Runtime here is *observed*, not scheduled. That is the point. The gap between
  the two is the delay the corridor package is trying to remove.
"""

from __future__ import annotations

import pandas as pd

from eng_corridors.config import OTP_THRESHOLD_MIN, TIME_PERIODS

SECONDS_PER_MINUTE = 60


def load_arrival_departure(path) -> pd.DataFrame:
    """Load the raw event feed and parse timestamps."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    for column in ("actual", "scheduled"):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    df["route_id"] = df["route_id"].astype(str)
    return df.dropna(subset=["actual"])


def classify_time_period(hour: int) -> str:
    """Bucket an hour of the day. Anything outside the named bands is off-peak."""
    for name, hours in TIME_PERIODS.items():
        if hour in hours:
            return name
    return "off_peak"


def trip_runtimes(events: pd.DataFrame) -> pd.DataFrame:
    """Collapse timepoint events into one runtime per trip.

    Trips with a single recorded event are dropped: a zero-length span is a
    data gap, not a instantaneous bus.
    """
    required = {"half_trip_id", "service_date", "actual", "route_id"}
    missing = required - set(events.columns)
    if missing:
        raise KeyError(f"event feed is missing {sorted(missing)}")

    grouped = events.groupby(["route_id", "service_date", "half_trip_id"])
    trips = grouped.agg(
        first_time=("actual", "min"),
        last_time=("actual", "max"),
        n_events=("actual", "size"),
    ).reset_index()

    trips = trips[trips["n_events"] > 1]
    trips["runtime_min"] = (
        trips["last_time"] - trips["first_time"]
    ).dt.total_seconds() / SECONDS_PER_MINUTE
    trips["departure_hour"] = trips["first_time"].dt.hour
    trips["time_period"] = trips["departure_hour"].map(classify_time_period)
    trips["is_peak"] = trips["time_period"].isin(["am_peak", "pm_peak"])

    # Guard against clock artefacts and trips that span midnight badly.
    return trips[(trips["runtime_min"] > 0) & (trips["runtime_min"] < 240)]


def on_time_performance(
    events: pd.DataFrame,
    threshold_min: int = OTP_THRESHOLD_MIN,
) -> pd.DataFrame:
    """Share of events arriving within the threshold of schedule, by route and period.

    Defined on absolute deviation, so a bus five minutes early is as much a
    failure as one five minutes late. For a headway-based rider that is the
    right call: an early bus is a bus you missed.
    """
    if "scheduled" not in events.columns:
        raise KeyError("event feed has no 'scheduled' column; cannot compute OTP")

    df = events.dropna(subset=["scheduled"]).copy()
    df["deviation_min"] = (
        df["actual"] - df["scheduled"]
    ).dt.total_seconds().abs() / SECONDS_PER_MINUTE
    df["on_time"] = df["deviation_min"] <= threshold_min
    df["time_period"] = df["actual"].dt.hour.map(classify_time_period)
    df["is_peak"] = df["time_period"].isin(["am_peak", "pm_peak"])

    out = (
        df.groupby(["route_id", "is_peak"])["on_time"]
        .mean()
        .unstack()
        .rename(columns={True: "otp_peak", False: "otp_offpeak"})
    )
    out.columns.name = None
    return out.reset_index()


def route_service_table(events: pd.DataFrame) -> pd.DataFrame:
    """Per-route peak runtime, all-day runtime, trip counts and OTP.

    ``avg_trips_per_weekday`` is derived from the event feed rather than GTFS,
    so it reflects service actually operated, including dropped trips.
    """
    trips = trip_runtimes(events)

    peak = (
        trips[trips["is_peak"]]
        .groupby("route_id")["runtime_min"]
        .mean()
        .rename("avg_peak_runtime_min")
    )
    allday = (
        trips.groupby("route_id")["runtime_min"]
        .mean()
        .rename("avg_trip_runtime_min")
    )
    trips_per_day = (
        trips.groupby(["route_id", "service_date"])
        .size()
        .groupby("route_id")
        .mean()
        .rename("avg_trips_per_weekday")
    )

    table = pd.concat([peak, allday, trips_per_day], axis=1).reset_index()
    table["rev_hours_per_weekday"] = (
        table["avg_trip_runtime_min"] / 60 * table["avg_trips_per_weekday"]
    )

    return table.merge(on_time_performance(events), on="route_id", how="left")


def operating_cost(
    service: pd.DataFrame,
    boardings: pd.DataFrame | None = None,
    cost_per_revenue_hour: float = 297.0,
) -> pd.DataFrame:
    """Daily operating cost, and cost per rider where boardings are available.

    Cost per rider is the metric that reframes these routes politically: the
    ENG routes are not expensive per passenger, they are cheap. Slowness is
    what makes them expensive per *hour*.
    """
    out = service.copy()
    out["operating_cost_per_weekday"] = (
        out["rev_hours_per_weekday"] * cost_per_revenue_hour
    )

    if boardings is not None:
        out = out.merge(boardings, on="route_id", how="left")
        out["cost_per_rider_weekday"] = (
            out["operating_cost_per_weekday"] / out["avg_weekday_boardings"]
        )
    return out
