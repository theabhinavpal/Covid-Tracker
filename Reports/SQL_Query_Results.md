# SQL Query Results — Executed Against the Live Database

Every query below was run against `database/covid_tracker.db` (36,500 rows / 50 countries / 2021-2022) using `sqlite3` via `etl/run_queries.py`. Output shown is the actual query result, not hand-written.


## Q1. Which 10 countries have the highest total cases per million population (true burden, population-adjusted)?

```sql
SELECT country_name, continent, ROUND(cases_per_million,1) AS cases_per_million
FROM vw_country_latest
ORDER BY cases_per_million DESC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| country_name   | continent     |   cases_per_million |
|:---------------|:--------------|--------------------:|
| Norway         | Europe        |             79706.3 |
| Sweden         | Europe        |             61256.3 |
| New Zealand    | Oceania       |             59398.2 |
| United States  | North America |             56919.3 |
| South Korea    | Asia          |             56152.1 |
| Netherlands    | Europe        |             54920.3 |
| Saudi Arabia   | Asia          |             52839.8 |
| Australia      | Oceania       |             47263   |
| Singapore      | Asia          |             41341   |
| Pakistan       | Asia          |             40611.8 |



## Q2. What is the global running total of cases and deaths over time (window function running total)?

```sql
SELECT report_date,
       SUM(new_cases) OVER (ORDER BY report_date) AS running_total_cases,
       SUM(new_deaths) OVER (ORDER BY report_date) AS running_total_deaths
FROM (SELECT report_date, SUM(new_cases) AS new_cases, SUM(new_deaths) AS new_deaths
      FROM covid_facts GROUP BY report_date)
ORDER BY report_date DESC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| report_date   |   running_total_cases |   running_total_deaths |
|:--------------|----------------------:|-----------------------:|
| 2022-12-31    |             178991579 |               12639183 |
| 2022-12-30    |             178990923 |               12639034 |
| 2022-12-29    |             178989914 |               12638850 |
| 2022-12-28    |             178988807 |               12638652 |
| 2022-12-27    |             178987554 |               12638433 |
| 2022-12-26    |             178986131 |               12638191 |
| 2022-12-25    |             178984569 |               12637919 |
| 2022-12-24    |             178983602 |               12637661 |
| 2022-12-23    |             178982191 |               12637361 |
| 2022-12-22    |             178980013 |               12637008 |



## Q3. Rank countries within each continent by total deaths per million (RANK window function).

```sql
SELECT continent, country_name, deaths_per_million,
       RANK() OVER (PARTITION BY continent ORDER BY deaths_per_million DESC) AS continent_rank
FROM vw_country_latest
ORDER BY continent, continent_rank
LIMIT 20;
```

**Result** (20 rows returned, showing up to 15):

| continent   | country_name   |   deaths_per_million |   continent_rank |
|:------------|:---------------|---------------------:|-----------------:|
| Africa      | Ghana          |               1602.7 |                1 |
| Africa      | Morocco        |               1426.7 |                2 |
| Africa      | Kenya          |                925.2 |                3 |
| Africa      | Ethiopia       |                895.3 |                4 |
| Africa      | Nigeria        |                676.2 |                5 |
| Africa      | South Africa   |                643.4 |                6 |
| Africa      | Egypt          |                422.9 |                7 |
| Asia        | China          |               2732.7 |                1 |
| Asia        | India          |               2695.9 |                2 |
| Asia        | Thailand       |               2693.5 |                3 |
| Asia        | South Korea    |               2592.2 |                4 |
| Asia        | Pakistan       |               2512.7 |                5 |
| Asia        | Saudi Arabia   |               2209.3 |                6 |
| Asia        | Vietnam        |               2043   |                7 |
| Asia        | Iraq           |               1642.7 |                8 |



## Q4. What does the Pareto concentration of global cases look like — what % of global cases come from the top 20% of countries (CTE + window function)?

```sql
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
```

**Result** (5 rows returned, showing up to 15):

|   quintile |   n_countries |   quintile_total_cases |   pct_of_global_cases |
|-----------:|--------------:|-----------------------:|----------------------:|
|          1 |            10 |            1.41245e+08 |                  78.9 |
|          2 |            10 |            2.0562e+07  |                  11.5 |
|          3 |            10 |            1.0852e+07  |                   6.1 |
|          4 |            10 |            4.33282e+06 |                   2.4 |
|          5 |            10 |            2.10659e+06 |                   1.2 |



