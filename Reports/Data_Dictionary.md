# Data Dictionary

## `countries` (dimension table, 50 rows)

| Column | Type | Business Relevance |
|---|---|---|
| country_id | INTEGER PK | Surrogate key, joins to `covid_facts` |
| country_name | TEXT | Standardized (Title Case, trimmed) during cleaning |
| continent | TEXT | Used for regional rollups and comparisons |
| population | INTEGER | Denominator for every per-capita metric (cases/million, vaccination rate, etc.) — without it, raw case counts are meaningless across countries of very different size |
| median_age | REAL | Tests the "older populations = higher mortality" hypothesis |
| gdp_per_capita | REAL (USD) | Proxy for healthcare system capacity, testing infrastructure, and vaccine-purchasing power |
| life_expectancy | REAL | Cross-checked against case fatality rate as a baseline health-system indicator |

## `covid_facts` (fact table, 36,500 rows — grain: one row per country per day)

| Column | Type | Business Relevance |
|---|---|---|
| report_date | TEXT (ISO date) | Time axis for every trend/seasonality query |
| total_cases / new_cases | INTEGER | Core volume metric; `new_cases` drives wave detection |
| total_deaths / new_deaths | INTEGER | Core severity metric; lags cases by ~12 days by design |
| total_recovered | INTEGER | Used for recovery-rate KPI |
| active_cases | INTEGER | `total_cases - total_deaths - total_recovered`; proxy for current health-system load |
| total_tests / new_tests | INTEGER | Denominator for positivity rate; low testing = likely case under-ascertainment |
| positive_rate | REAL | WHO benchmark: >5% sustained suggests inadequate testing coverage |
| people_vaccinated | INTEGER | At-least-one-dose coverage |
| people_fully_vaccinated | INTEGER | Primary vaccination-completion metric |
| total_boosters | INTEGER | Tracks durability of protection over time |
| icu_patients / hosp_patients | INTEGER | Health-system capacity stress indicators |
| reproduction_rate | REAL | Rt > 1 signals active exponential growth; core epidemiological control metric |
| stringency_index | REAL (0-100) | Oxford-style government policy strictness composite; used to test lockdown effectiveness |
| case_fatality_rate | REAL (%) | `total_deaths / total_cases * 100` — **derived** in cleaning step |
| cases_per_million / deaths_per_million | REAL | **Derived**; the correct way to compare burden across countries of different population sizes |
| vaccination_rate_pct | REAL | **Derived**; `people_fully_vaccinated / population * 100` |
| testing_rate_pct | REAL | **Derived**; cumulative tests per 100 population |
| new_cases_7day_avg / new_deaths_7day_avg | REAL | **Derived**; standard epidemiological smoothing to remove day-of-week reporting noise |
| case_growth_wow_pct | REAL | **Derived**; week-over-week % change on the 7-day average — used for wave/momentum detection |

## Cleaning Decisions (see `etl/clean_data.py` for implementation)

| Issue Found | Decision | Rationale |
|---|---|---|
| 146 duplicate (country, date) rows | Dropped, keep first | Exact key duplicates add no information and would double-count in every SUM() |
| 25 negative `new_cases` values | Floored to 0 | Real-world retroactive corrections exist, but a negative daily count breaks cumulative running totals; flooring preserves the row instead of deleting it |
| 546 missing `positive_rate` values | Recomputed from `new_cases / new_tests` | More accurate than mean/median imputation since the inputs to recompute it were already present |
| 366 missing `icu_patients` values | Forward/backward-filled within each country's time series | ICU census changes slowly day-to-day; last-observed-value is a defensible estimate, better than dropping rows or zero-filling (which would create a false capacity signal) |
| Inconsistent country name casing (`"UNITED STATES  "`) | Standardized to Title Case + trimmed, with explicit fixes for multi-word names | Prevents the same country from splitting into multiple GROUP BY buckets |

## Source Note

Real-world equivalents for this schema: Johns Hopkins CSSE COVID-19 Dashboard, Our World in Data COVID-19 dataset, WHO COVID-19 Dashboard. See README "Data Source & Methodology" for why this project uses a generated dataset instead of a live pull.
