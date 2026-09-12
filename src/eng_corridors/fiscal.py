"""The ENG corridor cost-benefit model.

This module is deliberately self-contained. It takes the published route
metrics and a :class:`~eng_corridors.config.FiscalAssumptions` instance and
returns every number quoted in the memo. No geodata, no network calls, no
hidden state, so the whole fiscal case can be re-derived and argued with.

Benefits are kept in three separate buckets, because they are not the same kind
of money and collapsing them would overstate the case:

1. **Operating savings** — real cash the MBTA stops spending, and only the half
   that is not reinvested in service counts.
2. **Rail fare revenue** — real cash the MBTA starts receiving, resting on a
   behavioural assumption chain that is stated explicitly.
3. **Rider time value** — economic benefit that never appears on the agency's
   balance sheet. Reported as a range and kept out of the payback calculation.

Payback and NPV use buckets 1 and 2 only.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

import pandas as pd

from eng_corridors.config import DEFAULT_ASSUMPTIONS, FiscalAssumptions

MINUTES_PER_HOUR = 60


# --------------------------------------------------------------------------
# Capital
# --------------------------------------------------------------------------


def capital_cost(a: FiscalAssumptions = DEFAULT_ASSUMPTIONS) -> float:
    """One-time quick-build capital cost, in dollars.

    Length times unit cost times a soft-cost multiplier. Quick-build is the
    whole point: at roughly $0.65M per treated mile this is an order of
    magnitude below a rail project and can be delivered inside a capital cycle.
    """
    return (
        a.corridor_miles
        * a.capital_cost_per_mile_musd
        * 1e6
        * a.soft_cost_multiplier
    )


# --------------------------------------------------------------------------
# Bucket 1: operating savings
# --------------------------------------------------------------------------


def operating_savings(
    routes: pd.DataFrame,
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> pd.DataFrame:
    """Per-route bus-hours and operating dollars freed by faster running.

    Holding the timetable fixed, an x% runtime cut needs x% fewer bus-hours to
    deliver the identical service. This bucket depends only on vehicle hours,
    not on how many people ride, which is what makes it the sturdiest part of
    the case.

    Requires columns ``route_id`` and ``rev_hours_per_weekday``.
    """
    _require(routes, ["route_id", "rev_hours_per_weekday"])
    out = routes[["route_id", "rev_hours_per_weekday"]].copy()

    out["bus_hours_saved_per_weekday"] = (
        out["rev_hours_per_weekday"] * a.speed_improvement
    )
    out["gross_savings_per_weekday"] = (
        out["bus_hours_saved_per_weekday"] * a.cost_per_bus_revenue_hour
    )
    out["gross_savings_per_year"] = (
        out["gross_savings_per_weekday"] * a.weekdays_per_year
    )
    out["net_savings_per_year"] = out["gross_savings_per_year"] * (
        1 - a.reinvestment_share
    )
    return out


# --------------------------------------------------------------------------
# Bucket 2: rail fare revenue
# --------------------------------------------------------------------------


def rail_revenue(
    routes: pd.DataFrame,
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> dict[str, float]:
    """Incremental rail fares from better bus-to-rail feeding.

    Three assumptions stacked in series, each of which can be argued with:
    faster buses lift boardings by ``ridership_uplift``; ``share_near_rail`` of
    those extra trips start or end within 400 m of a rail station; and
    ``new_transfer_share`` of those are genuinely new rail trips. The product is
    an effective conversion of about 25%, which is why the resulting revenue is
    the smallest of the three buckets and is presented as such.
    """
    _require(routes, ["avg_weekday_boardings"])
    baseline = float(routes["avg_weekday_boardings"].sum())

    extra_bus_trips = baseline * a.ridership_uplift
    conversion = a.share_near_rail * a.new_transfer_share
    new_rail_trips = extra_bus_trips * conversion
    revenue_per_weekday = new_rail_trips * a.avg_rail_fare

    return {
        "baseline_weekday_boardings": baseline,
        "extra_bus_trips_per_weekday": extra_bus_trips,
        "effective_conversion_rate": conversion,
        "new_rail_trips_per_weekday": new_rail_trips,
        "rail_revenue_per_weekday": revenue_per_weekday,
        "rail_revenue_per_year": revenue_per_weekday * a.weekdays_per_year,
    }


# --------------------------------------------------------------------------
# Bucket 3: rider time
# --------------------------------------------------------------------------


def rider_time_savings(
    routes: pd.DataFrame,
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> pd.DataFrame:
    """Per-route rider-hours returned to passengers.

    Each boarding is treated as one one-way trip saving ``speed_improvement`` of
    that route's average all-day runtime. This is a deliberate simplification:
    a rider who does not travel the full route saves proportionally less, so the
    per-trip figure is an upper bound on the typical journey. It is also why the
    time value is reported as a $10-$20/hour band rather than a point estimate.

    Requires ``route_id``, ``avg_trip_runtime_min`` and ``avg_weekday_boardings``.
    """
    _require(
        routes,
        ["route_id", "avg_trip_runtime_min", "avg_weekday_boardings"],
    )
    out = routes[
        ["route_id", "avg_trip_runtime_min", "avg_weekday_boardings"]
    ].copy()

    out["minutes_saved_per_trip"] = (
        out["avg_trip_runtime_min"] * a.speed_improvement
    )
    out["rider_hours_per_weekday"] = (
        out["avg_weekday_boardings"]
        * out["minutes_saved_per_trip"]
        / MINUTES_PER_HOUR
    )
    out["rider_hours_per_year"] = (
        out["rider_hours_per_weekday"] * a.weekdays_per_year
    )
    # A two-trip-a-day commuter, which is the number that lands in a room.
    out["hours_saved_per_year_daily_commuter"] = (
        out["minutes_saved_per_trip"] * 2 * a.weekdays_per_year / MINUTES_PER_HOUR
    )
    return out


# --------------------------------------------------------------------------
# Headline summary
# --------------------------------------------------------------------------


def annuity_factor(rate: float, years: int) -> float:
    """Present value of $1 a year for ``years`` years."""
    if rate == 0:
        return float(years)
    return (1 - (1 + rate) ** -years) / rate


@dataclass(frozen=True)
class FiscalSummary:
    """Headline results. All money in dollars, all hours in hours."""

    capital_cost: float
    bus_hours_saved_per_weekday: float
    gross_om_savings_per_year: float
    net_om_savings_per_year: float
    rail_revenue_per_year: float
    direct_benefit_per_year: float
    payback_years: float
    npv_10yr: float
    rider_hours_per_year: float
    rider_time_value_low: float
    rider_time_value_high: float
    capital_cost_per_annual_rider_hour: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [{"metric": k, "value": v} for k, v in self.to_dict().items()]
        )

    def __str__(self) -> str:  # pragma: no cover - presentation only
        m = 1e6
        return "\n".join(
            [
                f"Capital cost                  ${self.capital_cost / m:>8.2f}M",
                f"Bus-hours saved / weekday      {self.bus_hours_saved_per_weekday:>8.1f}",
                f"Gross O&M savings / year      ${self.gross_om_savings_per_year / m:>8.2f}M",
                f"Net O&M savings / year        ${self.net_om_savings_per_year / m:>8.2f}M",
                f"New rail revenue / year       ${self.rail_revenue_per_year / m:>8.2f}M",
                f"Direct benefit / year         ${self.direct_benefit_per_year / m:>8.2f}M",
                f"Payback                        {self.payback_years:>8.1f} years",
                f"10-year NPV                   ${self.npv_10yr / m:>8.1f}M",
                f"Rider-hours saved / year       {self.rider_hours_per_year / m:>8.2f}M",
                f"Rider time value / year       ${self.rider_time_value_low / m:>8.1f}M"
                f" - ${self.rider_time_value_high / m:.1f}M",
            ]
        )


def fiscal_summary(
    routes: pd.DataFrame,
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> FiscalSummary:
    """Run the whole model and collapse it to the headline numbers."""
    ops = operating_savings(routes, a)
    rail = rail_revenue(routes, a)
    time = rider_time_savings(routes, a)

    capex = capital_cost(a)
    net_om = float(ops["net_savings_per_year"].sum())
    rail_rev = rail["rail_revenue_per_year"]
    direct = net_om + rail_rev
    rider_hours = float(time["rider_hours_per_year"].sum())

    return FiscalSummary(
        capital_cost=capex,
        bus_hours_saved_per_weekday=float(
            ops["bus_hours_saved_per_weekday"].sum()
        ),
        gross_om_savings_per_year=float(ops["gross_savings_per_year"].sum()),
        net_om_savings_per_year=net_om,
        rail_revenue_per_year=rail_rev,
        direct_benefit_per_year=direct,
        payback_years=capex / direct,
        npv_10yr=direct * annuity_factor(a.discount_rate, a.horizon_years) - capex,
        rider_hours_per_year=rider_hours,
        rider_time_value_low=rider_hours * a.value_of_time_low,
        rider_time_value_high=rider_hours * a.value_of_time_high,
        capital_cost_per_annual_rider_hour=capex / rider_hours,
    )


# --------------------------------------------------------------------------
# Sensitivity
# --------------------------------------------------------------------------


def sensitivity(
    routes: pd.DataFrame,
    parameter: str,
    values: Iterable[float],
    a: FiscalAssumptions = DEFAULT_ASSUMPTIONS,
) -> pd.DataFrame:
    """Sweep one assumption and report how the headline numbers move.

    The honest use of this is to find the value at which the recommendation
    stops holding. For ``speed_improvement`` that turns out to be far below any
    documented bus-priority outcome, which is the real argument for the package.
    """
    if not hasattr(a, parameter):
        raise ValueError(f"unknown assumption: {parameter!r}")

    rows = []
    for value in values:
        variant = FiscalAssumptions(**{**asdict(a), parameter: value})
        s = fiscal_summary(routes, variant)
        rows.append(
            {
                parameter: value,
                "net_om_savings_per_year": s.net_om_savings_per_year,
                "rail_revenue_per_year": s.rail_revenue_per_year,
                "direct_benefit_per_year": s.direct_benefit_per_year,
                "payback_years": s.payback_years,
                "npv_10yr": s.npv_10yr,
                "rider_hours_per_year": s.rider_hours_per_year,
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------


def _require(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(
            f"route table is missing required column(s): {', '.join(missing)}"
        )
