-- ============================================================================
-- schema.sql
-- COVID-19 Global Trends Tracker — Database Schema
--
-- Engine used for THIS repo: SQLite 3 (zero-setup, fully portable, runs in CI)
-- Production target: MySQL 8+ / PostgreSQL 14+ (see notes below for the few
--   syntax deltas — AUTOINCREMENT vs AUTO_INCREMENT, etc.)
-- ============================================================================

DROP TABLE IF EXISTS covid_facts;
DROP TABLE IF EXISTS countries;

-- ----------------------------------------------------------------------------
-- Dimension table: one row per country, holding attributes that don't change
-- daily (population, GDP, median age...). Normalized out of the daily fact
-- table to avoid repeating ~36k rows of the same 6 values per country.
-- ----------------------------------------------------------------------------
CREATE TABLE countries (
    country_id        INTEGER PRIMARY KEY AUTOINCREMENT,   -- MySQL: AUTO_INCREMENT
    country_name       TEXT NOT NULL UNIQUE,
    continent           TEXT NOT NULL,
    population           INTEGER NOT NULL,
    median_age            REAL,
    gdp_per_capita         REAL,
    life_expectancy         REAL
);

-- ----------------------------------------------------------------------------
-- Fact table: one row per (country, date). This is the grain of the whole
-- analysis layer — every SQL query in queries/analysis_queries.sql joins
-- against this table.
-- ----------------------------------------------------------------------------
CREATE TABLE covid_facts (
    fact_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id               INTEGER NOT NULL REFERENCES countries(country_id),
    report_date                TEXT NOT NULL,          -- ISO 8601 'YYYY-MM-DD'
    total_cases                  INTEGER NOT NULL DEFAULT 0,
    new_cases                      INTEGER NOT NULL DEFAULT 0,
    total_deaths                     INTEGER NOT NULL DEFAULT 0,
    new_deaths                         INTEGER NOT NULL DEFAULT 0,
    total_recovered                      INTEGER NOT NULL DEFAULT 0,
    active_cases                           INTEGER NOT NULL DEFAULT 0,
    total_tests                              INTEGER NOT NULL DEFAULT 0,
    new_tests                                  INTEGER NOT NULL DEFAULT 0,
    positive_rate                                REAL,
    people_vaccinated                              INTEGER NOT NULL DEFAULT 0,
    people_fully_vaccinated                          INTEGER NOT NULL DEFAULT 0,
    total_boosters                                     INTEGER NOT NULL DEFAULT 0,
    icu_patients                                         INTEGER NOT NULL DEFAULT 0,
    hosp_patients                                          INTEGER NOT NULL DEFAULT 0,
    reproduction_rate                                        REAL,
    stringency_index                                           REAL,
    case_fatality_rate                                           REAL,
    cases_per_million                                              REAL,
    deaths_per_million                                               REAL,
    vaccination_rate_pct                                               REAL,
    testing_rate_pct                                                     REAL,
    new_cases_7day_avg                                                     REAL,
    new_deaths_7day_avg                                                      REAL,
    case_growth_wow_pct                                                        REAL,
    UNIQUE(country_id, report_date)
);

CREATE INDEX idx_facts_country_date ON covid_facts(country_id, report_date);
CREATE INDEX idx_facts_date         ON covid_facts(report_date);
CREATE INDEX idx_countries_continent ON countries(continent);

-- ============================================================================
-- MySQL 8+ PORTING NOTES (for production deployment):
--   1. Replace `INTEGER PRIMARY KEY AUTOINCREMENT` with
--        `INT PRIMARY KEY AUTO_INCREMENT`
--   2. Replace `TEXT` date column with `DATE` and store real DATE values
--   3. Add `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;` to each CREATE TABLE
--   4. Consider partitioning covid_facts by RANGE(YEAR(report_date)) at scale
-- ============================================================================
