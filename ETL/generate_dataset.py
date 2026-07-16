"""
generate_dataset.py
--------------------
Generates a realistic COVID-19 global tracking dataset for this portfolio project.

IMPORTANT / HONESTY NOTE:
This project uses a SIMULATED dataset, not a raw pull of Johns Hopkins / OWID data.
It is built to statistically resemble real pandemic dynamics:
  - Multiple infection "waves" per country with different timing (winter/summer seasonality
    by hemisphere) rather than one smooth curve
  - A Pareto-style concentration of cases: a small number of large, high-testing countries
    account for a disproportionate share of global reported cases
  - Case-fatality and vaccination-uptake differences driven by GDP per capita, median age,
    and stringency policy, not random noise
  - Realistic reporting mechanics: weekend under-reporting, test-positivity constraints,
    lagged death reporting relative to cases

This keeps the analysis honest (see README "Data Source & Methodology") while giving the
SQL/Python analysis layer real signal to find instead of noise.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. COUNTRY MASTER DATA (population, continent, GDP, median age, life expectancy)
#    Values are realistic approximations of real-world figures (World Bank / UN ballpark)
# ---------------------------------------------------------------------------
COUNTRIES = [
    # country, continent, population, gdp_per_capita, median_age, life_expectancy, hemisphere
    ("United States", "North America", 331_900_000, 69_287, 38.5, 78.9, "N"),
    ("Brazil", "South America", 213_400_000, 8_897, 33.5, 75.9, "S"),
    ("India", "Asia", 1_393_400_000, 2_277, 28.4, 69.7, "N"),
    ("United Kingdom", "Europe", 67_800_000, 46_510, 40.6, 81.3, "N"),
    ("France", "Europe", 65_400_000, 43_659, 42.0, 82.7, "N"),
    ("Germany", "Europe", 83_200_000, 51_203, 45.9, 81.3, "N"),
    ("Italy", "Europe", 59_100_000, 35_657, 47.3, 83.5, "N"),
    ("Spain", "Europe", 47_400_000, 30_115, 44.9, 83.6, "N"),
    ("Russia", "Europe", 144_100_000, 12_195, 39.6, 72.6, "N"),
    ("China", "Asia", 1_412_000_000, 12_556, 38.4, 78.2, "N"),
    ("Japan", "Asia", 125_800_000, 39_313, 48.6, 84.6, "N"),
    ("South Korea", "Asia", 51_800_000, 34_998, 43.7, 83.5, "N"),
    ("Indonesia", "Asia", 273_500_000, 4_788, 29.7, 71.7, "S"),
    ("Mexico", "North America", 128_900_000, 9_926, 29.3, 75.1, "N"),
    ("Canada", "North America", 38_200_000, 52_051, 41.1, 82.4, "N"),
    ("South Africa", "Africa", 59_300_000, 6_776, 27.6, 64.1, "S"),
    ("Nigeria", "Africa", 206_100_000, 2_085, 18.1, 55.8, "N"),
    ("Egypt", "Africa", 102_300_000, 3_876, 24.6, 71.8, "N"),
    ("Kenya", "Africa", 53_800_000, 2_007, 20.0, 66.7, "S"),
    ("Australia", "Oceania", 25_700_000, 60_443, 37.5, 83.4, "S"),
    ("New Zealand", "Oceania", 5_100_000, 48_781, 38.1, 82.3, "S"),
    ("Sweden", "Europe", 10_400_000, 52_838, 41.2, 82.8, "N"),
    ("Norway", "Europe", 5_400_000, 89_242, 39.4, 83.2, "N"),
    ("Poland", "Europe", 37_900_000, 17_999, 41.9, 78.7, "N"),
    ("Turkey", "Europe", 84_300_000, 9_539, 32.4, 77.7, "N"),
    ("Argentina", "South America", 45_400_000, 10_636, 32.0, 76.7, "S"),
    ("Chile", "South America", 19_200_000, 15_355, 35.4, 80.2, "S"),
    ("Colombia", "South America", 51_000_000, 6_131, 31.2, 77.3, "N"),
    ("Peru", "South America", 33_000_000, 6_692, 29.6, 76.7, "S"),
    ("Saudi Arabia", "Asia", 35_000_000, 23_139, 31.8, 76.9, "N"),
    ("Israel", "Asia", 9_400_000, 52_170, 30.1, 82.6, "N"),
    ("Vietnam", "Asia", 98_200_000, 3_756, 32.5, 75.4, "N"),
    ("Thailand", "Asia", 71_600_000, 7_066, 40.1, 79.3, "N"),
    ("Philippines", "Asia", 113_900_000, 3_499, 25.7, 71.7, "N"),
    ("Pakistan", "Asia", 231_400_000, 1_505, 20.6, 67.3, "N"),
    ("Bangladesh", "Asia", 169_400_000, 2_688, 27.6, 72.8, "N"),
    ("Netherlands", "Europe", 17_500_000, 57_767, 42.5, 82.3, "N"),
    ("Belgium", "Europe", 11_600_000, 51_247, 42.0, 82.0, "N"),
    ("Switzerland", "Europe", 8_700_000, 91_992, 42.7, 84.0, "N"),
    ("Portugal", "Europe", 10_300_000, 24_262, 45.6, 82.1, "N"),
    ("Greece", "Europe", 10_400_000, 20_876, 45.6, 81.9, "N"),
    ("Ukraine", "Europe", 43_800_000, 4_836, 41.4, 72.1, "N"),
    ("Ethiopia", "Africa", 120_300_000, 1_027, 19.5, 66.6, "N"),
    ("Ghana", "Africa", 31_700_000, 2_206, 21.5, 64.1, "N"),
    ("Morocco", "Africa", 37_100_000, 3_795, 29.7, 76.7, "N"),
    ("United Arab Emirates", "Asia", 9_900_000, 43_103, 33.5, 78.7, "N"),
    ("Malaysia", "Asia", 32_800_000, 11_371, 30.3, 76.2, "N"),
    ("Singapore", "Asia", 5_900_000, 72_794, 42.2, 83.6, "N"),
    ("Iran", "Asia", 85_000_000, 4_294, 32.5, 76.7, "N"),
    ("Iraq", "Asia", 41_200_000, 4_890, 21.2, 70.6, "N"),
]

n_countries = len(COUNTRIES)

# ---------------------------------------------------------------------------
# 2. DATE RANGE: 2 years of daily data (Jan 2021 - Dec 2022) = 730 days
# ---------------------------------------------------------------------------
start_date = datetime(2021, 1, 1)
n_days = 730
dates = [start_date + timedelta(days=i) for i in range(n_days)]

# ---------------------------------------------------------------------------
# 3. "Pareto" tier assignment: a handful of countries drive most global volume
#    (mirrors the real-world pattern where US/India/Brazil/etc dominate totals)
# ---------------------------------------------------------------------------
gdp_values = np.array([c[3] for c in COUNTRIES])
pop_values = np.array([c[2] for c in COUNTRIES])

# Tier 1 = top 20% of countries by population -> higher absolute case volume
pop_rank = pd.Series(pop_values).rank(ascending=False)
tier1_mask = pop_rank <= max(1, int(n_countries * 0.2))

records = []

for idx, (country, continent, population, gdp, med_age, life_exp, hemi) in enumerate(COUNTRIES):
    # -----------------------------------------------------------------
    # Country-specific parameters driven by real-world covariates
    # -----------------------------------------------------------------
    # Wealthier / better health-system countries test more -> higher detection rate
    testing_capacity = np.clip(0.15 + (gdp / 100_000) * 0.7 + np.random.normal(0, 0.05), 0.08, 0.85)

    # Older populations + lower GDP -> higher case fatality rate (CFR)
    base_cfr = 0.004 + (med_age / 100) * 0.03 - (gdp / 200_000) * 0.01
    base_cfr = np.clip(base_cfr + np.random.normal(0, 0.001), 0.003, 0.045)

    # Stringency varies by country (policy response), affects transmission damping
    stringency_baseline = np.clip(np.random.normal(55, 15), 20, 90)

    # Pareto scaling: tier-1 (populous) countries get amplified attack rate due to density/testing
    pareto_multiplier = 1.6 if tier1_mask[idx] else np.random.uniform(0.5, 1.1)

    # Attack rate: cumulative % of population infected by end of window (realistic 5%-35% range)
    attack_rate = np.clip(np.random.uniform(0.05, 0.22) * pareto_multiplier, 0.03, 0.40)
    total_potential_cases = population * attack_rate

    # Two to three waves per country, seasonally timed by hemisphere
    # Northern hemisphere -> winter waves around day ~15 (Jan) and ~380 (next Jan)
    # Southern hemisphere -> winter waves around day ~180 (Jun/Jul) and ~545
    if hemi == "N":
        wave_centers = [15, 250, 400, 620]
    else:
        wave_centers = [180, 250, 545, 620]
    wave_widths = [45, 35, 55, 30]
    wave_weights = [0.30, 0.15, 0.35, 0.20]

    daily_new_infections = np.zeros(n_days)
    for center, width, weight in zip(wave_centers, wave_widths, wave_weights):
        t = np.arange(n_days)
        gauss = np.exp(-0.5 * ((t - center) / width) ** 2)
        daily_new_infections += gauss * weight

    # normalize so the waves sum to the total potential (true) infections
    daily_new_infections = daily_new_infections / daily_new_infections.sum() * total_potential_cases

    # Add mild autocorrelated noise (real epidemic curves are not perfectly smooth)
    noise = np.random.normal(1.0, 0.06, n_days)
    noise = pd.Series(noise).rolling(3, min_periods=1).mean().values
    daily_new_infections = np.clip(daily_new_infections * noise, 0, None)

    # Detected (reported) new cases = true infections * testing capacity (detection rate)
    # with a gradual improvement in testing infrastructure over time
    testing_growth = np.linspace(testing_capacity * 0.6, testing_capacity, n_days)
    daily_new_cases = daily_new_infections * testing_growth

    # Weekend under-reporting effect (real health-department reporting artifact)
    weekday_factor = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.72, 0.55])
    dow = np.array([d.weekday() for d in dates])
    daily_new_cases = daily_new_cases * weekday_factor[dow]

    daily_new_cases = np.round(daily_new_cases).astype(int)
    daily_new_cases = np.clip(daily_new_cases, 0, None)

    # Deaths lag cases by ~12 days on average, driven by CFR, with its own smoothing
    lag = 12
    lagged_cases = np.concatenate([np.zeros(lag), daily_new_infections[:-lag] if lag < n_days else np.zeros(n_days)])
    daily_new_deaths = lagged_cases * base_cfr
    daily_new_deaths = daily_new_deaths * (weekday_factor[dow] * 0.3 + 0.7)  # smaller weekend dip for deaths
    daily_new_deaths = np.round(np.clip(daily_new_deaths, 0, None)).astype(int)

    total_cases = np.cumsum(daily_new_cases)
    total_deaths = np.cumsum(daily_new_deaths)

    # Recovered: assume ~14-21 day recovery window, ~97% of resolved cases recover
    recovery_lag = 18
    resolved = np.concatenate([np.zeros(recovery_lag), total_cases[:-recovery_lag] if recovery_lag < n_days else np.zeros(n_days)])
    total_recovered = np.round(resolved * 0.965).astype(int)
    total_recovered = np.minimum(total_recovered, total_cases)

    active_cases = np.clip(total_cases - total_deaths - total_recovered, 0, None)

    # Tests conducted: positivity rate implied ~ new_cases / tests, kept realistic (2%-25%)
    positivity_target = np.clip(0.03 + (1 - testing_capacity) * 0.18, 0.02, 0.30)
    daily_tests = np.where(daily_new_cases > 0, daily_new_cases / np.maximum(positivity_target, 0.01), population * 0.0005)
    daily_tests = np.round(daily_tests).astype(int)
    total_tests = np.cumsum(daily_tests)
    positive_rate = np.round(np.divide(daily_new_cases, np.maximum(daily_tests, 1)), 4)

    # Vaccination rollout: starts ~day 30-90 depending on GDP (wealthier countries start earlier)
    vax_start = int(np.clip(90 - (gdp / 100_000) * 70 + np.random.normal(0, 8), 15, 110))
    vax_speed = np.clip(0.0025 + (gdp / 100_000) * 0.006, 0.0012, 0.009)  # logistic growth rate
    t = np.arange(n_days) - vax_start
    vax_capacity = np.clip(0.55 + (gdp / 150_000), 0.4, 0.96)  # ceiling coverage
    fully_vax_pct = vax_capacity / (1 + np.exp(-vax_speed * t))
    fully_vax_pct = np.where(np.arange(n_days) < vax_start, 0, fully_vax_pct)
    people_fully_vaccinated = np.round(fully_vax_pct * population).astype(int)
    people_vaccinated = np.round(np.minimum(fully_vax_pct * 1.18, 0.98) * population).astype(int)
    booster_start = vax_start + 200
    booster_pct = np.clip((fully_vax_pct * 0.55) * (1 / (1 + np.exp(-0.006 * (np.arange(n_days) - booster_start)))), 0, None)
    total_boosters = np.round(booster_pct * population).astype(int)

    # ICU / hospitalization proxy: correlates with active cases and inversely with vaccination
    icu_rate = np.clip(0.015 - (fully_vax_pct * 0.01), 0.003, 0.02)
    icu_patients = np.round(active_cases * icu_rate).astype(int)
    hosp_rate = icu_rate * 4.2
    hosp_patients = np.round(active_cases * hosp_rate).astype(int)

    # Reproduction rate (Rt): oscillates around 1.0, driven by wave momentum
    new_case_growth = pd.Series(daily_new_infections).pct_change().fillna(0)
    reproduction_rate = np.clip(1.0 + new_case_growth.rolling(7, min_periods=1).mean().values * 3, 0.5, 2.5)

    # Stringency index responds (with lag) to active case load - governments tighten under pressure
    active_pct_pop = active_cases / population
    stringency_index = np.clip(
        stringency_baseline + (active_pct_pop / active_pct_pop.max() if active_pct_pop.max() > 0 else 0) * 35 + np.random.normal(0, 3, n_days),
        10, 100
    )

    for i, d in enumerate(dates):
        records.append({
            "country": country,
            "continent": continent,
            "date": d.strftime("%Y-%m-%d"),
            "population": population,
            "median_age": med_age,
            "gdp_per_capita": gdp,
            "life_expectancy": life_exp,
            "total_cases": int(total_cases[i]),
            "new_cases": int(daily_new_cases[i]),
            "total_deaths": int(total_deaths[i]),
            "new_deaths": int(daily_new_deaths[i]),
            "total_recovered": int(total_recovered[i]),
            "active_cases": int(active_cases[i]),
            "total_tests": int(total_tests[i]),
            "new_tests": int(daily_tests[i]),
            "positive_rate": float(positive_rate[i]) if np.isfinite(positive_rate[i]) else 0.0,
            "people_vaccinated": int(people_vaccinated[i]),
            "people_fully_vaccinated": int(people_fully_vaccinated[i]),
            "total_boosters": int(total_boosters[i]),
            "icu_patients": int(icu_patients[i]),
            "hosp_patients": int(hosp_patients[i]),
            "reproduction_rate": round(float(reproduction_rate[i]), 2),
            "stringency_index": round(float(stringency_index[i]), 1),
        })

df = pd.DataFrame.from_records(records)

# ---------------------------------------------------------------------------
# 4. Inject realistic data-quality issues for the cleaning script to handle
#    (duplicates, missing values, inconsistent casing, stray negative artifacts)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(7)

# a) Duplicate ~0.4% of rows
dup_idx = rng.choice(df.index, size=int(len(df) * 0.004), replace=False)
df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

# b) Null out some positive_rate / icu_patients values (reporting gaps)
null_idx = rng.choice(df.index, size=int(len(df) * 0.015), replace=False)
df.loc[null_idx, "positive_rate"] = np.nan
null_idx2 = rng.choice(df.index, size=int(len(df) * 0.01), replace=False)
df.loc[null_idx2, "icu_patients"] = np.nan

# c) Inconsistent country-name casing/whitespace for a subset of rows (real OWID-style mess)
messy_idx = rng.choice(df.index, size=int(len(df) * 0.01), replace=False)
df.loc[messy_idx, "country"] = df.loc[messy_idx, "country"].str.upper() + "  "

# d) A few negative new_cases artifacts (retroactive corrections in real datasets)
neg_idx = rng.choice(df.index, size=25, replace=False)
df.loc[neg_idx, "new_cases"] = -abs(df.loc[neg_idx, "new_cases"])

df.to_csv("/home/claude/covid-tracker/dataset/covid_data_raw.csv", index=False)
print(f"Generated {len(df):,} rows across {n_countries} countries, {n_days} days.")
print(df.head())