## Q5. 30-day moving average of new cases for the United States, India, and Brazil (compare 3 major countries over time).

```sql
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
```

**Result** (15 rows returned, showing up to 15):

| country_name   | report_date   |   moving_avg_30d |
|:---------------|:--------------|-----------------:|
| Brazil         | 2022-12-31    |          137.233 |
| Brazil         | 2022-12-30    |          148.933 |
| Brazil         | 2022-12-29    |          161.167 |
| Brazil         | 2022-12-28    |          174.233 |
| Brazil         | 2022-12-27    |          187.567 |
| Brazil         | 2022-12-26    |          194.233 |
| Brazil         | 2022-12-25    |          204.033 |
| Brazil         | 2022-12-24    |          221.6   |
| Brazil         | 2022-12-23    |          240.733 |
| Brazil         | 2022-12-22    |          260.933 |
| Brazil         | 2022-12-21    |          281.833 |
| Brazil         | 2022-12-20    |          302.967 |
| Brazil         | 2022-12-19    |          313.9   |
| Brazil         | 2022-12-18    |          330.7   |
| Brazil         | 2022-12-17    |          359     |



## Q6. Which countries achieved the fastest vaccination rollout (fully vaccinated % gained per 30 days, using LAG window function)?

```sql
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
```

**Result** (10 rows returned, showing up to 15):

| country_name   |   avg_monthly_vax_gain_pct |
|:---------------|---------------------------:|
| Switzerland    |                       4.16 |
| Norway         |                       4.16 |
| Singapore      |                       4.14 |
| United States  |                       4.13 |
| Australia      |                       4.09 |
| Netherlands    |                       4    |
| Sweden         |                       3.84 |
| Israel         |                       3.82 |
| Canada         |                       3.81 |
| Belgium        |                       3.79 |



## Q7. Correlation snapshot: for each country, current vaccination rate vs. current case-fatality rate (used to test the vaccination-mortality relationship).

```sql
SELECT country_name, vaccination_rate_pct, case_fatality_rate, gdp_per_capita, median_age
FROM vw_country_latest
ORDER BY vaccination_rate_pct DESC;
```

**Result** (50 rows returned, showing up to 15):

| country_name         |   vaccination_rate_pct |   case_fatality_rate |   gdp_per_capita |   median_age |
|:---------------------|-----------------------:|---------------------:|-----------------:|-------------:|
| Switzerland          |                  95.62 |                1.873 |            91992 |         42.7 |
| Norway               |                  95.58 |                1.841 |            89242 |         39.4 |
| Singapore            |                  95.21 |                3.188 |            72794 |         42.2 |
| United States        |                  95.06 |                2.497 |            69287 |         38.5 |
| Australia            |                  93.97 |                2.634 |            60443 |         37.5 |
| Netherlands          |                  91.89 |                3.106 |            57767 |         42.5 |
| Sweden               |                  88.26 |                3.636 |            52838 |         41.2 |
| Israel               |                  87.82 |                2.74  |            52170 |         30.1 |
| Canada               |                  87.69 |                3.145 |            52051 |         41.1 |
| Belgium              |                  87.14 |                4.885 |            51247 |         42   |
| Germany              |                  87.05 |                4.71  |            51203 |         45.9 |
| New Zealand          |                  85.42 |                3.24  |            48781 |         38.1 |
| United Kingdom       |                  83.5  |                3.859 |            46510 |         40.6 |
| France               |                  81.31 |                5.653 |            43659 |         42   |
| United Arab Emirates |                  81.06 |                5.169 |            43103 |         33.5 |



## Q8. Which countries had the highest average weekly case growth rate during 2021 (HAVING clause on aggregated growth)?

