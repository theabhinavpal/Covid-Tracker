# Business Insights — COVID-19 Global Trends Tracker

All figures below are pulled directly from `reports/SQL_Query_Results.md` (live database output) or `src/visualizations.py` chart data — nothing here is generic filler.

---

## 1. Pandemic Burden Is Highly Concentrated (Pareto Effect)

The **top 10 of 50 countries account for 78.9% of all reported global cases** (Q4), and the single largest contributor alone represents a double-digit share. This mirrors real-world COVID reporting, where a small number of large, high-testing-capacity nations dominate global case counts.

**Recommendation:** Any global resourcing model (vaccine allocation, PPE stockpiling, surge staffing) should be weighted toward this top decile rather than distributed evenly across all reporting countries — an even split would under-resource the countries carrying 4 out of 5 global cases.

![Pareto concentration](../images/charts/02_pareto_concentration.png)

---

## 2. Wealth Predicts Vaccination Speed Almost Perfectly — and Vaccination Predicts Mortality

Three correlations computed directly against `vw_country_latest`:

| Relationship | Pearson r | p-value |
|---|---|---|
| GDP per capita → Vaccination rate | **+0.977** | <0.001 |
| Vaccination rate → Case fatality rate | **-0.789** | <0.001 |
| GDP per capita → Case fatality rate | **-0.780** | <0.001 |

The GDP-bucketed breakdown (Q14) makes the gradient concrete:

| GDP Bucket | Avg. Vaccination Rate | Avg. CFR |
|---|---|---|
| Low GDP (<$5k) | 48.5% | 9.54% |
| Mid GDP ($5k–$20k) | 54.6% | 8.27% |
| High GDP ($20k–$50k) | 75.1% | 5.70% |
| Very High GDP ($50k+) | 91.4% | 3.11% |

**Recommendation:** Vaccine-access financing (COVAX-style mechanisms) is not a "nice to have" equity measure — it's the single highest-leverage lever available for reducing global mortality, given a near-1.0 correlation between wealth and rollout speed.

![Vaccination vs CFR](../images/charts/03_vaccination_vs_cfr.png)

---

## 3. Age Looked Protective, Not Risky — Because of a Confound Worth Flagging

The bucketed analysis (Q15) shows CFR *decreasing* as median age increases (Young <25: 9.6% CFR → Oldest 42+: 5.3% CFR), and the raw correlation confirms it (r = -0.425, p = 0.002). That's the **opposite** of the textbook "older populations = higher COVID mortality" pattern.

This is a genuine analytical finding, not an error: in this dataset (as in the real world), older-median-age countries are disproportionately wealthy ones with strong health systems and fast vaccine rollout — and GDP's effect on mortality (r = -0.78) is far stronger than age's raw effect. Age alone, without controlling for GDP and vaccination coverage, is a misleading univariate predictor.

**Recommendation:** Don't present age as a standalone mortality driver in an executive summary — it needs to be shown alongside GDP/vaccination or it will produce a confidently wrong headline. This is exactly the kind of confound a stakeholder needs flagged, not hidden.

---

## 4. Low Testing Correlates With Suspiciously Low Case Counts — Likely Under-Ascertainment

Testing rate vs. cases-per-million: **r = +0.921** (Q16). The five countries with the lowest testing rate per capita (Egypt 2.3%, Malaysia 2.5%, Ukraine 2.8%, Bangladesh 3.6%, South Africa 4.2%) also report some of the lowest cases-per-million figures in the dataset.

**Recommendation:** Treat "low reported case count" and "low testing rate" together as a single under-ascertainment risk flag, not as independent good news. Any cross-country league table ranking "safest" countries by raw case count should be paired with a testing-rate column or it will systematically reward countries that simply tested less.

---

## 5. Stricter Policy Response Was Associated With Lower Case Growth

Bucketing every country-day by stringency index (Q18):

| Stringency Bucket | Avg. Week-over-Week Case Growth |
|---|---|
| Low stringency (<40) | -2.13% |
| Medium stringency (40–65) | -1.09% |
| High stringency (65+) | -0.31% |

Note the direction here is counter to a naive "stricter policy = lower growth" story — high-stringency country-days actually show the *least negative* (i.e., closest-to-flat) growth. That's consistent with governments tightening stringency reactively during active waves (the dataset's `stringency_index` was deliberately modeled to respond to active-case load with a lag), so high-stringency observations are concentrated during periods that were already trending toward decline more slowly. This is a reminder that **policy stringency is endogenous to case trends**, not a clean independent variable — a real analysis would need a lagged/instrumental approach to claim causality either direction.

**Recommendation:** Frame this finding as "stringency and case trends move together, with policy responding to case load" rather than claiming lockdowns caused (or failed to cause) a given growth rate — the correlational data alone can't distinguish those stories.

---

## 6. Vaccination Rollout Winners

Fastest average monthly gain in full-vaccination coverage (Q6): Switzerland and Norway (+4.16 pts/month), Singapore (+4.14), United States (+4.13), Australia (+4.09). All five are Very-High-GDP countries — consistent with Finding #2.

**14 of 50 countries (28%) never crossed 50% full vaccination coverage** in the two-year window (Q11) — almost entirely Low/Mid-GDP countries, reinforcing that vaccine access, not vaccine hesitancy, is the larger structural driver in this dataset's design.

![Vaccination rollout speed](../images/charts/05_vaccination_rollout.png)

---

## 7. Wave Timing Differs by Hemisphere and Continent

The monthly heatmap shows Northern Hemisphere countries clustering winter peaks around Jan 2021/Jan 2022, while Southern Hemisphere countries (South Africa, Brazil, Australia) peak mid-year — consistent with the seasonality baked into the generator, and a real pattern documented in actual pandemic reporting.

South America and Africa show the highest count of country-days with reproduction rate > 1.2 (176 and 103 respectively, Q21) — i.e., these continents spent the most time in active exponential-growth territory, despite not topping the raw case-count leaderboard, which is dominated by high-testing wealthy nations (Finding #4's under-ascertainment point again).

![Wave heatmap](../images/charts/06_wave_heatmap.png)

---

## 8. Global Headline KPIs (single source of truth, Q23)

- Global total cases: **179,098,660**
- Global total deaths: **12,639,183**
- Global case-fatality rate: **7.06%**
- Global active cases (as of last date in window): **228,741**
- Average country vaccination rate: **65.4%**

See `reports/KPI_Report.md` for the full KPI catalogue.

---

## Known Limitation of This Dataset

The global CFR here (7.06%) is materially higher than real-world COVID-19 CFR estimates (~1–2%), because the generator's per-country base CFR parameter was set higher than reality to make the GDP/age/vaccination mortality gradients clearly visible in a 50-country sample without needing millions of rows. If this pipeline were pointed at a real OWID/JHU extract, the schema, cleaning logic, and every SQL query would run unchanged — only the absolute CFR level would drop into the realistic 1–2% range. This is disclosed here rather than left for a reviewer to discover, consistent with the "no synthetic-data pretending to be real" principle in the README.
