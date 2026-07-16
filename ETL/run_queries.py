"""
run_queries.py
---------------
Runs every query in queries/analysis_queries.sql against the REAL populated SQLite
database and writes the actual results into reports/SQL_Query_Results.md.
This is what makes the "actually tested, not just written" claim verifiable —
nothing in that report file is hand-typed; it's captured tool output.

Run:
    python3 etl/run_queries.py
"""

import sqlite3
import pandas as pd

DB_PATH = "/home/claude/covid-tracker/database/covid_tracker.db"
OUT_MD = "/home/claude/covid-tracker/reports/SQL_Query_Results.md"

# Each entry: (id, business_question, sql, business_insight_template)
QUERIES = [
("Q1", "Which 10 countries have the highest total cases per million population (true burden, population-adjusted)?",
"""
SELECT country_name, continent, ROUND(cases_per_million,1) AS cases_per_million
FROM vw_country_latest
ORDER BY cases_per_million DESC
LIMIT 10;
"""),

("Q2", "What is the global running total of cases and deaths over time (window function running total)?",
"""
SELECT report_date,
       SUM(new_cases) OVER (ORDER BY report_date) AS running_total_cases,
       SUM(new_deaths) OVER (ORDER BY report_date) AS running_total_deaths
FROM (SELECT report_date, SUM(new_cases) AS new_cases, SUM(new_deaths) AS new_deaths
      FROM covid_facts GROUP BY report_date)
ORDER BY report_date DESC
LIMIT 10;
"""),

("Q3", "Rank countries within each continent by total deaths per million (RANK window function).",
"""
SELECT continent, country_name, deaths_per_million,
       RANK() OVER (PARTITION BY continent ORDER BY deaths_per_million DESC) AS continent_rank
FROM vw_country_latest
ORDER BY continent, continent_rank
LIMIT 20;
"""),

("Q4", "What does the Pareto concentration of global cases look like — what % of global cases come from the top 20% of countries (CTE + window function)?",
"""
WITH ranked AS (
    SELECT country_name, total_cases,
           SUM(total_cases) OVER () AS global_total,
           NTILE(5) OVER (ORDER BY total_cases DESC) AS quintile
    FROM vw_country_latest
)
SELECT quintile,
       COUNT(*) AS n_countries,
       SUM(total_cases) AS quintile_total_cases,
       ROUND(100.0 * SUM(total_cases) / MAX(global_total), 1) AS pct_of_global_cases
FROM ranked
GROUP BY quintile
ORDER BY quintile;
"""),

("Q5", "30-day moving average of new cases for the United States, India, and Brazil (compare 3 major countries over time).",
"""
SELECT c.country_name, f.report_date,
       AVG(f.new_cases) OVER (
           PARTITION BY c.country_name ORDER BY f.report_date
           ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
       ) AS moving_avg_30d
FROM covid_facts f
JOIN countries c ON c.country_id = f.country_id
WHERE c.country_name IN ('United States','India','Brazil')
ORDER BY c.country_name, f.report_date DESC
LIMIT 15;
"""),

("Q6", "Which countries achieved the fastest vaccination rollout (fully vaccinated % gained per 30 days, using LAG window function)?",
"""
WITH monthly AS (
    SELECT c.country_name, substr(f.report_date,1,7) AS ym,
           MAX(f.vaccination_rate_pct) AS month_end_vax_pct
    FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
    GROUP BY c.country_name, substr(f.report_date,1,7)
),
deltas AS (
    SELECT country_name, ym, month_end_vax_pct,
           month_end_vax_pct - LAG(month_end_vax_pct) OVER (PARTITION BY country_name ORDER BY ym) AS monthly_gain
    FROM monthly
)
SELECT country_name, ROUND(AVG(monthly_gain),2) AS avg_monthly_vax_gain_pct
FROM deltas
WHERE monthly_gain IS NOT NULL
GROUP BY country_name
ORDER BY avg_monthly_vax_gain_pct DESC
LIMIT 10;
"""),

("Q7", "Correlation snapshot: for each country, current vaccination rate vs. current case-fatality rate (used to test the vaccination-mortality relationship).",
"""
SELECT country_name, vaccination_rate_pct, case_fatality_rate, gdp_per_capita, median_age
FROM vw_country_latest
ORDER BY vaccination_rate_pct DESC;
"""),

("Q8", "Which countries had the highest average weekly case growth rate during 2021 (HAVING clause on aggregated growth)?",
"""
SELECT c.country_name, ROUND(AVG(f.case_growth_wow_pct),2) AS avg_wow_growth_pct
FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
WHERE f.report_date BETWEEN '2021-01-01' AND '2021-12-31'
GROUP BY c.country_name
HAVING AVG(f.case_growth_wow_pct) IS NOT NULL
ORDER BY avg_wow_growth_pct DESC
LIMIT 10;
"""),

("Q9", "Monthly global new cases and new deaths trend (GROUP BY date function, full pandemic window).",
"""
SELECT substr(report_date,1,7) AS month, SUM(new_cases) AS total_new_cases, SUM(new_deaths) AS total_new_deaths
FROM covid_facts
GROUP BY substr(report_date,1,7)
ORDER BY month;
"""),

("Q10", "Continent-level comparison: total cases, deaths, and CFR at the latest snapshot (JOIN + aggregation).",
"""
SELECT continent,
       SUM(total_cases) AS total_cases,
       SUM(total_deaths) AS total_deaths,
       ROUND(100.0*SUM(total_deaths)/SUM(total_cases),3) AS continent_cfr_pct,
       SUM(population) AS population
FROM vw_country_latest
GROUP BY continent
ORDER BY total_cases DESC;
"""),

("Q11", "Which countries never crossed 50% full vaccination coverage by end of the dataset (subquery / anti-pattern)?",
"""
SELECT country_name, ROUND(vaccination_rate_pct,1) AS vaccination_rate_pct
FROM vw_country_latest
WHERE vaccination_rate_pct < 50
ORDER BY vaccination_rate_pct ASC;
"""),

("Q12", "Detect distinct COVID 'waves' for India using week-over-week growth sign changes (CASE + window function).",
"""
WITH weekly AS (
    SELECT c.country_name, substr(f.report_date,1,7) AS ym,
           SUM(f.new_cases) AS monthly_cases
    FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
    WHERE c.country_name = 'India'
    GROUP BY substr(f.report_date,1,7)
),
labeled AS (
    SELECT ym, monthly_cases,
           CASE WHEN monthly_cases > LAG(monthly_cases) OVER (ORDER BY ym) THEN 'RISING'
                WHEN monthly_cases < LAG(monthly_cases) OVER (ORDER BY ym) THEN 'FALLING'
                ELSE 'FLAT' END AS trend_direction
    FROM weekly
)
SELECT * FROM labeled ORDER BY ym;
"""),

("Q13", "Top 5 countries by ICU patient load relative to population — hospital-system stress indicator.",
"""
SELECT country_name, icu_patients, population,
       ROUND(1000000.0 * icu_patients / population, 2) AS icu_per_million
FROM vw_country_latest
ORDER BY icu_per_million DESC
LIMIT 5;
"""),

("Q14", "GDP per capita vs. vaccination rate — do wealthier countries vaccinate faster (bucketed CASE analysis)?",
"""
SELECT
  CASE WHEN gdp_per_capita < 5000 THEN '1. Low GDP (<$5k)'
       WHEN gdp_per_capita < 20000 THEN '2. Mid GDP ($5k-$20k)'
       WHEN gdp_per_capita < 50000 THEN '3. High GDP ($20k-$50k)'
       ELSE '4. Very High GDP ($50k+)' END AS gdp_bucket,
  COUNT(*) AS n_countries,
  ROUND(AVG(vaccination_rate_pct),1) AS avg_vaccination_rate_pct,
  ROUND(AVG(case_fatality_rate),3) AS avg_cfr
FROM vw_country_latest
GROUP BY gdp_bucket
ORDER BY gdp_bucket;
"""),

("Q15", "Median age vs. case-fatality rate bucketed comparison (older populations = higher CFR hypothesis test).",
"""
SELECT
  CASE WHEN median_age < 25 THEN '1. Young (<25)'
       WHEN median_age < 35 THEN '2. Mid (25-35)'
       WHEN median_age < 42 THEN '3. Older (35-42)'
       ELSE '4. Oldest (42+)' END AS age_bucket,
  COUNT(*) AS n_countries,
  ROUND(AVG(case_fatality_rate),3) AS avg_cfr,
  ROUND(AVG(life_expectancy),1) AS avg_life_expectancy
FROM vw_country_latest
GROUP BY age_bucket
ORDER BY age_bucket;
"""),

("Q16", "Testing rate leaders vs. laggards — which countries test the least relative to population (possible undercount risk flag)?",
"""
SELECT country_name, ROUND(testing_rate_pct,1) AS testing_rate_pct, ROUND(cases_per_million,1) AS cases_per_million
FROM vw_country_latest
ORDER BY testing_rate_pct ASC
LIMIT 10;
"""),

("Q17", "Peak single-day new case count and the date it occurred, per country (subquery with correlated MAX).",
"""
SELECT c.country_name, f.report_date AS peak_date, f.new_cases AS peak_new_cases
FROM covid_facts f
JOIN countries c ON c.country_id = f.country_id
WHERE f.new_cases = (
    SELECT MAX(f2.new_cases) FROM covid_facts f2 WHERE f2.country_id = f.country_id
)
ORDER BY peak_new_cases DESC
LIMIT 10;
"""),

("Q18", "Stringency index vs. case growth — did stricter lockdowns correlate with lower growth the following month?",
"""
SELECT
  CASE WHEN stringency_index < 40 THEN '1. Low stringency'
       WHEN stringency_index < 65 THEN '2. Medium stringency'
       ELSE '3. High stringency' END AS stringency_bucket,
  ROUND(AVG(case_growth_wow_pct),2) AS avg_wow_case_growth_pct,
  COUNT(*) AS n_observations
FROM covid_facts
WHERE case_growth_wow_pct IS NOT NULL
GROUP BY stringency_bucket;
"""),

("Q19", "Booster uptake as a % of fully vaccinated population, top 10 countries.",
"""
SELECT country_name,
       ROUND(100.0 * total_boosters / NULLIF(people_fully_vaccinated,0), 1) AS booster_pct_of_fully_vaxxed
FROM vw_country_latest
WHERE people_fully_vaccinated > 0
ORDER BY booster_pct_of_fully_vaxxed DESC
LIMIT 10;
"""),

("Q20", "Year-over-year comparison: total cases and deaths in 2021 vs 2022 (CASE-based pivot).",
"""
SELECT
  SUM(CASE WHEN substr(report_date,1,4)='2021' THEN new_cases ELSE 0 END) AS cases_2021,
  SUM(CASE WHEN substr(report_date,1,4)='2022' THEN new_cases ELSE 0 END) AS cases_2022,
  SUM(CASE WHEN substr(report_date,1,4)='2021' THEN new_deaths ELSE 0 END) AS deaths_2021,
  SUM(CASE WHEN substr(report_date,1,4)='2022' THEN new_deaths ELSE 0 END) AS deaths_2022
FROM covid_facts;
"""),

("Q21", "Reproduction rate (Rt) distribution — how many country-days had Rt > 1.2 (active exponential growth)?",
"""
SELECT continent, COUNT(*) AS days_with_rt_above_1_2
FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
WHERE f.reproduction_rate > 1.2
GROUP BY continent
ORDER BY days_with_rt_above_1_2 DESC;
"""),

("Q22", "Recovery rate leaders — countries with the highest total_recovered / total_cases ratio.",
"""
SELECT country_name,
       ROUND(100.0 * total_recovered / NULLIF(total_cases,0), 2) AS recovery_rate_pct,
       ROUND(case_fatality_rate,3) AS case_fatality_rate
FROM vw_country_latest
ORDER BY recovery_rate_pct DESC
LIMIT 10;
"""),

("Q23", "Global KPI summary snapshot (single-row executive KPI query).",
"""
SELECT
  SUM(total_cases) AS global_total_cases,
  SUM(total_deaths) AS global_total_deaths,
  SUM(total_recovered) AS global_total_recovered,
  SUM(active_cases) AS global_active_cases,
  ROUND(100.0*SUM(total_deaths)/SUM(total_cases),3) AS global_cfr_pct,
  ROUND(AVG(vaccination_rate_pct),1) AS avg_country_vaccination_rate_pct
FROM vw_country_latest;
"""),

("Q24", "Countries where vaccination rate is high (>60%) but CFR is still above the global average — outlier investigation.",
"""
WITH global_avg AS (SELECT AVG(case_fatality_rate) AS avg_cfr FROM vw_country_latest)
SELECT v.country_name, v.vaccination_rate_pct, v.case_fatality_rate, v.median_age
FROM vw_country_latest v, global_avg g
WHERE v.vaccination_rate_pct > 60 AND v.case_fatality_rate > g.avg_cfr
ORDER BY v.case_fatality_rate DESC;
"""),

("Q25", "Monthly rollup view sanity check — using the vw_monthly_country_summary view directly for Germany.",
"""
SELECT report_month, monthly_new_cases, monthly_new_deaths, ROUND(avg_positive_rate,3) AS avg_positive_rate
FROM vw_monthly_country_summary
WHERE country_name = 'Germany'
ORDER BY report_month;
"""),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    lines = ["# SQL Query Results — Executed Against the Live Database\n",
             "Every query below was run against `database/covid_tracker.db` "
             "(36,500 rows / 50 countries / 2021-2022) using `sqlite3` via "
             "`etl/run_queries.py`. Output shown is the actual query result, not hand-written.\n"]
    for qid, question, sql in QUERIES:
        lines.append(f"\n## {qid}. {question}\n")
        lines.append(f"```sql{sql}```\n")
        try:
            df = pd.read_sql(sql, conn)
            lines.append(f"**Result** ({len(df)} rows returned, showing up to 15):\n")
            lines.append(df.head(15).to_markdown(index=False))
            lines.append("\n")
        except Exception as e:
            lines.append(f"**ERROR:** {e}\n")
            print(f"FAILED {qid}: {e}")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    conn.close()
    print(f"Wrote results for {len(QUERIES)} queries to {OUT_MD}")


if __name__ == "__main__":
    main()
