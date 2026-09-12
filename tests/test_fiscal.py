"""The fiscal model must keep reproducing what was submitted.

These tests are the reason the repository exists in this form. The original
notebooks are gone; the published numbers are not. Pinning the model to those
numbers means any future refactor that quietly changes the answer fails loudly.

Tolerances are the rounding precision of the memo, not arbitrary slack.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from eng_corridors.config import DEFAULT_ASSUMPTIONS, PROCESSED, FiscalAssumptions
from eng_corridors.fiscal import (
    annuity_factor,
    capital_cost,
    fiscal_summary,
    operating_savings,
    rail_revenue,
    rider_time_savings,
    sensitivity,
)

MILLION = 1e6


@pytest.fixture(scope="module")
def routes() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "eng_corridor_metrics.csv")


# --------------------------------------------------------------------------
# Published headline figures
# --------------------------------------------------------------------------


def test_capital_cost_is_6_5_million():
    assert capital_cost() == pytest.approx(6.5 * MILLION)


def test_bus_hours_saved_matches_memo(routes):
    ops = operating_savings(routes)
    assert ops["bus_hours_saved_per_weekday"].sum() == pytest.approx(85.1, abs=0.1)


def test_gross_and_net_operating_savings(routes):
    ops = operating_savings(routes)
    assert ops["gross_savings_per_year"].sum() == pytest.approx(
        6.32 * MILLION, rel=0.01
    )
    assert ops["net_savings_per_year"].sum() == pytest.approx(
        3.16 * MILLION, rel=0.01
    )


def test_rail_revenue_about_half_a_million(routes):
    rail = rail_revenue(routes)
    assert rail["baseline_weekday_boardings"] == pytest.approx(35_017, abs=1)
    assert rail["extra_bus_trips_per_weekday"] == pytest.approx(5_252, abs=1)
    assert rail["new_rail_trips_per_weekday"] == pytest.approx(1_339, abs=5)
    assert rail["rail_revenue_per_year"] == pytest.approx(0.56 * MILLION, rel=0.03)


def test_rider_hours_about_1_23_million(routes):
    time = rider_time_savings(routes)
    assert time["rider_hours_per_weekday"].sum() == pytest.approx(4_904, abs=5)
    assert time["rider_hours_per_year"].sum() == pytest.approx(
        1.23 * MILLION, rel=0.01
    )


@pytest.mark.parametrize(
    "route_id,minutes",
    [("23", 7.21), ("28", 8.22), ("66", 9.79)],
)
def test_per_route_minutes_saved(routes, route_id, minutes):
    time = rider_time_savings(routes).set_index("route_id")
    assert time.loc[int(route_id), "minutes_saved_per_trip"] == pytest.approx(
        minutes, abs=0.01
    )


def test_headline_summary(routes):
    s = fiscal_summary(routes)
    assert s.direct_benefit_per_year == pytest.approx(3.7 * MILLION, rel=0.02)
    assert 1.5 < s.payback_years < 2.0, "memo claims payback under two years"
    assert s.npv_10yr == pytest.approx(23.5 * MILLION, rel=0.03)
    assert s.rider_time_value_low == pytest.approx(12.3 * MILLION, rel=0.02)
    assert s.rider_time_value_high == pytest.approx(24.5 * MILLION, rel=0.02)


def test_capital_cost_per_annual_rider_hour(routes):
    """The appendix metric: about $5.3 of capital per annual rider-hour saved."""
    s = fiscal_summary(routes)
    assert s.capital_cost_per_annual_rider_hour == pytest.approx(5.3, abs=0.2)


# --------------------------------------------------------------------------
# Model behaviour
# --------------------------------------------------------------------------


def test_annuity_factor_matches_textbook():
    assert annuity_factor(0.04, 10) == pytest.approx(8.1109, abs=1e-4)
    assert annuity_factor(0.0, 10) == 10.0


def test_reinvesting_everything_removes_the_operating_benefit(routes):
    a = FiscalAssumptions(reinvestment_share=1.0)
    s = fiscal_summary(routes, a)
    assert s.net_om_savings_per_year == pytest.approx(0.0)
    # Rail fares alone still repay the capital, just far more slowly.
    assert s.payback_years > 10


def test_benefits_scale_linearly_with_speed_improvement(routes):
    half = fiscal_summary(routes, FiscalAssumptions(speed_improvement=0.10))
    full = fiscal_summary(routes, FiscalAssumptions(speed_improvement=0.20))
    assert full.net_om_savings_per_year == pytest.approx(
        2 * half.net_om_savings_per_year
    )
    assert full.rider_hours_per_year == pytest.approx(2 * half.rider_hours_per_year)


def test_case_survives_a_pessimistic_scenario(routes):
    """Halve the speed gain, cut the ridership response, raise the discount rate."""
    pessimistic = FiscalAssumptions(
        speed_improvement=0.10,
        ridership_uplift=0.05,
        discount_rate=0.08,
        cost_per_bus_revenue_hour=250.0,
    )
    s = fiscal_summary(routes, pessimistic)
    assert s.payback_years < 5
    assert s.npv_10yr > 0


def test_sensitivity_sweep_shape(routes):
    sweep = sensitivity(routes, "speed_improvement", [0.10, 0.15, 0.20])
    assert len(sweep) == 3
    assert sweep["payback_years"].is_monotonic_decreasing


def test_sensitivity_rejects_unknown_parameter(routes):
    with pytest.raises(ValueError, match="unknown assumption"):
        sensitivity(routes, "not_a_real_knob", [1, 2])


# --------------------------------------------------------------------------
# Guard rails
# --------------------------------------------------------------------------


def test_missing_columns_fail_loudly(routes):

    with pytest.raises(KeyError, match="rev_hours_per_weekday"):
        operating_savings(routes.drop(columns=["rev_hours_per_weekday"]))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"speed_improvement": 0.0},
        {"speed_improvement": 1.5},
        {"reinvestment_share": -0.1},
        {"weekdays_per_year": 0},
    ],
)
def test_invalid_assumptions_are_rejected(kwargs):
    with pytest.raises(ValueError):
        FiscalAssumptions(**kwargs)


def test_default_assumptions_are_immutable():
    """Shared defaults must not be mutable, or one caller could silently
    change every other caller's model."""
    with pytest.raises(FrozenInstanceError):
        DEFAULT_ASSUMPTIONS.speed_improvement = 0.5  # type: ignore[misc]