```sql
SELECT c.country_name, ROUND(AVG(f.case_growth_wow_pct),2) AS avg_wow_growth_pct
FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
WHERE f.report_date BETWEEN '2021-01-01' AND '2021-12-31'
GROUP BY c.country_name
HAVING AVG(f.case_growth_wow_pct) IS NOT NULL
ORDER BY avg_wow_growth_pct DESC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| country_name   |   avg_wow_growth_pct |
|:---------------|---------------------:|
| South Africa   |                13.06 |
| Brazil         |                12.02 |
| Peru           |                12    |
| New Zealand    |                11.91 |
| Argentina      |                11.88 |
| Indonesia      |                11.72 |
| Kenya          |                11.54 |
| Australia      |                11.49 |
| Chile          |                10.91 |
| Ethiopia       |                 2.73 |



## Q9. Monthly global new cases and new deaths trend (GROUP BY date function, full pandemic window).

```sql
SELECT substr(report_date,1,7) AS month, SUM(new_cases) AS total_new_cases, SUM(new_deaths) AS total_new_deaths
FROM covid_facts
GROUP BY substr(report_date,1,7)
ORDER BY month;
```

**Result** (24 rows returned, showing up to 15):

| month   |   total_new_cases |   total_new_deaths |
|:--------|------------------:|-------------------:|
| 2021-01 |          11696627 |             664720 |
| 2021-02 |           9090549 |             915369 |
| 2021-03 |           5612671 |             650626 |
| 2021-04 |           2079455 |             264920 |
| 2021-05 |           1031082 |             103750 |
| 2021-06 |           1390071 |              88901 |
| 2021-07 |           3357688 |             186050 |
| 2021-08 |           6833900 |             421403 |
| 2021-09 |           8257966 |             609534 |
| 2021-10 |           6825758 |             560839 |
| 2021-11 |           7301912 |             471271 |
| 2021-12 |          12422276 |             715442 |
| 2022-01 |          17397498 |            1089983 |
| 2022-02 |          16941234 |            1159871 |
| 2022-03 |          15562520 |            1157166 |



## Q10. Continent-level comparison: total cases, deaths, and CFR at the latest snapshot (JOIN + aggregation).

```sql
SELECT continent,
       SUM(total_cases) AS total_cases,
       SUM(total_deaths) AS total_deaths,
       ROUND(100.0*SUM(total_deaths)/SUM(total_cases),3) AS continent_cfr_pct,
       SUM(population) AS population
FROM vw_country_latest
GROUP BY continent
ORDER BY total_cases DESC;
```

**Result** (6 rows returned, showing up to 15):

| continent     |   total_cases |   total_deaths |   continent_cfr_pct |   population |
|:--------------|--------------:|---------------:|--------------------:|-------------:|
| Asia          |     124510037 |        9819344 |               7.886 |   4160200000 |
| North America |      23298361 |         761549 |               3.269 |    499000000 |
| Europe        |      17658454 |        1057794 |               5.99  |    707300000 |
| Africa        |       6118150 |         481989 |               7.878 |    610600000 |
| South America |       5996069 |         476692 |               7.95  |    362000000 |
| Oceania       |       1517589 |          41815 |               2.755 |     30800000 |



## Q11. Which countries never crossed 50% full vaccination coverage by end of the dataset (subquery / anti-pattern)?

```sql
SELECT country_name, ROUND(vaccination_rate_pct,1) AS vaccination_rate_pct
FROM vw_country_latest
WHERE vaccination_rate_pct < 50
ORDER BY vaccination_rate_pct ASC;
```

**Result** (14 rows returned, showing up to 15):

| country_name   |   vaccination_rate_pct |
|:---------------|-----------------------:|
| Ethiopia       |                   46.6 |
| Pakistan       |                   47   |
| Nigeria        |                   47.5 |
| Ghana          |                   47.6 |
| India          |                   47.6 |
| Kenya          |                   47.8 |
| Bangladesh     |                   48.1 |
| Philippines    |                   48.6 |
| Morocco        |                   48.8 |
| Egypt          |                   49   |
| Vietnam        |                   49.1 |
| Indonesia      |                   49.6 |
| Iran           |                   49.6 |
| Ukraine        |                   49.8 |



## Q12. Detect distinct COVID 'waves' for India using week-over-week growth sign changes (CASE + window function).

```sql
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
```

**Result** (24 rows returned, showing up to 15):

| ym      |   monthly_cases | trend_direction   |
|:--------|----------------:|:------------------|
| 2021-01 |         2899683 | FLAT              |
| 2021-02 |         2252879 | FALLING           |
| 2021-03 |         1369220 | FALLING           |
| 2021-04 |          460023 | FALLING           |
| 2021-05 |          115835 | FALLING           |
| 2021-06 |          119499 | RISING            |
| 2021-07 |          566512 | RISING            |
| 2021-08 |         1431354 | RISING            |
| 2021-09 |         1882904 | RISING            |
| 2021-10 |         1620431 | FALLING           |
| 2021-11 |         1809151 | RISING            |
| 2021-12 |         3058763 | RISING            |
| 2022-01 |         4385168 | RISING            |
| 2022-02 |         4223440 | FALLING           |
| 2022-03 |         3788239 | FALLING           |



## Q13. Top 5 countries by ICU patient load relative to population — hospital-system stress indicator.

```sql
SELECT country_name, icu_patients, population,
       ROUND(1000000.0 * icu_patients / population, 2) AS icu_per_million
