# Building an Equitable Network Growth (ENG) Corridor

**Memorandum**
**To:** Massachusetts Bay Transportation Authority
**From:** Team TartanSparks — Anushri Gade, Rahul Tejannavar, Sahil Mittal
**Date:** 23 November 2025
**Event:** MIT Policy Hackathon 2025, Transportation track (second place)

> This is the memo as submitted, converted to markdown. Wording is unchanged
> except for formatting and one corrected table (see the note in Appendix A).
> The accompanying slides are in [`slides/`](slides/).

---

## Executive summary

This memo evaluates underserved MBTA bus routes by analysing the demographics of
affected neighbourhoods and assessing service reliability through bus speeds,
wait times, and total commute time. Based on these findings, we propose policy
changes to improve transit equity and performance across the MBTA bus network.
We make the following recommendations:

- **Implement a bus-priority package targeting at least a 15–20% runtime
  reduction** for Routes 23, 28 and 66, consisting of:
  - **Dedicated bus lanes** to reduce travel times and avoid traffic congestion.
  - **Transit Signal Priority (TSP)** to reduce red-light delays.
  - **Queue jumps** at central bottlenecks, giving buses a bus-only head start.
  - **Far-side stops and stop consolidation** to reduce dwell and stop time.
- **Invest the resulting time savings** into service improvements and toward
  offsetting the MBTA's projected $600–700 million operating gap.

The recommendations are supported by a fiscal analysis covering implementation
costs, funding mechanisms and return on investment.

## Context

Greater Boston's bus network carries the region's most transit-dependent riders
on some of its slowest and least reliable services. Bus riders in communities of
colour and low-income neighbourhoods spend dramatically more time travelling
than white riders, losing up to 64 hours a year simply getting to work and to
services such as health care, education and childcare.[^64hours] These service
inequities reduce socio-economic mobility; addressing them would improve access
to education, employment and essential services.

Previous efforts to improve bus service proposed a plan that could have raised
ridership by 8.4% and cut travel times by four minutes for riders in underserved
communities. That proposal was rejected over funding constraints, concerns about
parking loss, and failed negotiations with elected officials.

Many routes — including those already running fare-free — continue to experience
unreliable service, producing persistent inequities in the bus system. There is a
need for policy recommendations that address inequity and operational efficiency
together.

We identify Routes 23, 28 and 66 as the key concern: high ridership, high transit
dependence, slow and unreliable operations, and strong connectivity to the rail
network. Addressing 23 and 28 mattered to us precisely *because* they are already
fare-free. Unreliable service undermines the benefit of free fares; riders pay
nothing but still face unpredictable schedules and difficult access to essential
services.

ENG corridor residents are more likely to hold low- and mid-wage jobs than the
Massachusetts average, and are over-represented in health care, education and
professional services linked to major hospitals and campuses. Jobs located *in*
the corridor are slightly higher-paying, reflecting those anchors, but only about
one-quarter of employment held by ENG residents is actually inside the corridor.
Roughly three-quarters of workers commute beyond it, so faster and more reliable
bus service has job-access impacts well beyond the corridor itself.

## Recommendations

We designate Routes 23, 28 and 66 as an **Equitable Network Growth (ENG)
corridor** on the basis of high ridership, high inequity index, and slow,
unreliable service, and recommend a bus-priority package:

- **Dedicated bus lanes in congested areas.** Cities across the US, Canada and
  Europe have used this to cut runtimes by up to 20%. New York's Select Bus
  Service reduced journey times by 10–20%.[^sbs] London[^tfl] and
  France[^civitas] show increased ridership and rider satisfaction where lanes
  were implemented thoroughly.
- **Transit Signal Priority.** An approaching bus communicates with the traffic
  signal to extend a green or turn it green early. Implementations in Los
  Angeles and Seattle cut travel time without adverse effects on cross-street
  traffic.
- **Queue jumps:** short dedicated lanes plus a bus-only signal phase giving
  buses a head start at busy intersections.
- **Far-side stops and stop consolidation** to reduce run times, delays and
  total travel time. Pittsburgh[^prt] and Montreal[^consolidation] have seen
  improved on-time performance and reduced dwell times after consolidation.
  Far-side stops, common in Portland and Toronto, let buses clear intersections
  before stopping, reducing conflicts with turning vehicles.

We further recommend **reinvesting efficiency gains**, allocating at least half
of the time savings to increased peak and evening frequency, with the remainder
offsetting the MBTA's $600–700 million annual operating gap. The corridor would
be financed through low-capital quick-build investments — paint, posts and signal
software — estimated at **$0.5 million per mile**, supplemented by FTA Small
Starts, CMAQ, city budgets, and value capture near nodes such as Nubian and
Longwood.

## Analysis

The analysis uses two indices to quantify need and service quality.

### Transit Dependence Index

The TDI measures how reliant the population near a bus route is on public
transit, using four variables collected at census tract / block-group level in a
400–800 m buffer around each route:

