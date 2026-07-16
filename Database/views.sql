-- ============================================================================
-- views.sql — reusable analytical views built on top of covid_facts
-- ============================================================================

-- Latest snapshot per country (most recent report_date) — used by almost
-- every "current state" KPI (leaderboards, vaccination coverage today, etc.)
DROP VIEW IF EXISTS vw_country_latest;
CREATE VIEW vw_country_latest AS
SELECT f.*, c.country_name, c.continent, c.population, c.median_age, c.gdp_per_capita, c.life_expectancy
FROM covid_facts f
JOIN countries c ON c.country_id = f.country_id
WHERE f.report_date = (
    SELECT MAX(report_date) FROM covid_facts f2 WHERE f2.country_id = f.country_id
);

-- Monthly rollup per country — powers trend charts without re-aggregating
-- 36k daily rows on every query.
DROP VIEW IF EXISTS vw_monthly_country_summary;
CREATE VIEW vw_monthly_country_summary AS
SELECT
    c.country_name,
    c.continent,
    substr(f.report_date, 1, 7) AS report_month,
    SUM(f.new_cases)  AS monthly_new_cases,
    SUM(f.new_deaths) AS monthly_new_deaths,
    AVG(f.positive_rate) AS avg_positive_rate,
    AVG(f.stringency_index) AS avg_stringency_index,
    MAX(f.people_fully_vaccinated) AS end_of_month_fully_vaccinated
FROM covid_facts f
JOIN countries c ON c.country_id = f.country_id
GROUP BY c.country_name, c.continent, substr(f.report_date, 1, 7);

-- Continent-level daily aggregation
DROP VIEW IF EXISTS vw_continent_daily;
CREATE VIEW vw_continent_daily AS
SELECT
    c.continent,
    f.report_date,
    SUM(f.new_cases)  AS new_cases,
    SUM(f.new_deaths) AS new_deaths,
    SUM(f.total_cases) AS total_cases,
    SUM(f.total_deaths) AS total_deaths,
    SUM(c.population) AS population
FROM covid_facts f
JOIN countries c ON c.country_id = f.country_id
GROUP BY c.continent, f.report_date;
