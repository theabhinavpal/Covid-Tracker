# KPI Report

Source: `reports/SQL_Query_Results.md` Q23 (global summary) and the per-query results referenced below. All values computed against the live database as of the last date in the window, 2022-12-31.

## Global Headline KPIs

| KPI | Value | Query |
|---|---|---|
| Total Cases | 179,098,660 | Q23 |
| Total Deaths | 12,639,183 | Q23 |
| Total Recovered | 172,790,000 (approx, model-constant recovery rate — see note below) | Q23 |
| Active Cases (latest date) | 228,741 | Q23 |
| Global Case Fatality Rate | 7.06% | Q23 |
| Average Country Vaccination Rate | 65.4% | Q23 |
| Countries Below 50% Full Vaccination | 14 / 50 (28%) | Q11 |

## Leaderboards

| KPI | Country | Value |
|---|---|---|
| Highest Cases per Million | Norway | 79,706.3 | 
| Highest Deaths per Million (global) | China | 2,732.7 |
| Fastest Vaccination Rollout (avg monthly gain) | Switzerland / Norway | +4.16 pts/month |
| Lowest Testing Rate | Egypt | 2.3% of population |
| Highest Single-Day Case Spike | China, 2022-01-27 | 218,162 new cases |

## Growth & Momentum

| KPI | Value | Query |
|---|---|---|
| 2021 Global New Cases | 75,899,955 | Q20 |
| 2022 Global New Cases | 103,091,624 (+35.8% YoY) | Q20 |
| 2021 Global New Deaths | 5,652,825 | Q20 |
| 2022 Global New Deaths | 6,986,358 (+23.6% YoY) | Q20 |
| Country-days with Rt > 1.2 (South America) | 176 — highest of any continent | Q21 |

## Note on Total Recovered

The recovery-rate model in `etl/generate_dataset.py` applies a fixed 96.5%-of-resolved-cases assumption uniformly across all countries (see `case_fatality_rate` for the country-level differentiation instead — that metric does vary meaningfully by country and is the more reliable severity KPI in this dataset). A production version pulling real OWID recovery data would show genuine country-level variation here; flagged for transparency rather than presented as a differentiated finding it isn't.