FROM vw_country_latest
ORDER BY icu_per_million DESC
LIMIT 5;
```

**Result** (5 rows returned, showing up to 15):

| country_name   |   icu_patients |   population |   icu_per_million |
|:---------------|---------------:|-------------:|------------------:|
| Norway         |             39 |      5400000 |              7.22 |
| Switzerland    |             31 |      8700000 |              3.56 |
| United States  |           1062 |    331900000 |              3.2  |
| Australia      |             63 |     25700000 |              2.45 |
| Netherlands    |             23 |     17500000 |              1.31 |



## Q14. GDP per capita vs. vaccination rate — do wealthier countries vaccinate faster (bucketed CASE analysis)?

```sql
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
```

**Result** (4 rows returned, showing up to 15):

| gdp_bucket               |   n_countries |   avg_vaccination_rate_pct |   avg_cfr |
|:-------------------------|--------------:|---------------------------:|----------:|
| 1. Low GDP (<$5k)        |            15 |                       48.5 |     9.537 |
| 2. Mid GDP ($5k-$20k)    |            13 |                       54.6 |     8.265 |
| 3. High GDP ($20k-$50k)  |            11 |                       75.1 |     5.702 |
| 4. Very High GDP ($50k+) |            11 |                       91.4 |     3.114 |



## Q15. Median age vs. case-fatality rate bucketed comparison (older populations = higher CFR hypothesis test).

```sql
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
```

**Result** (4 rows returned, showing up to 15):

| age_bucket       |   n_countries |   avg_cfr |   avg_life_expectancy |
|:-----------------|--------------:|----------:|----------------------:|
| 1. Young (<25)   |             7 |     9.602 |                  66.1 |
| 2. Mid (25-35)   |            18 |     7.73  |                  75.1 |
| 3. Older (35-42) |            13 |     5.93  |                  79.6 |
| 4. Oldest (42+)  |            12 |     5.336 |                  82.9 |



## Q16. Testing rate leaders vs. laggards — which countries test the least relative to population (possible undercount risk flag)?

```sql
SELECT country_name, ROUND(testing_rate_pct,1) AS testing_rate_pct, ROUND(cases_per_million,1) AS cases_per_million
FROM vw_country_latest
ORDER BY testing_rate_pct ASC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| country_name   |   testing_rate_pct |   cases_per_million |
|:---------------|-------------------:|--------------------:|
| Egypt          |                2.3 |              4177.1 |
| Malaysia       |                2.5 |              4190   |
| Ukraine        |                2.8 |              5053.6 |
| Bangladesh     |                3.6 |              6920.6 |
| South Africa   |                4.2 |              6772.9 |
| Greece         |                4.5 |              7172.4 |
| Spain          |                4.7 |              7127.8 |
| Ghana          |                5.1 |              9903.6 |
| Kenya          |                5.5 |              9967   |
| Nigeria        |                5.8 |             10277.5 |



## Q17. Peak single-day new case count and the date it occurred, per country (subquery with correlated MAX).

