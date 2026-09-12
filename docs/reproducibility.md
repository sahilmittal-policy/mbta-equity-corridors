# Reproducibility notes

This project was built in about 48 hours at a hackathon. The analysis notebooks
were subsequently lost. This document records exactly what has been recovered,
what has been reconstructed, and what does not reconcile.

It is here because a repository that quietly presents rebuilt code as original
artefacts is worse than useless to anyone trying to evaluate the work.

---

## What survived

| Artefact | Status |
| --- | --- |
| Submitted policy memo | Complete, with both appendix tables |
| Presentation deck | Complete, 8 slides |
| Working project document | Complete — ~1,900 lines including intermediate tables and roughly 400 lines of the original GeoPandas code |
| Jupyter notebooks | **Lost** |
| Raw challenge datasets | **Not retained** — they were provided under the event's data terms |
| Intermediate outputs (`.pkl`, `.geojson`) | **Lost** |

## What is what in this repository

| Layer | Provenance |
| --- | --- |
| `data/processed/*.csv` | **Original results.** Transcribed verbatim from the memo and working document. |
| `data/reference/*.csv` | **Digitised.** Read off a chart in the deck, accurate to roughly ±150. Labelled in the file. |
| `src/eng_corridors/fiscal.py` | **Rebuilt and verified.** Reproduces every published figure; covered by tests. |
| `src/eng_corridors/indices.py` | **Rebuilt and verified.** Formulas from the memo; reproduces the published rankings. |
| `src/eng_corridors/spatial.py` | **Reconstructed from surviving code.** The buffering, spatial joins and weighted means follow the original closely. Not re-executed — the raw geodata is gone. |
| `src/eng_corridors/service.py` | **Reconstructed from the documented method.** No surviving code; written from the memo's description of the runtime and OTP calculation. |
| `src/eng_corridors/jobs.py` | **Reconstructed from the documented method.** Same caveat. |
| `figures/` | **Regenerated** from the CSVs in this repository, not copied from the deck. |

The practical upshot: **the fiscal model is verified, the pipeline is not.**
Running `scripts/01` and `scripts/02` against the original data should reproduce
the published tables, but that has not been demonstrated and should not be
claimed. The scripts write to `*_rebuilt.csv` rather than overwriting the
submitted results precisely so that a rebuild can be diffed rather than
confused with the original.

---

## Known discrepancies

### 1. Transposed boardings in Appendix A — resolved

The submitted memo's Appendix A assigns 12,394 average weekday boardings to Route
23 and 11,273 to Route 28. Three independent checks say this is transposed:

- The working document's corrected ridership table lists Route 28 at 12,394.4 and
  Route 23 at 11,273.4.
- The rider-hours calculation pairs 12,394.4 with 8.22 minutes saved, which is
  20% of Route 28's 41.10-minute runtime, not Route 23's 36.04.
- The ridership bar chart in the deck shows Route 28 as the tallest bar.

**Resolution:** this repository uses Route 28 = 12,394, Route 23 = 11,273. The
corrected pairing is noted in `docs/policy-memo.md`. Nothing downstream changes —
the totals, and therefore every headline figure, are identical either way.

### 2. Two ridership bases in circulation — documented, not resolved

Partway through the hackathon the team found that average weekday boardings had
been overstated by a factor of roughly four, and recalculated everything
downstream. The working document records the correction in detail.

The corrected values were written down **only for the three ENG routes**. The
full top-15 table in the working document retains the pre-correction basis, even
though the deck's chart plots corrected values for all fifteen.

**Consequence:** `route_equity_scorecard.csv` carries the column name
`avg_weekday_boardings_uncorrected` as a warning. The **ranking** is unaffected —
the correction was close to monotonic, and the deck's corrected chart preserves
the same ordering — but the absolute boardings in that file should not be cited.
`data/reference/top15_boardings_digitized.csv` holds the corrected values for the
other twelve routes, digitised from the chart and labelled as approximate.

The scale factor is not uniform across routes (4.09 to 4.42), so this was not a
simple rescale. The most likely cause is a change in how boardings were
aggregated across time periods, but without the notebook this cannot be
confirmed.

### 3. The Service Deficit Index does not reproduce — unresolved

The memo states:

```
SDI_r = 0.5 · (T_r / T_median) + 0.5 · (1 − OTP_r / OTP_median)
```

