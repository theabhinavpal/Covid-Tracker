"""
clean_data.py
--------------
Cleans the raw generated COVID-19 dataset. Every decision below is deliberate and documented
(see reports/Data_Dictionary.md for the full rationale table).

Run:
    python3 etl/clean_data.py
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("clean_data")

RAW_PATH = "/home/claude/covid-tracker/dataset/covid_data_raw.csv"
CLEAN_PATH = "/home/claude/covid-tracker/dataset/covid_data.csv"


def load_raw(path: str) -> pd.DataFrame:
    log.info(f"Loading raw dataset from {path}")
    df = pd.read_csv(path, parse_dates=["date"])
    log.info(f"Loaded {len(df):,} raw rows")
    return df


def standardize_country_names(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace and normalize casing to Title Case (real OWID-style fix)."""
    before = df["country"].nunique()
    df["country"] = df["country"].str.strip().str.title()
    # a couple of known multi-word edge cases Title Case mangles
    fixes = {
        "United Arab Emirates": "United Arab Emirates",
        "United States": "United States",
        "United Kingdom": "United Kingdom",
        "South Korea": "South Korea",
        "South Africa": "South Africa",
        "New Zealand": "New Zealand",
        "Saudi Arabia": "Saudi Arabia",
    }
    df["country"] = df["country"].replace(fixes)
    after = df["country"].nunique()
    log.info(f"Standardized country names ({before} -> {after} distinct labels)")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["country", "date"], keep="first")
    log.info(f"Removed {before - len(df):,} duplicate (country, date) rows")
    return df


def fix_negative_values(df: pd.DataFrame) -> pd.DataFrame:
    """new_cases/new_deaths should never be negative in a clean analytical table.
    Real-world negatives (retroactive corrections) are floored at 0 rather than dropped,
    since dropping would break the cumulative running totals for that country."""
    neg_cases = (df["new_cases"] < 0).sum()
    df["new_cases"] = df["new_cases"].clip(lower=0)
    log.info(f"Floored {neg_cases} negative new_cases values to 0")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    positive_rate: recompute from new_cases/new_tests where missing (more accurate than
                   imputing) rather than dropping the row.
    icu_patients:  forward-fill within each country's time series (ICU census changes
                   slowly day to day, so last-observed-value is a defensible estimate);
                   any still-missing leading values fall back to 0.
    """
    missing_pr = df["positive_rate"].isna().sum()
    recomputed = df["new_cases"] / df["new_tests"].replace(0, np.nan)
    df["positive_rate"] = df["positive_rate"].fillna(recomputed).fillna(0).round(4)
    log.info(f"Recomputed {missing_pr} missing positive_rate values from new_cases/new_tests")

    missing_icu = df["icu_patients"].isna().sum()
    df = df.sort_values(["country", "date"])
    df["icu_patients"] = (
        df.groupby("country")["icu_patients"].transform(lambda s: s.ffill().bfill()).fillna(0)
    )
    df["icu_patients"] = df["icu_patients"].round().astype(int)
    log.info(f"Forward/backward-filled {missing_icu} missing icu_patients values")
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering used throughout the SQL/Python analysis layer."""
    df = df.sort_values(["country", "date"]).reset_index(drop=True)

    df["case_fatality_rate"] = np.where(
        df["total_cases"] > 0, (df["total_deaths"] / df["total_cases"] * 100).round(3), 0
    )
    df["cases_per_million"] = (df["total_cases"] / df["population"] * 1_000_000).round(1)
    df["deaths_per_million"] = (df["total_deaths"] / df["population"] * 1_000_000).round(1)
    df["vaccination_rate_pct"] = (df["people_fully_vaccinated"] / df["population"] * 100).clip(0, 100).round(2)
    df["testing_rate_pct"] = (df["total_tests"] / df["population"] * 100).round(2)

    # 7-day rolling averages (standard epidemiological smoothing)
    df["new_cases_7day_avg"] = (
        df.groupby("country")["new_cases"].transform(lambda s: s.rolling(7, min_periods=1).mean().round(1))
    )
    df["new_deaths_7day_avg"] = (
        df.groupby("country")["new_deaths"].transform(lambda s: s.rolling(7, min_periods=1).mean().round(1))
    )

    # week-over-week growth rate on the 7-day average (reduces day-of-week noise)
    df["case_growth_wow_pct"] = (
        df.groupby("country")["new_cases_7day_avg"]
        .transform(lambda s: s.pct_change(periods=7).replace([np.inf, -np.inf], np.nan) * 100)
        .round(2)
    )

    return df


def validate(df: pd.DataFrame) -> None:
    """Basic data-quality assertions before we load into the database."""
    assert df["date"].notna().all(), "Null dates found"
    assert (df["new_cases"] >= 0).all(), "Negative new_cases survived cleaning"
    assert (df["total_deaths"] <= df["total_cases"] + 1).all(), "Deaths exceed cases in some row"
    assert df.duplicated(subset=["country", "date"]).sum() == 0, "Duplicates survived cleaning"
    log.info("Validation checks passed.")


def main():
    df = load_raw(RAW_PATH)
    df = standardize_country_names(df)
    df = remove_duplicates(df)
    df = fix_negative_values(df)
    df = handle_missing_values(df)
    df = add_derived_features(df)
    validate(df)
    df.to_csv(CLEAN_PATH, index=False)
    log.info(f"Saved cleaned dataset with {len(df):,} rows -> {CLEAN_PATH}")


if __name__ == "__main__":
    main()
