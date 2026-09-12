"""Tests for the composite indices.

The indices are the analytical claim of the project: that ranking routes by
TDI x ridership is a defensible way to pick where to spend money. These tests
check the arithmetic behaves the way the memo says it does, and that the
published route rankings fall out of the published inputs.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from eng_corridors.config import PROCESSED
from eng_corridors.indices import (
    add_indices,
    component_ratios,
    equity_volume_score,
    population_weighted_mean,
    service_deficit_index,
    transit_dependence_index,
)


@pytest.fixture(scope="module")
def scorecard() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "route_equity_scorecard.csv")


@pytest.fixture(scope="module")
def service() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "service_performance.csv")


# --------------------------------------------------------------------------
# Weighted means
# --------------------------------------------------------------------------


def test_population_weighting_favours_larger_block_groups():
    values = pd.Series([0.10, 0.50])
    weights = pd.Series([9_000, 1_000])
    assert population_weighted_mean(values, weights) == pytest.approx(0.14)


def test_missing_values_are_dropped_pairwise():
    """A block group with no households must not drag the mean toward zero."""
    values = pd.Series([0.40, np.nan, 0.60])
    weights = pd.Series([1_000, 5_000, 1_000])
    assert population_weighted_mean(values, weights) == pytest.approx(0.50)


def test_all_missing_returns_nan():
    result = population_weighted_mean(pd.Series([np.nan]), pd.Series([100]))
    assert math.isnan(result)


def test_zero_weights_are_ignored():
    values = pd.Series([0.10, 0.90])
    weights = pd.Series([0, 500])
    assert population_weighted_mean(values, weights) == pytest.approx(0.90)


# --------------------------------------------------------------------------
# TDI
# --------------------------------------------------------------------------


def test_a_perfectly_average_route_scores_one():
    shares = {
        "pct_no_vehicle": 0.20,
        "pct_below_200fpl": 0.25,
        "pct_nonwhite": 0.30,
        "pct_transit_commute": 0.15,
    }
    ratios = component_ratios(shares, shares)
    assert transit_dependence_index(ratios) == pytest.approx(1.0)


def test_tdi_is_the_mean_of_the_component_ratios():
    ratios = {
        "pct_no_vehicle": 3.0,
        "pct_below_200fpl": 2.0,
        "pct_nonwhite": 4.0,
        "pct_transit_commute": 3.0,
    }
    assert transit_dependence_index(ratios) == pytest.approx(3.0)


def test_a_missing_component_renormalises_rather_than_penalising():
    """Three strong components should not be diluted by one absent one."""
    ratios = {
        "pct_no_vehicle": 3.0,
        "pct_below_200fpl": 3.0,
        "pct_nonwhite": 3.0,
        "pct_transit_commute": float("nan"),
    }
    assert transit_dependence_index(ratios) == pytest.approx(3.0)


def test_zero_system_share_does_not_divide_by_zero():
    ratios = component_ratios({"pct_no_vehicle": 0.2}, {"pct_no_vehicle": 0.0})
    assert math.isnan(ratios["pct_no_vehicle"])


def test_reweighting_shifts_the_score_toward_the_weighted_component():
    ratios = {
        "pct_no_vehicle": 4.0,
        "pct_below_200fpl": 1.0,
        "pct_nonwhite": 1.0,
        "pct_transit_commute": 1.0,
    }
    equal = transit_dependence_index(ratios)
    vehicle_heavy = transit_dependence_index(
        ratios,
        weights={
            "pct_no_vehicle": 0.7,
            "pct_below_200fpl": 0.1,
            "pct_nonwhite": 0.1,
            "pct_transit_commute": 0.1,
        },
    )
    assert vehicle_heavy > equal


# --------------------------------------------------------------------------
# Equity volume
# --------------------------------------------------------------------------


def test_equity_volume_is_the_product():
    assert equity_volume_score(3.0, 12_394.4) == pytest.approx(37_183.2)


def test_published_scorecard_is_internally_consistent(scorecard):
    """Every published equity-volume score should be TDI x boardings."""
    recomputed = (
        scorecard["tdi"] * scorecard["avg_weekday_boardings_uncorrected"]
    )
    # The published table rounds TDI to two decimals, so allow 1%.
    assert np.allclose(
        recomputed, scorecard["equity_volume_score"], rtol=0.01
    )


def test_eng_routes_are_the_top_three(scorecard):
    """The whole corridor selection rests on this ordering."""
    top_three = set(scorecard.nlargest(3, "equity_volume_score")["route_id"])
    assert top_three == {23, 28, 66}


def test_equity_volume_reorders_the_tdi_ranking(scorecard):
    """The product, not TDI alone, is what drives the ranking.

    Route 28 happens to top both, but the two orderings are otherwise very
    different: route 15 has the second-highest TDI in the group and still ranks
    fourteenth on equity volume, because barely anyone rides it. If these two
    rankings ever coincided, the ridership term would be doing no work.
    """
    by_tdi = list(scorecard.sort_values("tdi", ascending=False)["route_id"])
    by_ev = list(
        scorecard.sort_values("equity_volume_score", ascending=False)["route_id"]
    )
    assert by_tdi != by_ev

    tdi_rank_of_15 = by_tdi.index(15)
    ev_rank_of_15 = by_ev.index(15)
    assert tdi_rank_of_15 < 3 and ev_rank_of_15 > 10


# --------------------------------------------------------------------------
# Service deficit
# --------------------------------------------------------------------------


def test_a_median_route_scores_one_half():
    """At median runtime and median OTP, the reliability term vanishes."""
    assert service_deficit_index(34.0, 0.74) == pytest.approx(0.5)


def test_slower_routes_score_worse():
    fast = service_deficit_index(25.0, 0.78)
    slow = service_deficit_index(49.0, 0.78)
    assert slow > fast


def test_less_reliable_routes_score_worse():
    reliable = service_deficit_index(35.0, 0.80)
    unreliable = service_deficit_index(35.0, 0.70)
    assert unreliable > reliable


def test_route_66_is_the_worst_on_service_deficit(service):
    """Route 66 is the memo's headline problem route."""
    scored = add_indices(service)
    worst = scored.nlargest(1, "sdi")["route_id"].item()
    assert worst == 66


def test_runtime_dominates_the_index(service):
    """Documented limitation, asserted so it cannot be forgotten.

    The runtime term is unbounded while the reliability term is squeezed into a
    narrow band, so SDI correlates almost perfectly with raw runtime. See
    docs/reproducibility.md.
    """
    scored = add_indices(service).dropna(subset=["sdi"])
    correlation = scored["sdi"].corr(scored["avg_peak_runtime_min"])
    assert correlation > 0.98


def test_invalid_reference_values_are_rejected():
    with pytest.raises(ValueError):
        service_deficit_index(35.0, 0.75, median_runtime_min=0)
    with pytest.raises(ValueError):
        service_deficit_index(35.0, 0.75, median_otp=0)


def test_add_indices_tolerates_missing_runtime(service):
    """Route 1 has no full-trip coverage and must survive as NaN, not crash."""
    scored = add_indices(service)
    assert scored.loc[scored["route_id"] == 1, "sdi"].isna().all()
