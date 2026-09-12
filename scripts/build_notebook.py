"""Build and execute notebooks/01_fiscal_model_walkthrough.ipynb.

Kept as a build script so the notebook is generated from a single source of
truth rather than hand-edited and drifting.
"""

import nbformat as nbf
from nbclient import NotebookClient

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md(
        """# The ENG corridor fiscal case, step by step

**MBTA bus routes 23, 28 and 66 — MIT Policy Hackathon 2025, second place**

This notebook walks through the cost-benefit model behind the memo's headline
claims: a $6.5 million quick-build bus-priority package on three routes, paying
back in under two years and returning 1.23 million rider-hours a year.

It needs no raw data. Everything comes from the published route metrics in
`data/processed/` plus the assumptions in `eng_corridors.config`.

The structure follows the model's three benefit buckets, which are kept separate
because they are not the same kind of money:

1. **Operating savings** — cash the MBTA stops spending
2. **Rail fare revenue** — cash the MBTA starts receiving
3. **Rider time** — economic benefit that never touches the agency's books

Payback and NPV use buckets 1 and 2 only."""
    ),
    code(
        """import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent / "src"))

import pandas as pd
import numpy as np

from eng_corridors.config import DEFAULT_ASSUMPTIONS, FiscalAssumptions, PROCESSED
from eng_corridors import fiscal, viz

pd.set_option("display.float_format", "{:,.2f}".format)
viz.use_house_style()"""
    ),
    md(
        """## The three routes

Everything downstream rests on this table. `tdi` and `equity_volume_score` are
what selected these routes out of the whole network; `rev_hours_per_weekday` and
`avg_weekday_boardings` are what drive the money."""
    ),
    code(
        """routes = pd.read_csv(PROCESSED / "eng_corridor_metrics.csv")
routes"""
    ),
    md(
        """A TDI of 3.00 means Route 28's catchment is three times as
transit-dependent as the MBTA service area average, across no-vehicle,
low-income, non-white and transit-commute shares.

These three routes rank **first, second and third on equity volume out of the
entire MBTA bus network** — and they are also among the slowest. That
coincidence is the whole argument."""
    ),
    md(
        """## Assumptions

Every number the model assumes rather than measures, in one frozen dataclass.
Nothing is hard-coded downstream, so any of these can be challenged and the
whole case re-run."""
    ),
    code(
        """for key, value in DEFAULT_ASSUMPTIONS.__dict__.items():
    print(f"{key:<32} {value}")"""
    ),
    md(
        """## Capital cost

Roughly 6 miles of overlapping segments on the 23/28 spine plus 4 miles of
high-delay segments on route 66. Quick-build — paint, posts and signal software
— at the $0.5M/mile benchmark from comparable projects, plus 30% for signals,
TSP hardware, stop works and design."""
    ),
    code(
        """capex = fiscal.capital_cost()
print(f"{DEFAULT_ASSUMPTIONS.corridor_miles:.0f} mi "
      f"x ${DEFAULT_ASSUMPTIONS.capital_cost_per_mile_musd}M/mi "
      f"x {DEFAULT_ASSUMPTIONS.soft_cost_multiplier} = ${capex/1e6:.2f}M")"""
    ),
    md(
        """## Bucket 1 — Operating savings

The sturdiest part of the case, because it depends only on vehicle hours and not
at all on how many people ride.

Hold the timetable fixed. A 20% runtime cut means 20% fewer bus-hours are needed
to deliver the identical service."""
    ),
    code(
        """ops = fiscal.operating_savings(routes)
ops"""
    ),
    code(
        """print(f"Bus-hours freed per weekday   {ops['bus_hours_saved_per_weekday'].sum():,.1f}")
print(f"Gross savings per year        ${ops['gross_savings_per_year'].sum()/1e6:,.2f}M")
print(f"Net after 50% reinvestment    ${ops['net_savings_per_year'].sum()/1e6:,.2f}M")"""
    ),
    md(
        """Half the freed hours are assumed reinvested into frequency, recovery
time and extending priority into evenings and weekends. That is a **policy
choice, not a measurement**, and it halves the headline number. We made it
because a proposal that banks 100% of savings is not credible to an agency under
service pressure — and because reinvestment is what riders actually feel."""
    ),
    md(
        """## Bucket 2 — Rail fare revenue

Three assumptions in series. This is the weakest link in the analysis, which is
why it is also the smallest bucket.

Faster buses lift boardings 15% (Columbus Avenue and comparable pilots) → 51% of
those extra trips start or end within 400 m of rail → half of those are
genuinely new rail transfers. An effective conversion of about 25%."""
    ),
    code(
        """rail = fiscal.rail_revenue(routes)
for key, value in rail.items():
    print(f"{key:<34} {value:>14,.2f}")"""
    ),
    md(
        """The case does not depend on this. Set rail revenue to zero and
payback is still 2.1 years."""
    ),
    code(
        """no_rail = fiscal.fiscal_summary(routes, FiscalAssumptions(ridership_uplift=1e-9))
print(f"Payback with no rail benefit at all: {no_rail.payback_years:.1f} years")"""
    ),
    md(
        """## Bucket 3 — Rider time

Not agency money. Reported separately and excluded from payback, because mixing
societal benefit into a payback calculation is how cost-benefit analyses get
dismissed by the people who have to sign off on them."""
    ),
    code(
        """time = fiscal.rider_time_savings(routes)
time"""
    ),
    code(
        """total_hours = time["rider_hours_per_year"].sum()
print(f"Rider-hours per weekday   {time['rider_hours_per_weekday'].sum():,.0f}")
print(f"Rider-hours per year      {total_hours/1e6:,.2f}M")
print(f"At $10/hour               ${total_hours*10/1e6:,.1f}M")
print(f"At $20/hour               ${total_hours*20/1e6:,.1f}M")"""
    ),
    md(
        """For someone riding both ways, five days a week, that is **60 to 82
hours a year** — one and a half to two working weeks returned to them.

One caveat that matters: each boarding is treated as one one-way trip saving the
full proportional runtime. A rider not travelling the whole route saves
proportionally less, so this is an **upper bound on the typical journey**. That
is why it is reported as a $10–20 band rather than a point estimate."""
    ),
    md("""## Putting it together"""),
    code(
        """summary = fiscal.fiscal_summary(routes)
print(summary)"""
    ),
    code("""fig_dir = Path.cwd().parent / "figures"
viz.plot_payback(routes, fig_dir)
from IPython.display import Image
Image(str(fig_dir / "fig04_payback.png"))"""),
    md(
        """## Does it survive pessimism?

The interesting question is not what the model says at the central case. It is
how far you have to push the assumptions before the recommendation stops
holding."""
    ),
    code(
        """sweep = fiscal.sensitivity(routes, "speed_improvement", np.arange(0.05, 0.31, 0.05))
out = sweep.copy()
for col in ["net_om_savings_per_year", "rail_revenue_per_year",
            "direct_benefit_per_year", "npv_10yr"]:
    out[col] = out[col] / 1e6
out["rider_hours_per_year"] = out["rider_hours_per_year"] / 1e6
out"""
    ),
    code(
        """# How weak can the speed gain be before payback exceeds five years?
fine = fiscal.sensitivity(routes, "speed_improvement", np.arange(0.03, 0.21, 0.005))
threshold = fine[fine["payback_years"] <= 5]["speed_improvement"].min()
print(f"Payback stays under 5 years down to a {threshold:.1%} runtime reduction.")
print("Documented range for comparable bus-priority projects: 10-25%.")"""
    ),
    md(
        """Now a deliberately hostile scenario: halve the speed gain, cut the
ridership response to a third, raise the discount rate to 8%, and use the bottom
of the NTD operating-cost range."""
    ),
    code(
        """pessimistic = FiscalAssumptions(
    speed_improvement=0.10,
    ridership_uplift=0.05,
    discount_rate=0.08,
    cost_per_bus_revenue_hour=250.0,
)
print(fiscal.fiscal_summary(routes, pessimistic))"""
    ),
    md(
        """Still under five years, still a positive NPV. This scenario is
asserted in `tests/test_fiscal.py` so it cannot silently stop being true.

## What would actually change the answer

Not the speed assumption — the model is robust there. The things that would
matter:

- **Capital cost being badly wrong.** At 3x the estimate, payback goes to about
  five years. Quick-build costs are well benchmarked, but utility relocation or
  significant civil work would break this.
- **The reinvestment share.** At 100% reinvestment there are no banked savings
  and only the rail revenue repays the capital. That is a legitimate policy
  position, and the model should be able to say so honestly.
- **Induced demand on the cost side.** If ridership really rises 15%, crowding
  may require more service, which is a cost the model does not carry.

All three are in `docs/reproducibility.md` under modelling limitations."""
    ),
    code(
        """for share in [0.0, 0.25, 0.50, 0.75, 1.0]:
    s = fiscal.fiscal_summary(routes, FiscalAssumptions(reinvestment_share=share))
    payback = f"{s.payback_years:.1f} yr" if s.payback_years < 50 else "never"
    print(f"reinvest {share:>4.0%}   benefit ${s.direct_benefit_per_year/1e6:.2f}M/yr"
          f"   payback {payback:>7}   NPV ${s.npv_10yr/1e6:>6.1f}M")"""
    ),
    md(
        """---

Full methodology in [`docs/methodology.md`](../docs/methodology.md). Known
discrepancies and limitations in
[`docs/reproducibility.md`](../docs/reproducibility.md)."""
    ),
]

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3.11"},
}

out = "notebooks/01_fiscal_model_walkthrough.ipynb"
client = NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": "notebooks/"}})
client.execute()
nbf.write(nb, out)
print(f"executed and wrote {out}")