with T_median ≈ 34 minutes and OTP_median ≈ 74%, and reports **SDI ≈ 1.28** for
Route 66.

That formula with those inputs gives:

```
0.5 × (48.66 / 34) + 0.5 × (1 − 0.723 / 0.74)
  = 0.716 + 0.011
  = 0.727
```

Substituting plausible alternative medians does not close the gap. A ratio-form
variant of the reliability term gets closer:

```
0.5 × (T/T_med) + 0.5 × (OTP_med/OTP_r) = 0.716 + 0.512 = 1.23
```

but still does not land on 1.28, and it is not the formula the memo states.

**Status:** unresolved. `indices.service_deficit_index()` implements the formula
**as published**, and the repository reports what that formula yields rather than
back-fitting to the reported number. The route *ordering* is unaffected — Route
66 is worst under every variant tried — and SDI was used as a supporting
diagnostic rather than a selection criterion, so no recommendation depends on it.

### 4. SDI is close to a runtime ranking — a design flaw, not a bug

Separately from the reproduction problem: OTP across MBTA bus routes varies only
from about 0.70 to 0.79, so the reliability term of the SDI occupies a band of
roughly 0.05 while the runtime term ranges over 0.27 to 0.72. The composite
therefore correlates with raw peak runtime at r > 0.98.

This is asserted in `tests/test_indices.py::test_runtime_dominates_the_index` so
that it cannot be quietly forgotten. A better version would z-score both terms
before combining them, or use a reliability measure with more spread, such as
excess wait time or the 95th percentile of headway deviation.

### 5. Sector labels were wrong in an early draft — corrected

An intermediate table in the working document mislabels the LODES CNS codes
(CNS15 shown as Accommodation & Food Services, CNS12 as Retail Trade, and so on).
The final memo has them right. `jobs.SECTOR_LABELS` uses the official LODES
mapping, and `data/processed/lodes_sector_shares.csv` follows the final memo.

### 6. Two minor arithmetic slips in intermediate tables — superseded

The working document's operating-cost table lists $39,567/weekday for Route 28,
but 131.89 revenue hours × $297 is $39,171. The later fiscal section uses the
correct value. This repository stores only revenue hours and derives cost in
code, so the slip cannot propagate.

An earlier draft also used 260 weekday service days; the submitted analysis uses
250. `config.FiscalAssumptions.weekdays_per_year` is 250.

---

## Modelling limitations

These are not errors — they are choices worth knowing about before citing
anything.

**Ridership uplift is fixed, not elastic.** The 15% boardings uplift is held
constant regardless of how much speed actually improves, so rail revenue does not
move in a speed sensitivity sweep. A proper treatment would use a service
elasticity. The effect is small: rail revenue is 15% of direct benefit.

**Every boarding is treated as a full-length trip.** Rider time savings assume
each boarding saves 20% of the *route's* runtime. Riders travelling part of the
route save proportionally less, so 1.23M rider-hours is an upper bound. This is
the main reason time value is reported as a $10–20/hour band and excluded from
payback.

**No induced demand on the cost side.** The model does not account for the
additional bus-hours needed if ridership genuinely rises 15% and crowding
requires more service. Bucket 1 assumes a fixed timetable throughout.

**Catchments are intersection-based, not area-weighted.** A block group
overlapping the corridor by 10% counts fully. Applied identically to every route,
so the bias is common-mode for ranking purposes, but absolute demographic shares
for the corridor are smoothed toward the regional mean.

**Capital cost is an order-of-magnitude estimate.** $0.5M/mile plus 30% is a
planning-level benchmark from comparable quick-build projects, not an engineer's
estimate. It carries no allowance for utility relocation, significant civil work,
or right-of-way acquisition. If real costs came in at triple the estimate,
payback would still be under six years.

---

## If you want to re-run the pipeline

You need the challenge datasets. `data/README.md` lists what each script expects
and where the public equivalents can be obtained. Two files — `demographics.gpkg`
and `mbta_network.gpkg` — were provided by the organisers as pre-processed
convenience layers; equivalent data can be assembled from ACS and MBTA GTFS, but
column names will differ and `config.TDI_COMPONENTS` will need updating.

The fiscal model and figures need none of this and run from a clean clone.
