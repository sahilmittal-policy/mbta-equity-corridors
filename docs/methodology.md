# Methodology

How the corridor was chosen and how the fiscal case was built. The short version
is four steps: find who needs the bus most, find who gets the worst service,
check the two overlap, then price the fix.

---

## 1. Who needs the bus most?

### The unit of analysis

Transit equity questions are usually asked about *places*, but service is
delivered to *routes*. Bridging the two means defining a catchment.

We buffer every stop a route serves by **800 m**, union the buffers, and take
every census block group that intersects the result. Eight hundred metres is a
ten-minute walk and is the standard walkshed in transit planning literature.

This is deliberately coarser than areal interpolation. A block group that
overlaps the catchment by 10% counts the same as one fully inside it. We accepted
that because the alternative introduces an assumption of uniform population
density within block groups that is demonstrably false in Boston, and because the
index is used comparatively — every route is measured the same way, so the bias
is common-mode.

### The four components

| Component | Numerator | Denominator | Why |
| --- | --- | --- | --- |
| No vehicle | `vehicles_0inHousehold` | `vehicles_householdTotal` | Households with no car have no alternative when the bus fails |
| Below 200% FPL | `income_200PercentPoverty` | `population_2020` | 200% FPL rather than 100% captures the working poor, who commute |
| Non-white | `race_hispanicOrNonWhite` | `population_2020` | The documented 64-hour racial gap in Boston bus travel time |
| Transit commute | `commute_transit` | `commute_workersTotal` | Revealed dependence, not just demographic proxy |

Each is aggregated to the catchment as a **population-weighted mean**, so a block
group of 3,000 people counts three times as much as one of 1,000. Block groups
with a zero denominator produce `NaN` and are dropped pairwise rather than
treated as zero — otherwise an empty industrial block group would drag a
catchment's no-vehicle share toward zero.

### Normalisation

The four components are in different units and have wildly different base rates.
Averaging raw shares would silently weight whichever component happens to have
the largest numbers. So each is expressed as a **ratio to the system-wide
population-weighted share**:

```
R_x,r = p_x,r / p̄_x
```

A ratio of 1.0 means the route's catchment looks like the MBTA service area on
that dimension.

### The index

```
TDI_r = ¼ · (R_no_vehicle + R_low_income + R_non_white + R_transit_commute)
```

Equal weights. An earlier draft weighted vehicle access and income at 0.3 each
and the other two at 0.2; the submitted version used equal weights, which is what
`config.TDI_WEIGHTS` encodes. `indices.transit_dependence_index()` accepts custom
weights so the choice can be tested rather than assumed.

**Reading it:** TDI = 1.0 is an average route. The ENG routes score 2.48–3.00,
meaning their catchments are roughly two and a half to three times as
transit-dependent as the system average.

---

## 2. Turning need into priority

TDI alone is a bad investment criterion. It would rank a lightly-used shuttle
through a very poor neighbourhood above a trunk route carrying ten thousand
people a day. Ridership alone is equally bad — it rewards busy routes through
affluent areas.

The **Equity Volume Score** is the product:

```
EV_r = TDI_r × avg_weekday_boardings_r
```

It asks a blunter question: *where are the most equity-weighted riders?* That is
the quantity a transit agency with a fixed capital budget should be maximising.

The product reorders the TDI ranking substantially. Route 15 has the second
highest TDI of the top fifteen and ranks fourteenth on equity volume, because
barely anyone rides it. Routes 28, 23 and 66 come out first, second and third in
the entire bus network. That result is what made the corridor selection an
analytical finding rather than an assertion.

---

## 3. Who gets the worst service?

### Reconstructing runtimes

The MBTA performance feed is one row per **timepoint event**, not per trip. A
trip's runtime has to be rebuilt by grouping on `half_trip_id` and `service_date`
and taking the span between the first and last observed event.

Two consequences:

- A trip missing its first or last timepoint yields a runtime that is too short.
  Route 1 dropped out of the runtime table entirely for this reason and is
  reported as **missing rather than fast** — an important distinction, since
  Route 1 is in fact one of the slowest routes in the system.
- Runtimes here are **observed, not scheduled**. The gap between the two is
  exactly the delay the corridor package removes.

Trips with a single event, a non-positive runtime, or a runtime above four hours
are dropped as data artefacts.

### On-time performance

```
OTP = share of events where |actual − scheduled| ≤ 5 minutes
```

Defined on **absolute** deviation, so a bus five minutes early counts as a
failure. For a rider arriving at a stop on a schedule, an early bus is a bus you
missed. This matches the band MBTA uses in its own reporting.

Trips are bucketed by the departure hour of their first timepoint: AM peak 7–9,
midday 10–15, PM peak 16–18, everything else off-peak.

### Service Deficit Index

```
SDI_r = 0.5 · (T_r / T_median) + 0.5 · (1 − OTP_r / OTP_median)
```

with medians taken across the top equity-volume routes (≈34 min, ≈74%). Higher is
worse.