```sql
SELECT c.country_name, f.report_date AS peak_date, f.new_cases AS peak_new_cases
FROM covid_facts f
JOIN countries c ON c.country_id = f.country_id
WHERE f.new_cases = (
    SELECT MAX(f2.new_cases) FROM covid_facts f2 WHERE f2.country_id = f.country_id
)
ORDER BY peak_new_cases DESC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| country_name   | peak_date   |   peak_new_cases |
|:---------------|:------------|-----------------:|
| China          | 2022-01-27  |           218162 |
| India          | 2022-01-27  |           182143 |
| United States  | 2022-02-09  |            84371 |
| Pakistan       | 2022-02-14  |            40288 |
| Indonesia      | 2022-08-29  |            27590 |
| Vietnam        | 2022-02-07  |            16145 |
| Mexico         | 2022-02-04  |            14358 |
| Russia         | 2022-02-14  |            12809 |
| South Korea    | 2022-02-04  |            12725 |
| Brazil         | 2022-08-22  |            10808 |



## Q18. Stringency index vs. case growth — did stricter lockdowns correlate with lower growth the following month?

```sql
SELECT
  CASE WHEN stringency_index < 40 THEN '1. Low stringency'
       WHEN stringency_index < 65 THEN '2. Medium stringency'
       ELSE '3. High stringency' END AS stringency_bucket,
  ROUND(AVG(case_growth_wow_pct),2) AS avg_wow_case_growth_pct,
  COUNT(*) AS n_observations
FROM covid_facts
WHERE case_growth_wow_pct IS NOT NULL
GROUP BY stringency_bucket;
```

**Result** (3 rows returned, showing up to 15):

| stringency_bucket    |   avg_wow_case_growth_pct |   n_observations |
|:---------------------|--------------------------:|-----------------:|
| 1. Low stringency    |                     -2.13 |             3192 |
| 2. Medium stringency |                     -1.09 |            15108 |
| 3. High stringency   |                     -0.31 |            17814 |



## Q19. Booster uptake as a % of fully vaccinated population, top 10 countries.

```sql
SELECT country_name,
       ROUND(100.0 * total_boosters / NULLIF(people_fully_vaccinated,0), 1) AS booster_pct_of_fully_vaxxed
FROM vw_country_latest
WHERE people_fully_vaccinated > 0
ORDER BY booster_pct_of_fully_vaxxed DESC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| country_name   |   booster_pct_of_fully_vaxxed |
|:---------------|------------------------------:|
| Australia      |                          52.3 |
| Norway         |                          52.3 |
| Singapore      |                          52.3 |
| United States  |                          52.3 |
| Switzerland    |                          52.2 |
| New Zealand    |                          52.1 |
| Belgium        |                          52   |
| Israel         |                          52   |
| Netherlands    |                          52   |
| South Korea    |                          52   |



## Q20. Year-over-year comparison: total cases and deaths in 2021 vs 2022 (CASE-based pivot).

```sql
SELECT
  SUM(CASE WHEN substr(report_date,1,4)='2021' THEN new_cases ELSE 0 END) AS cases_2021,
  SUM(CASE WHEN substr(report_date,1,4)='2022' THEN new_cases ELSE 0 END) AS cases_2022,
  SUM(CASE WHEN substr(report_date,1,4)='2021' THEN new_deaths ELSE 0 END) AS deaths_2021,
  SUM(CASE WHEN substr(report_date,1,4)='2022' THEN new_deaths ELSE 0 END) AS deaths_2022
FROM covid_facts;
```

**Result** (1 rows returned, showing up to 15):

|   cases_2021 |   cases_2022 |   deaths_2021 |   deaths_2022 |
|-------------:|-------------:|--------------:|--------------:|
|     75899955 |    103091624 |       5652825 |       6986358 |



## Q21. Reproduction rate (Rt) distribution — how many country-days had Rt > 1.2 (active exponential growth)?

```sql
SELECT continent, COUNT(*) AS days_with_rt_above_1_2
FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
WHERE f.reproduction_rate > 1.2
GROUP BY continent
ORDER BY days_with_rt_above_1_2 DESC;
```

**Result** (6 rows returned, showing up to 15):

| continent     |   days_with_rt_above_1_2 |
|:--------------|-------------------------:|
| South America |                      176 |
| Africa        |                      103 |
| Oceania       |                      100 |
| Asia          |                       69 |
| Europe        |                       16 |
| North America |                        6 |



## Q22. Recovery rate leaders — countries with the highest total_recovered / total_cases ratio.