- share of households with no vehicle
- share of population below 200% of the Federal Poverty Line
- share of non-white residents
- share of workers who commute by transit

For each route *r*, the TDI averages the ratio of the route's rate to the
system-wide bus average for each of the four categories *k*:

```
TDI_r = ¼ · (R_r,no_vehicle + R_r,low_income + R_r,non_white + R_r,transit_commute)
```

This compares each route against the system average rather than against absolute
numbers. **A TDI of 2.0 means the population served is twice as transit-dependent
as the average rider.**

### Equity Volume Score

```
EV_r = TDI_r × AvgWeekdayBoardings_r
```

This focuses investment on high-need routes that also generate high ridership.
**Routes 28, 23 and 66 rank #1, #2 and #3 among non-fare-free candidates,**
indicating the highest concentration of equity-weighted riders in the network.

### Service Deficit Index

The SDI captures how far a route's service falls short of the median performance
of the system's top routes. It is a weighted average of a runtime ratio (speed)
and an on-time performance ratio (reliability):

```
SDI_r = 0.5 · (T_r / T_median) + 0.5 · (1 − OTP_r / OTP_median)
```

where *T_median* ≈ 34 minutes and *OTP_median* ≈ 74% among top routes. A higher
SDI means worse service. All three ENG routes have above-median delays, with
Route 66 worst. **The highest-need routes are also the ones struggling most with
service quality**, which is what justifies targeted improvement.

> See [`reproducibility.md`](reproducibility.md) on the SDI: the formula as
> written above does not reproduce the value reported in the original analysis.

## Financial case, payback and funding

Quick-build bus lanes cost roughly **$0.5M per mile**. Using recent MBTA projects
as a guide, an ENG package assumes $0.5M/mi plus about 30% for signals, TSP,
stops and design.

Treating Routes 23 and 28 as ~6 miles of overlapping or adjacent segments and
Route 66 as ~4 miles of high-delay segments gives **~10 miles of priority
treatment**: a base cost of ~$5.0M, or **~$6.5M with overhead**.

### Operating and maintenance savings

With full bus-priority treatment we assume a **20% runtime reduction**. Holding
the timetable constant, this translates directly into fewer bus-hours for the
same service. The three routes consume about **425.65 revenue hours per
weekday**; a 20% improvement frees roughly **85.1 bus-hours per day**, worth
about **$25,284 per weekday** at $297 per revenue hour. Over 250 weekday service
days that is approximately **$6.32 million per year**.

It is more realistic to monetise only part of this. Reinvesting roughly half of
the saved hours into higher frequencies, better recovery time, or extending
priority into evenings and weekends leaves **net O&M savings of about $3.16
million per year** while still improving service quality.

### Additional rail revenue

Roughly half of all boardings on Routes 23, 28 and 66 occur at stops within about
400 m of a rapid transit or commuter rail station.

Drawing on Columbus Avenue and comparable bus-priority projects, we assume faster
and more reliable service yields a **15% increase in bus boardings**, or about
5,252 additional trips per weekday. About 51% of these occur near rail stations,
and about half of those represent genuinely new bus–rail transfers — an effective
conversion of roughly 25%, or about **1,313 additional rail boardings per
weekday**.

At a conservative blended fare of $1.70, that is about **$2,232 per weekday**, or
approximately **$0.56 million per year**.

### Payback and NPV

Combining net O&M savings (~$3.16M/yr) with additional rail revenue (~$0.56M/yr)
gives a total direct fiscal benefit of roughly **$3.7 million per year** against
a one-time capital cost of $6.5 million.

- **Simple payback: 1.8 years.** On direct O&M and fare revenue alone, the
  package repays in under two years.
- Over a 10-year horizon at a 4% discount rate (annuity factor ≈ 8.11), the
  present value of the annual benefit is about $30.0M. Subtracting capital gives
  a **10-year NPV of roughly $23.5 million** in direct MBTA financial benefits.

### Indirect benefits: rider time

A 20% runtime reduction saves riders between about 7 and 10 minutes per one-way
trip, or approximately **4,900 rider-hours per weekday** and **1.23 million
rider-hours per year**. These do not appear on the MBTA's balance sheet but are a
significant economic benefit. At $10/hour that is about $12.3 million a year; at
$20/hour, about $24.5 million. **A 20% speed increase yields roughly $12–24
million in time value each year** on top of the MBTA's direct fiscal gains.

### Funding

A blend of federal transit funds (FTA CMAQ, Small Starts, Bus and Bus
Facilities), state and MBTA capital aligned with climate and workforce-access
objectives, City of Boston transportation capital dedicated to bus priority, and
targeted value capture or institutional contributions from the major hospitals
and universities whose employees and students use the corridor.

## Alternatives

Designating and investing in the ENG corridor was chosen because it addresses
equity, ridership and fiscal health together. Unlike previous fragmented
approaches, this plan focuses on measurable runtime reductions reinvested into
service frequency, directly addressing reliability and equity for the most
transit-dependent communities.