**Known limitation, asserted in the test suite:** the runtime term is unbounded
above while the reliability term is compressed into a very narrow band, because
OTP across MBTA bus routes only varies from about 0.70 to 0.79. SDI therefore
correlates with raw peak runtime at r > 0.98 — it is close to a runtime ranking
wearing a composite-index costume. It was used as a supporting diagnostic rather
than as a selection criterion, which limits the damage, but a future version
should standardise both terms before combining them. See
[`reproducibility.md`](reproducibility.md).

---

## 4. Bus–rail connectivity

Rapid transit and commuter rail stops are buffered by **400 m**; any bus stop
intersecting the union is flagged `near_rail`. Boardings are then split by that
flag and aggregated by route.

```
ShareNearRail_r = boardings at near-rail stops / total boardings on route r
```

905 of 7,147 bus stops fall within 400 m of rail. On the ENG routes the share of
*boardings* is far higher than the share of stops — 43–60% — because near-rail
stops are the busy ones. This is the empirical basis for the rail-revenue bucket
in the fiscal model: these routes are already feeders, so speeding them up feeds
the rail network.

---

## 5. Job access

Two LODES questions, kept deliberately apart:

- **Residence side (RAC):** what work do people who *live* on the corridor do?
  This is who the bus serves.
- **Workplace side (WAC):** what jobs are *located* on the corridor? This is who
  the bus delivers workers to.

Corridor blocks are 2020 census blocks within the 800 m catchment — 2,204 blocks,
about 2% of Massachusetts. Shares are computed within each group's own total, so
the comparison is composition, not size; comparing raw counts between 2% of a
state and the other 98% would say nothing.

The finding that carried the memo came from putting both sides together with the
origin–destination file. The corridor is a **major job centre** — over 69,000
health and social assistance jobs, nearly 58,000 accommodation and food service
jobs — and yet only about **one quarter** of the jobs held by corridor residents
are inside it. Corridor residents work at more than 12,000 distinct workplace
blocks.

That containment rate is the most load-bearing number in the argument. It is why
the intervention is framed as a network improvement rather than a local one: most
riders are passing through to somewhere else, usually via a rail transfer.

---

## 6. The fiscal model

Three benefit buckets, kept separate because they are not the same kind of money.

### Bucket 1 — Operating savings

Holding the timetable fixed, a 20% runtime cut needs 20% fewer bus-hours to
deliver identical service.

```
bus_hours_saved = Σ_r rev_hours_r × 0.20            = 85.1 h/weekday
gross savings   = 85.1 × $297 × 250 weekdays        = $6.32M/year
net savings     = gross × (1 − 0.50 reinvestment)   = $3.16M/year
```

This bucket depends only on vehicle hours, not on how many people ride, which is
what makes it the sturdiest part of the case. **Half is assumed reinvested** in
frequency, recovery time and extending priority to evenings and weekends. That
assumption is a policy choice, not a measurement, and halves the headline number
— we made it because a proposal that banks 100% of savings is not credible to an
agency under service pressure.

### Bucket 2 — Rail fare revenue

Three assumptions in series, each arguable:

```
extra bus trips  = 35,017 boardings × 15% uplift    = 5,252/weekday
near rail        × 51%
genuinely new    × 50%                              → 25% effective conversion
new rail trips   = 1,313/weekday
revenue          = 1,313 × $1.70 × 250              = $0.56M/year
```

The 15% uplift comes from Columbus Avenue and comparable pilots. The conversion
chain is the weakest link in the whole analysis, which is why this is the
smallest bucket and why the case does not depend on it: even at zero rail
revenue, payback is 2.1 years.

### Bucket 3 — Rider time

```
minutes saved/trip = route runtime × 0.20           = 7.2 to 9.8 min
rider-hours/weekday = Σ_r boardings × minutes / 60  = 4,904
rider-hours/year                                    = 1.23M
value at $10-$20/hour                               = $12.3M - $24.5M
```

Each boarding is treated as one one-way trip saving the full proportional
runtime. A rider not travelling the full route saves proportionally less, so this
is an **upper bound on the typical journey** — which is why it is reported as a
band and, more importantly, why it is **excluded from payback and NPV entirely**.
It is a societal benefit, not agency cash, and mixing the two is how cost-benefit
analyses get dismissed.

### Payback and NPV

```
capital       = 10 mi × $0.5M/mi × 1.30 soft costs  = $6.5M
direct benefit = $3.16M + $0.56M                    = $3.72M/year
payback        = 6.5 / 3.72                         = 1.75 years
NPV(10y, 4%)   = 3.72 × 8.111 − 6.5                 = $23.7M
```

Buckets 1 and 2 only.

### Sensitivity

`fiscal.sensitivity()` sweeps any single assumption. The result that matters: the
package still pays back inside **five years at a 5% runtime reduction**, which is
well below the bottom of the 10–25% range documented for comparable projects. The
recommendation does not hinge on the optimistic end of the evidence.

One modelling simplification to be aware of when reading a speed sweep: the
ridership uplift is held fixed at 15% rather than scaled with the speed gain, so
rail revenue is flat across the sweep. This understates benefit at high speed
gains and overstates it at low ones.
