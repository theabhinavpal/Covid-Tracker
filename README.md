# COVID-19 Global Trends Tracker

**End-to-End Global Pandemic Analytics & Business Intelligence Project**
SQL · Python · ETL · Time-Series Analysis · Business Intelligence

---

## ⚠️ Data Source & Methodology (read this first)

This project uses a **simulated dataset**, not a raw download of Johns Hopkins/OWID data. It was generated with `etl/generate_dataset.py` to statistically mirror real pandemic dynamics — multiple seasonal waves per country, a Pareto-style concentration of cases in a handful of large countries, GDP/age-driven mortality and vaccination-speed differences, and realistic reporting artifacts (weekend under-reporting, lagged death reporting, missing values, duplicate rows, inconsistent country-name casing).

Why simulated instead of a live pull: it keeps the project fully reproducible with no external dependency or license ambiguity, while still requiring a **real cleaning pipeline, a real database, and real analysis** — every number in `reports/` was computed by actually running the SQL/Python against the loaded data, not written by hand. Swapping in a live OWID/JHU CSV is a one-line change in `etl/generate_dataset.py`'s output path — the schema, cleaning, and SQL layers are written against realistic OWID-style columns and would work unchanged.

## Project Overview

A full analytics stack built around a country-day COVID-19 fact table:

- **36,500 rows** across **50 countries**, 2 continents' worth of hemispheres, **730 days** (Jan 2021 – Dec 2022)
- Cases, deaths, recoveries, testing, vaccination, ICU/hospitalization, reproduction rate, and government stringency index
- A real SQLite database (`database/covid_tracker.db`), built and queried, not just described
- 25 tested SQL queries covering joins, CTEs, window functions, ranking, running totals, moving averages, and date-based aggregation
- A Python cleaning + feature-engineering pipeline with documented decisions
- 6 executive-ready visualizations generated straight from the database
- Insights and KPIs grounded in the actual computed numbers (see `reports/Business_Insights.md`)

## Repository Structure

```
covid-tracker/
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
├── dataset/
│   ├── covid_data_raw.csv        # generated, with intentional data-quality issues
│   └── covid_data.csv            # cleaned + feature-engineered
├── database/
│   ├── schema.sql                # tables, keys, indexes
│   ├── views.sql                 # vw_country_latest, vw_monthly_country_summary, vw_continent_daily
│   └── covid_tracker.db          # populated SQLite database
├── etl/
│   ├── generate_dataset.py       # dataset generator (patterns documented inline)
│   ├── clean_data.py             # cleaning + feature engineering, with logging
│   ├── load_data.py              # builds schema + loads cleaned data + sanity checks
│   └── run_queries.py            # executes every SQL query against the live DB
├── queries/
│   └── analysis_queries.sql      # all 25 queries, standalone and re-runnable
├── src/
│   └── visualizations.py         # generates all 6 charts from the live database
├── images/charts/                # 6 PNG charts
└── reports/
    ├── Data_Dictionary.md
    ├── SQL_Query_Results.md      # real output of every query, captured by run_queries.py
    ├── Business_Insights.md
    ├── KPI_Report.md
    └── Interview_QA.md
```

## How to Reproduce This Project

```bash
pip install -r requirements.txt

python3 etl/generate_dataset.py     # -> dataset/covid_data_raw.csv
python3 etl/clean_data.py           # -> dataset/covid_data.csv
python3 etl/load_data.py            # -> database/covid_tracker.db (schema + views + data + checks)
python3 etl/run_queries.py          # -> reports/SQL_Query_Results.md (real output)
python3 src/visualizations.py       # -> images/charts/*.png
```

Every step above was actually run to build this repo — the checked-in `database/covid_tracker.db`, `reports/SQL_Query_Results.md`, and `images/charts/` are real generated artifacts, not mockups.

## Key Findings (headline numbers, see `reports/Business_Insights.md` for full detail)

- Global case-fatality rate across the dataset: **7.06%**
- The **top 10 of 50 countries account for 78.9%** of global reported cases — a strong Pareto concentration
- Vaccination rate vs. case-fatality rate: **r = -0.79** (strong negative correlation)
- GDP per capita vs. vaccination rate: **r = 0.98** (near-perfect — wealth is the dominant predictor of rollout speed)
- Countries testing least per capita (Egypt, Malaysia, Ukraine) also report the lowest cases per million — a likely **under-ascertainment signal**, not genuinely lower spread
- 14 of 50 countries never crossed 50% full vaccination coverage in the window

## Tech Stack

Python 3.11 (pandas, numpy, scipy, matplotlib, seaborn), SQLite 3 (portable stand-in for MySQL 8 / PostgreSQL — porting notes included in `database/schema.sql`), SQL (window functions, CTEs, views).

## License

MIT — see `LICENSE`.
