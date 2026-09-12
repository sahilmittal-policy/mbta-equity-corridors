"""The three composite indices used to pick corridors.

None of these touch the raw geodata. They take already-aggregated shares or
route metrics, which makes them cheap to test and easy to re-weight.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from eng_corridors.config import (
    SDI_MEDIAN_OTP,
    SDI_MEDIAN_RUNTIME_MIN,
    TDI_WEIGHTS,
)


def population_weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Population-weighted mean that ignores block groups with missing values.

    Block groups with zero households or zero population produce NaN shares
    upstream. Dropping them pairwise keeps one sparse component from wiping out
    an otherwise valid route.
    """
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return float("nan")
    v, w = values[mask], weights[mask]
    return float((v * w).sum() / w.sum())


def component_ratios(
    route_shares: Mapping[str, float],
    system_shares: Mapping[str, float],
) -> dict[str, float]:
    """Express each route share as a multiple of the system-wide share.

    A ratio of 1.0 means the route's catchment looks like the MBTA service area
    on that dimension. This normalisation is what lets four quantities measured
    in different units be averaged at all.
    """
    ratios = {}
    for key, route_value in route_shares.items():
        system_value = system_shares.get(key)
        if not system_value:
            ratios[key] = float("nan")
        else:
            ratios[key] = route_value / system_value
    return ratios


def transit_dependence_index(
    ratios: Mapping[str, float],
    weights: Mapping[str, float] | None = None,
) -> float:
    """Weighted mean of the normalised component ratios.

    TDI = 1.0 is an average MBTA bus route. The ENG routes score 2.5-3.0, i.e.
    their catchments are roughly three times as transit-dependent as the system
    average across no-vehicle, low-income, non-white and transit-commute shares.
    """
    weights = dict(weights or TDI_WEIGHTS)
    usable = {k: v for k, v in ratios.items() if not np.isnan(v) and k in weights}
    if not usable:
        return float("nan")

    # Renormalise over the components that survived, so a route missing one
    # component is not silently penalised.
    total_weight = sum(weights[k] for k in usable)
    return sum(usable[k] * weights[k] for k in usable) / total_weight


def equity_volume_score(tdi: float, avg_weekday_boardings: float) -> float:
    """TDI multiplied by ridership.

    TDI alone rewards small routes through very poor neighbourhoods; boardings
    alone reward busy routes through wealthy ones. The product asks a blunter
    question: where are the most equity-weighted riders? That is the ranking
    that put routes 28, 23 and 66 at the top of the network.
    """
    return tdi * avg_weekday_boardings


def service_deficit_index(
    runtime_min: float,
    otp: float,
    median_runtime_min: float = SDI_MEDIAN_RUNTIME_MIN,
    median_otp: float = SDI_MEDIAN_OTP,
) -> float:
    """How far a route's service falls short of the top-route median.

    Half speed, half reliability::

        SDI = 0.5 * (T / T_median) + 0.5 * (1 - OTP / OTP_median)

    Higher is worse. Note that the runtime term is unbounded above while the
    reliability term is compressed into a narrow range, so in practice SDI is
    driven mostly by runtime. See docs/reproducibility.md for the consequences.
    """
    if median_runtime_min <= 0 or median_otp <= 0:
        raise ValueError("median reference values must be positive")
    speed_term = runtime_min / median_runtime_min
    reliability_term = 1 - (otp / median_otp)
    return 0.5 * speed_term + 0.5 * reliability_term


def add_indices(
    routes: pd.DataFrame,
    runtime_col: str = "avg_peak_runtime_min",
    otp_col: str = "otp_peak",
    tdi_col: str = "tdi",
    boardings_col: str = "avg_weekday_boardings",
) -> pd.DataFrame:
    """Attach equity-volume and service-deficit columns to a route table."""
    out = routes.copy()
    if tdi_col in out and boardings_col in out:
        out["equity_volume_score"] = out[tdi_col] * out[boardings_col]
    if runtime_col in out and otp_col in out:
        out["sdi"] = [
            service_deficit_index(t, o) if pd.notna(t) and pd.notna(o) else np.nan
            for t, o in zip(out[runtime_col], out[otp_col], strict=False)
        ]
    return out
