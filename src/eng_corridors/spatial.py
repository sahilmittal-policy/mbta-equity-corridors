"""Corridor catchments and the route-level Transit Dependence Index.

Needs the challenge geodata in ``data/raw/``. ``geopandas`` is imported lazily
so the rest of the package stays usable without a GDAL stack.

The unit of analysis is the *stop catchment*: buffer every stop a route serves
by 800 m, union them, and take the block groups that intersect. That is coarser
than an areal-interpolated corridor but it is what a rider's walkshed actually
looks like, and it is robust to the block-group boundaries not lining up with
the street the bus runs on.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from eng_corridors.config import (
    CORRIDOR_BUFFER_M,
    METRIC_CRS,
    RAIL_BUFFER_M,
    TDI_COMPONENTS,
)
from eng_corridors.indices import (
    component_ratios,
    population_weighted_mean,
    transit_dependence_index,
)

if TYPE_CHECKING:  # pragma: no cover
    import geopandas as gpd


def _gpd():
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "This step needs geopandas. Install the geo extras:\n"
            "    pip install -r requirements-geo.txt"
        ) from exc
    return gpd


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_weekday_bus_ridership(path) -> pd.DataFrame:
    """Stop-level average weekday boardings by route.

    The MBTA portal file carries every mode and day type. Mode 3 is bus. Rows
    are one per route/stop/time-period, so boardings are summed over time
    periods to get a stop-day total.
    """
    rid = pd.read_csv(path)
    rid.columns = [c.strip().lower() for c in rid.columns]

    bus = rid[rid["mode"].astype(str).str.strip().isin(["3", "bus", "Bus"])]
    weekday = bus[bus["day_type_name"].str.lower().str.strip() == "weekday"]

    if weekday.empty:
        raise ValueError(
            "No weekday bus rows found. Check the 'mode' and 'day_type_name' "
            "codings in your download; the portal has changed them before."
        )

    out = weekday.copy()
    out["route_id"] = out["route_id"].astype(str)
    out["stop_id"] = out["stop_id"].astype(str)
    return out


def route_boardings(bus_weekday: pd.DataFrame) -> pd.DataFrame:
    """Average weekday boardings per route."""
    return (
        bus_weekday.groupby("route_id", as_index=False)["ons_all_trips"]
        .sum()
        .rename(columns={"ons_all_trips": "avg_weekday_boardings"})
    )


def load_bus_stops(path, layer: str = "bus_stops_gtfs") -> gpd.GeoDataFrame:
    """Bus stop geometries, reprojected to a metric CRS so buffers mean metres."""
    gpd = _gpd()
    stops = gpd.read_file(path, layer=layer)
    stops["stop_id"] = stops["stop_id"].astype(str)
    return stops.to_crs(METRIC_CRS)


def load_demographics(path, layer: str = "blockgroup") -> gpd.GeoDataFrame:
    """Block-group demographics with the four TDI shares computed.

    Denominators are replaced with NaN where zero rather than filled, so an
    empty block group contributes nothing to a weighted mean instead of
    contributing a spurious zero.
    """
    gpd = _gpd()
    dem = gpd.read_file(path, layer=layer).to_crs(METRIC_CRS)

    for share, (numerator, denominator) in TDI_COMPONENTS.items():
        missing = [c for c in (numerator, denominator) if c not in dem.columns]
        if missing:
            raise KeyError(
                f"demographics layer is missing {missing}; "
                f"available columns: {sorted(dem.columns)[:20]}..."
            )
        dem[share] = dem[numerator] / dem[denominator].replace(0, np.nan)

    return dem


# --------------------------------------------------------------------------
# Catchments
# --------------------------------------------------------------------------


def route_catchment(
    route_id: str,
    bus_weekday: pd.DataFrame,
    stops: gpd.GeoDataFrame,
    buffer_m: int = CORRIDOR_BUFFER_M,
):
    """Unioned buffer around every stop served by one route."""
    from shapely.ops import unary_union

    stop_ids = set(
        bus_weekday.loc[
            bus_weekday["route_id"].astype(str) == str(route_id), "stop_id"
        ].astype(str)
    )
    route_stops = stops[stops["stop_id"].isin(stop_ids)]
    if route_stops.empty:
        return None
    return unary_union(route_stops.geometry.buffer(buffer_m).values)


def system_shares(dem: gpd.GeoDataFrame) -> dict[str, float]:
    """Population-weighted shares across the whole service area.

    This is the denominator that makes a TDI of 1.0 mean "average route".
    """
    weights = dem["population_2020"]
    return {
        share: population_weighted_mean(dem[share], weights)
        for share in TDI_COMPONENTS
    }


def catchment_shares(
    geometry,
    dem: gpd.GeoDataFrame,
) -> dict[str, float] | None:
    """Population-weighted shares for the block groups a catchment touches."""
    gpd = _gpd()
    catchment = gpd.GeoDataFrame(geometry=[geometry], crs=dem.crs)
    hit = gpd.sjoin(dem, catchment, how="inner", predicate="intersects")
    if hit.empty:
        return None

    # A block group can be picked up more than once if the catchment is a
    # multipolygon; keep one row each so it is not double-weighted.
    hit = hit[~hit.index.duplicated(keep="first")]

    weights = hit["population_2020"]
    return {
        share: population_weighted_mean(hit[share], weights)
        for share in TDI_COMPONENTS
    }


def build_route_tdi_table(
    bus_weekday: pd.DataFrame,
    stops: gpd.GeoDataFrame,
    dem: gpd.GeoDataFrame,
    buffer_m: int = CORRIDOR_BUFFER_M,
) -> pd.DataFrame:
    """TDI, boardings and equity-volume score for every bus route.

    This is the expensive step: one spatial join per route, roughly 150 routes.
    Expect a few minutes.
    """
    baseline = system_shares(dem)
    boardings = route_boardings(bus_weekday).set_index("route_id")

    rows = []
    for route_id in sorted(bus_weekday["route_id"].astype(str).unique()):
        geometry = route_catchment(route_id, bus_weekday, stops, buffer_m)
        if geometry is None:
            warnings.warn(
                f"route {route_id}: no stops matched, skipping", stacklevel=2
            )
            continue

        shares = catchment_shares(geometry, dem)
        if shares is None:
            warnings.warn(
                f"route {route_id}: catchment hit no block groups", stacklevel=2
            )
            continue

        ratios = component_ratios(shares, baseline)
        rows.append(
            {
                "route_id": route_id,
                "tdi": transit_dependence_index(ratios),
                **shares,
                **{f"{k}_ratio": v for k, v in ratios.items()},
            }
        )

    table = pd.DataFrame(rows).merge(
        boardings, left_on="route_id", right_index=True, how="left"
    )
    table["equity_volume_score"] = table["tdi"] * table["avg_weekday_boardings"]
    return table.sort_values("equity_volume_score", ascending=False).reset_index(
        drop=True
    )


# --------------------------------------------------------------------------
# Bus-rail connectivity
# --------------------------------------------------------------------------


def near_rail_share(
    bus_weekday: pd.DataFrame,
    stops: gpd.GeoDataFrame,
    network_path,
    buffer_m: int = RAIL_BUFFER_M,
    rail_layers: tuple[str, ...] = ("rapid_transit_stops", "commuter_rail_stops"),
) -> pd.DataFrame:
    """Share of each route's boardings at stops within walking distance of rail.

    A proxy for transfer potential, and the mechanism behind the rail-revenue
    bucket in the fiscal model: if half a route's boardings already happen next
    to a rail station, speeding up that route feeds the rail network.
    """
    gpd = _gpd()
    from shapely.ops import unary_union

    rail_geoms = []
    for layer in rail_layers:
        rail = gpd.read_file(network_path, layer=layer).to_crs(METRIC_CRS)
        rail_geoms.extend(rail.geometry.buffer(buffer_m).values)
    rail_buffer = unary_union(rail_geoms)

    stops = stops.copy()
    stops["near_rail"] = stops.geometry.intersects(rail_buffer)

    joined = bus_weekday.merge(
        stops[["stop_id", "near_rail"]], on="stop_id", how="left"
    )
    joined["near_rail"] = joined["near_rail"].fillna(False)

    totals = joined.groupby("route_id")["ons_all_trips"].sum()
    near = (
        joined[joined["near_rail"]].groupby("route_id")["ons_all_trips"].sum()
    )

    out = pd.DataFrame(
        {"total_boardings": totals, "boardings_near_rail": near}
    ).fillna({"boardings_near_rail": 0})
    out["share_near_rail"] = out["boardings_near_rail"] / out["total_boardings"]
    return out.reset_index().sort_values("share_near_rail", ascending=False)
