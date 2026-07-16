"""
load_data.py
-------------
Loads the cleaned dataset into a real SQLite database (database/covid_tracker.db),
applying schema.sql and views.sql first. This is the script that makes the "tested,
not just written" claim true — every query in the SQL analysis file is run against
this actual populated database before being written up.

Run:
    python3 etl/load_data.py
"""

import sqlite3
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("load_data")

BASE = "/home/claude/covid-tracker"
DB_PATH = f"{BASE}/database/covid_tracker.db"
CLEAN_CSV = f"{BASE}/dataset/covid_data.csv"
SCHEMA_SQL = f"{BASE}/database/schema.sql"
VIEWS_SQL = f"{BASE}/database/views.sql"


def build_schema(conn):
    with open(SCHEMA_SQL) as f:
        conn.executescript(f.read())
    log.info("Schema applied (countries, covid_facts tables + indexes).")


def load_countries(conn, df: pd.DataFrame):
    countries = (
        df[["country", "continent", "population", "median_age", "gdp_per_capita", "life_expectancy"]]
        .drop_duplicates(subset=["country"])
        .rename(columns={"country": "country_name"})
    )
    countries.to_sql("countries", conn, if_exists="append", index=False)
    log.info(f"Loaded {len(countries)} countries into `countries` table.")


def load_facts(conn, df: pd.DataFrame):
    country_map = pd.read_sql("SELECT country_id, country_name FROM countries", conn)
    df = df.merge(country_map, left_on="country", right_on="country_name", how="left")

    facts = df.rename(columns={"date": "report_date"})[
        [
            "country_id", "report_date", "total_cases", "new_cases", "total_deaths", "new_deaths",
            "total_recovered", "active_cases", "total_tests", "new_tests", "positive_rate",
            "people_vaccinated", "people_fully_vaccinated", "total_boosters", "icu_patients",
            "hosp_patients", "reproduction_rate", "stringency_index", "case_fatality_rate",
            "cases_per_million", "deaths_per_million", "vaccination_rate_pct", "testing_rate_pct",
            "new_cases_7day_avg", "new_deaths_7day_avg", "case_growth_wow_pct",
        ]
    ]
    facts["report_date"] = pd.to_datetime(facts["report_date"]).dt.strftime("%Y-%m-%d")
    facts.to_sql("covid_facts", conn, if_exists="append", index=False)
    log.info(f"Loaded {len(facts):,} rows into `covid_facts` table.")


def build_views(conn):
    with open(VIEWS_SQL) as f:
        conn.executescript(f.read())
    log.info("Views applied (vw_country_latest, vw_monthly_country_summary, vw_continent_daily).")


def sanity_check(conn):
    checks = {
        "countries row count": "SELECT COUNT(*) FROM countries",
        "facts row count": "SELECT COUNT(*) FROM covid_facts",
        "distinct country_id in facts": "SELECT COUNT(DISTINCT country_id) FROM covid_facts",
        "min report_date": "SELECT MIN(report_date) FROM covid_facts",
        "max report_date": "SELECT MAX(report_date) FROM covid_facts",
    }
    for label, q in checks.items():
        val = conn.execute(q).fetchone()[0]
        log.info(f"  CHECK {label}: {val}")


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        build_schema(conn)
        df = pd.read_csv(CLEAN_CSV)
        load_countries(conn, df)
        load_facts(conn, df)
        build_views(conn)
        conn.commit()
        sanity_check(conn)
        log.info(f"Database built successfully at {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