```sql
SELECT country_name,
       ROUND(100.0 * total_recovered / NULLIF(total_cases,0), 2) AS recovery_rate_pct,
       ROUND(case_fatality_rate,3) AS case_fatality_rate
FROM vw_country_latest
ORDER BY recovery_rate_pct DESC
LIMIT 10;
```

**Result** (10 rows returned, showing up to 15):

| country_name   |   recovery_rate_pct |   case_fatality_rate |
|:---------------|--------------------:|---------------------:|
| Bangladesh     |               96.48 |               13.218 |
| Belgium        |               96.48 |                4.885 |
| Canada         |               96.48 |                3.145 |
| China          |               96.48 |                7.653 |
| Colombia       |               96.48 |                9.533 |
| Egypt          |               96.48 |               10.123 |
| Ethiopia       |               96.48 |                6.085 |
| France         |               96.48 |                5.653 |
| Germany        |               96.48 |                4.71  |
| Ghana          |               96.48 |               16.184 |



## Q23. Global KPI summary snapshot (single-row executive KPI query).

```sql
SELECT
  SUM(total_cases) AS global_total_cases,
  SUM(total_deaths) AS global_total_deaths,
  SUM(total_recovered) AS global_total_recovered,
  SUM(active_cases) AS global_active_cases,
  ROUND(100.0*SUM(total_deaths)/SUM(total_cases),3) AS global_cfr_pct,
  ROUND(AVG(vaccination_rate_pct),1) AS avg_country_vaccination_rate_pct
FROM vw_country_latest;
```

**Result** (1 rows returned, showing up to 15):

|   global_total_cases |   global_total_deaths |   global_total_recovered |   global_active_cases |   global_cfr_pct |   avg_country_vaccination_rate_pct |
|---------------------:|----------------------:|-------------------------:|----------------------:|-----------------:|-----------------------------------:|
|          1.79099e+08 |           1.26392e+07 |               1.7279e+08 |                228741 |            7.057 |                               65.4 |



## Q24. Countries where vaccination rate is high (>60%) but CFR is still above the global average — outlier investigation.

```sql
WITH global_avg AS (SELECT AVG(case_fatality_rate) AS avg_cfr FROM vw_country_latest)
SELECT v.country_name, v.vaccination_rate_pct, v.case_fatality_rate, v.median_age
FROM vw_country_latest v, global_avg g
WHERE v.vaccination_rate_pct > 60 AND v.case_fatality_rate > g.avg_cfr
ORDER BY v.case_fatality_rate DESC;
```

**Result** (2 rows returned, showing up to 15):

| country_name   |   vaccination_rate_pct |   case_fatality_rate |   median_age |
|:---------------|-----------------------:|---------------------:|-------------:|
| Greece         |                  63.63 |               11.62  |         45.6 |
| Poland         |                  61.02 |                8.303 |         41.9 |



## Q25. Monthly rollup view sanity check — using the vw_monthly_country_summary view directly for Germany.

```sql
SELECT report_month, monthly_new_cases, monthly_new_deaths, ROUND(avg_positive_rate,3) AS avg_positive_rate
FROM vw_monthly_country_summary
WHERE country_name = 'Germany'
ORDER BY report_month;
```

**Result** (24 rows returned, showing up to 15):

| report_month   |   monthly_new_cases |   monthly_new_deaths |   avg_positive_rate |
|:---------------|--------------------:|---------------------:|--------------------:|
| 2021-01        |              147402 |                 5570 |               0.131 |
| 2021-02        |              115808 |                 7800 |               0.131 |
| 2021-03        |               70999 |                 5400 |               0.131 |
| 2021-04        |               23609 |                 2167 |               0.131 |
| 2021-05        |                5791 |                  563 |               0.131 |
| 2021-06        |                6039 |                  208 |               0.131 |
| 2021-07        |               28527 |                  858 |               0.131 |
| 2021-08        |               74127 |                 2861 |               0.131 |
| 2021-09        |               92474 |                 4554 |               0.131 |
| 2021-10        |               80825 |                 4314 |               0.131 |
| 2021-11        |               89792 |                 3785 |               0.131 |
| 2021-12        |              154130 |                 5819 |               0.131 |
| 2022-01        |              217790 |                 9012 |               0.131 |
| 2022-02        |              213410 |                 9756 |               0.131 |
| 2022-03        |              193525 |                 9599 |               0.131 |