What makes the approach effective is its explicit connection to employment access
and its pragmatic financing through low-capital quick-build investment backed by
targeted grants. Prior efforts have lacked this data-driven targeting and
financial pragmatism, producing limited or temporary improvement.

The opportunity cost of the status quo:

- **Lost operating savings** of approximately $3.1 million a year on the bus
  system alone.
- **Lost rail revenue** of approximately $0.56 million a year from transfers that
  never happen.
- **Lost rider time** of roughly 1.23 million rider-hours a year, worth about
  $12–24 million annually.

---

## Appendix A — Full metric table for ENG routes

**Table 1: Consolidated metrics for Routes 23, 28 and 66**

| Metric | Route 23 | Route 28 | Route 66 |
| --- | ---: | ---: | ---: |
| TDI | 2.98 | 3.00 | 2.48 |
| Average weekday boardings | 11,273 | 12,394 | 11,349 |
| Equity–volume score | 33,609 | 37,147 | 28,157 |
| Average peak runtime (min) | 35.39 | 40.38 | 48.66 |
| Peak on-time performance | 0.775 | 0.764 | 0.723 |
| Off-peak on-time performance | 0.802 | 0.782 | 0.707 |
| Average trip runtime, all day (min) | 36.04 | 41.10 | 48.94 |

> **Correction.** The submitted memo transposed the boardings and equity–volume
> figures for Routes 23 and 28. The values above are the corrected pairing,
> confirmed by the ridership chart in the deck and by the rider-hours
> calculation. See [`reproducibility.md`](reproducibility.md).

## Appendix B — Jobs and wages

RAC job counts for residents of ENG corridor blocks, compared with all other
Massachusetts residents. Jobs are grouped into monthly earnings buckets: **CE01**
below $1,250, **CE02** $1,250–3,333, **CE03** above $3,333.

**Table 2: Wages of jobs held by ENG corridor residents vs the rest of Massachusetts**

| Group | Total jobs | CE01 share | CE02 share | CE03 share |
| --- | ---: | ---: | ---: | ---: |
| ENG corridor residents | 116,347 | **0.134** | **0.215** | 0.651 |
| Rest of Massachusetts residents | 3,040,664 | 0.123 | 0.197 | **0.680** |

**Table 3: Main sectors of jobs held by ENG corridor residents (top 10)**

| Sector | Name | Corridor jobs | Rest of MA | Corridor share | Rest share |
| --- | --- | ---: | ---: | ---: | ---: |
| CNS16 | Health Care & Social Assistance | 23,698 | 501,686 | **0.204** | 0.165 |
| CNS15 | Education Services | 16,964 | 325,003 | **0.146** | 0.107 |
| CNS12 | Professional, Scientific & Technical Services | 14,636 | 330,639 | **0.126** | 0.109 |
| CNS18 | Accommodation & Food Services | 9,134 | 217,834 | 0.079 | 0.072 |
| CNS07 | Retail Trade | 8,991 | 287,645 | 0.077 | 0.095 |
| CNS14 | Admin & Support, Waste Mgmt & Remediation | 6,713 | 152,629 | 0.058 | 0.050 |
| CNS10 | Finance & Insurance | 5,694 | 155,122 | 0.049 | 0.051 |
| CNS20 | Public Administration | 4,683 | 130,343 | 0.040 | 0.043 |
| CNS19 | Other Services (excl. Public Admin) | 4,060 | 94,094 | 0.035 | 0.031 |
| CNS09 | Information | 3,834 | 92,691 | 0.033 | 0.030 |

---

## References

- CIVITAS (2019). *Introducing dedicated bus lanes.*
- Diab, E. I., & El-Geneidy, A. (2015). The far side story: measuring the benefits
  of bus stop location on transit performance. *Transportation Research Record*, 2538.
- El-Geneidy, A. M., Strathman, J. G., Kimpel, T. J., & Crout, D. T. (2006).
  Effects of bus stop consolidation on passenger activity and transit operations.
  *Transportation Research Record*, 1971, 32–41.
- LivableStreets Alliance (2019). *64 Hours: Closing the Bus Equity Gap.*
- MTA (2024). *Select Bus Service: performance evaluation.*
- Pittsburgh Regional Transit. *Bus stop consolidation program.*
- Transport for London (2021). *Bus priority in London.*

Data sources are listed in [`data-sources.md`](data-sources.md).

[^64hours]: LivableStreets Alliance (2019), *64 Hours: Closing the Bus Equity Gap*, p. 7.
[^sbs]: MTA (2024), *Select Bus Service: performance evaluation.*
[^tfl]: Transport for London (2021), *Bus priority in London.*
[^civitas]: CIVITAS (2019), *Introducing dedicated bus lanes.*
[^prt]: Pittsburgh Regional Transit, *Bus stop consolidation program.*
[^consolidation]: El-Geneidy et al. (2006), *Transportation Research Record* 1971, 32–41.
