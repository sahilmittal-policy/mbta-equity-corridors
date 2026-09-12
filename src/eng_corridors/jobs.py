"""Job access using LEHD LODES.

Two questions, deliberately kept apart, because conflating them is the usual
way corridor job analysis goes wrong:

**Residence side (RAC)** — what kind of work do people who *live* on the
corridor do? This is who the bus serves.

**Workplace side (WAC)** — what kind of jobs are *located* on the corridor?
This is who the bus delivers workers to.

The answer that mattered for the memo came from putting them together: the
corridor is a large health-and-education job centre, yet only about a quarter
of the jobs held by corridor residents are inside it. Most riders are passing
through to somewhere else, usually via a rail transfer, which is why a bus-only
framing understates the benefit.
"""

from __future__ import annotations

import pandas as pd

#: LODES monthly earnings bands.
WAGE_BANDS = {
    "CE01": "Low wage (< $1,250/month)",
    "CE02": "Mid wage ($1,250-3,333/month)",
    "CE03": "High wage (> $3,333/month)",
}

#: NAICS sector labels for the LODES CNS columns.
SECTOR_LABELS = {
    "CNS01": "Agriculture, Forestry, Fishing & Hunting",
    "CNS02": "Mining, Quarrying, Oil & Gas Extraction",
    "CNS03": "Utilities",
    "CNS04": "Construction",
    "CNS05": "Manufacturing",
    "CNS06": "Wholesale Trade",
    "CNS07": "Retail Trade",
    "CNS08": "Transportation & Warehousing",
    "CNS09": "Information",
    "CNS10": "Finance & Insurance",
    "CNS11": "Real Estate, Rental & Leasing",
    "CNS12": "Professional, Scientific & Technical Services",
    "CNS13": "Management of Companies & Enterprises",
    "CNS14": "Admin & Support, Waste Mgmt & Remediation",
    "CNS15": "Education Services",
    "CNS16": "Health Care & Social Assistance",
    "CNS17": "Arts, Entertainment & Recreation",
    "CNS18": "Accommodation & Food Services",
    "CNS19": "Other Services (excl. Public Admin)",
    "CNS20": "Public Administration",
}


def load_lodes(path, geo_column: str = "h_geocode") -> pd.DataFrame:
    """Load a LODES RAC or WAC file, keeping the geocode as a string.

    Census block geocodes are fifteen-digit identifiers with meaningful leading
    zeros. Reading them as integers silently corrupts every block in a state
    whose FIPS code starts with zero, which is most of New England.
    """
    df = pd.read_csv(path, dtype={geo_column: str})
    df[geo_column] = df[geo_column].str.zfill(15)
    return df


def tag_corridor_blocks(
    lodes: pd.DataFrame,
    corridor_block_ids: set[str],
    geo_column: str = "h_geocode",
) -> pd.DataFrame:
    """Flag each LODES row as inside or outside the corridor catchment."""
    out = lodes.copy()
    out["in_corridor"] = out[geo_column].isin(corridor_block_ids)
    return out


def wage_composition(tagged: pd.DataFrame, basis: str = "residence") -> pd.DataFrame:
    """Share of jobs in each earnings band, corridor vs rest of state."""
    label_in = (
        "ENG corridor residents"
        if basis == "residence"
        else "Jobs located in ENG corridor"
    )
    label_out = (
        "Rest of Massachusetts residents"
        if basis == "residence"
        else "Jobs located outside ENG corridor"
    )

    rows = []
    for flag, label in ((True, label_in), (False, label_out)):
        subset = tagged[tagged["in_corridor"] == flag]
        total = float(subset["C000"].sum())
        row = {"basis": basis, "group": label, "total_jobs": total}
        for band in WAGE_BANDS:
            row[f"{band.lower()}_share"] = (
                float(subset[band].sum()) / total if total else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows)


def sector_composition(tagged: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Job counts and shares by NAICS sector, corridor vs rest of state.

    Shares are of each group's own total, so the comparison is composition, not
    size. The corridor is about 2% of Massachusetts blocks; comparing raw counts
    would say nothing.
    """
    sectors = [c for c in SECTOR_LABELS if c in tagged.columns]
    if not sectors:
        raise KeyError("no CNS sector columns found in the LODES table")

    inside = tagged[tagged["in_corridor"]]
    outside = tagged[~tagged["in_corridor"]]

    table = pd.DataFrame(
        {
            "cns_code": sectors,
            "sector_name": [SECTOR_LABELS[c] for c in sectors],
            "corridor_jobs": [float(inside[c].sum()) for c in sectors],
            "rest_of_ma_jobs": [float(outside[c].sum()) for c in sectors],
        }
    )
    table["corridor_share"] = table["corridor_jobs"] / table["corridor_jobs"].sum()
    table["rest_share"] = table["rest_of_ma_jobs"] / table["rest_of_ma_jobs"].sum()

    # Over-representation: how much more concentrated is this sector on the
    # corridor than in the rest of the state?
    table["concentration_ratio"] = table["corridor_share"] / table["rest_share"]

    return (
        table.sort_values("corridor_jobs", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def local_job_containment(
    od: pd.DataFrame,
    corridor_block_ids: set[str],
) -> dict[str, float]:
    """How much corridor residents' work stays inside the corridor.

    Uses the LODES origin-destination file: rows where the home block is in the
    corridor, split by whether the work block is too. The resulting containment
    rate of roughly one quarter is the single most load-bearing number in the
    memo's argument for treating this as a network intervention.
    """
    resident_trips = od[od["h_geocode"].isin(corridor_block_ids)]
    total = float(resident_trips["S000"].sum())
    inside = float(
        resident_trips[resident_trips["w_geocode"].isin(corridor_block_ids)][
            "S000"
        ].sum()
    )
    return {
        "jobs_held_by_corridor_residents": total,
        "held_within_corridor": inside,
        "held_outside_corridor": total - inside,
        "containment_rate": inside / total if total else float("nan"),
        "distinct_workplace_blocks": int(resident_trips["w_geocode"].nunique()),
    }
