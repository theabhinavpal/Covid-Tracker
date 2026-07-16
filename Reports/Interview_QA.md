# Interview Prep: SQL, Python & Analytics Q&A

## How to Talk About This Project in an Interview (30-second version)

"I built an end-to-end COVID analytics pipeline — generated a realistic 36,500-row country-day dataset with real epidemiological patterns baked in (seasonal waves, Pareto-concentrated case volume, GDP-driven vaccination speed), cleaned it with a documented pipeline handling duplicates, missing values, and negative-value artifacts, loaded it into a normalized SQL database with views and indexes, then wrote 25 SQL queries using window functions, CTEs, and ranking to answer real business questions. The headline finding: vaccination rate and GDP per capita correlate at r=0.98, and vaccination rate predicts case-fatality rate at r=-0.79 — I can walk through how I validated that and the confound I found with median age."

---

## Resume Bullet Points (ATS-friendly)

1. Designed and built an end-to-end COVID-19 analytics pipeline processing 36,500+ records across 50 countries, using Python (pandas, NumPy) for ETL and SQLite for a normalized, indexed relational schema.
2. Wrote 25 production-quality SQL queries leveraging window functions (RANK, NTILE, LAG, moving averages), CTEs, and views to surface Pareto concentration, vaccination-mortality correlation, and wave-detection insights.
3. Built a documented data-cleaning pipeline resolving duplicate records, missing values, and inconsistent entity naming, with automated validation assertions before database load.
4. Quantified key public-health relationships using Pearson correlation and bucketed cohort analysis (e.g., GDP per capita vs. vaccination rate: r=0.98; vaccination rate vs. case fatality rate: r=-0.79), identifying and correctly flagging a confounding variable in the age-mortality relationship.
5. Delivered 6 executive-ready visualizations (Matplotlib/Seaborn) and a full business-insights report translating raw statistics into prioritized, actionable recommendations.

---

## SQL Interview Questions

1. **What's the difference between a window function and a GROUP BY aggregation?**
   GROUP BY collapses rows into one row per group. A window function (e.g., `SUM(...) OVER (PARTITION BY ...)`) keeps every row but computes an aggregate "over a window" of related rows — used in this project for running totals (Q2) and continent rankings (Q3) without losing row-level detail.

2. **Walk through how you'd calculate a 7-day moving average in SQL.**
   `AVG(new_cases) OVER (PARTITION BY country ORDER BY report_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` — see Q5 in this project for a 30-day variant applied to three countries.

3. **What's the difference between RANK(), DENSE_RANK(), and ROW_NUMBER()?**
   RANK() leaves gaps after ties (1,1,3); DENSE_RANK() doesn't (1,1,2); ROW_NUMBER() ignores ties entirely and assigns a unique sequential number. Q3 uses RANK() so tied countries share a rank rather than being arbitrarily ordered.

4. **Why use a view instead of just writing the query each time?**
   Views centralize business logic (e.g., `vw_country_latest` = "most recent row per country") so every downstream query gets the same definition instead of six slightly-different re-implementations. It also makes SELECT * from a view readable in a BI tool.

5. **How do you find the top N per group in SQL?**
   Window function with PARTITION BY + a rank function, filtered in an outer query, e.g., `WHERE continent_rank <= 5`. This project's Q3 demonstrates the PARTITION BY pattern (the outer filter was omitted only to show the full ranked table).

6. **What's a CTE and when would you use one over a subquery?**
   A Common Table Expression (`WITH x AS (...)`) is a named, reusable result set for the query that follows. It's preferred over nested subqueries when the same intermediate result is referenced multiple times, or simply for readability — see Q4's Pareto quintile analysis, which would be unreadable as a nested subquery.

7. **How would you detect duplicate rows in a large table without a unique constraint?**
   `GROUP BY <candidate key columns> HAVING COUNT(*) > 1`, or `ROW_NUMBER() OVER (PARTITION BY <key> ORDER BY <tiebreaker>) ` and delete/flag rows where the row number > 1. Applied in `etl/clean_data.py` via pandas' `drop_duplicates`, but the SQL-native version is the same logic.

8. **What's the difference between HAVING and WHERE?**
   WHERE filters rows before aggregation; HAVING filters groups after aggregation. Q8 uses HAVING to filter out countries whose average growth rate is NULL after the GROUP BY.

9. **How would you handle a correlated subquery for "find the max value per group" efficiently?**
   A correlated subquery like Q17 (peak new cases per country) works but re-scans per outer row; at scale, a window function (`MAX(...) OVER (PARTITION BY country)` compared against `new_cases`) is typically more efficient since it's a single pass.

10. **How do you decide what to index?**
    Index columns used in WHERE/JOIN/ORDER BY on large tables — here, `(country_id, report_date)` composite index supports both the per-country time-series queries and the join pattern used in nearly every query in this project.

---

## Python / Pandas Interview Questions

1. **How do you compute a rolling average in pandas, and why would you group first?**
   `df.groupby('country')['new_cases'].transform(lambda s: s.rolling(7).mean())` — grouping first prevents the rolling window from bleeding across country boundaries, which would silently corrupt the 7-day averages in this project if omitted.

2. **What's the difference between `.transform()` and `.apply()` on a groupby object?**
   `.transform()` returns a result the same shape as the input (broadcast back to every row) — used throughout `clean_data.py` for exactly this reason (adding a per-row derived column). `.apply()` can return arbitrary shapes, which is more flexible but easy to misuse when you actually want a same-shape column.

3. **How do you handle missing values, and how do you decide between drop/fill/impute?**
   Depends on why it's missing. In this project, `positive_rate` gaps were recomputed from other present columns (more accurate than any fill); `icu_patients` gaps were forward-filled because ICU census is slow-changing day to day. Blanket `fillna(0)` would have been wrong for both — it would understate real values.

4. **Why use `np.clip()` instead of manually filtering out-of-range values?**
   Clipping preserves the row and its other columns while capping the specific value — important when the surrounding row still has valid information you don't want to lose (e.g., flooring a negative `new_cases` value to 0 rather than dropping the whole day's record).

5. **What's a vectorized operation and why does it matter for performance?**
   An operation applied to an entire array/Series at once via NumPy/pandas' underlying C implementation instead of a Python-level loop. The whole dataset generator (`generate_dataset.py`) is vectorized per-country using NumPy arrays across 730 days, which is why 50 countries × 730 days materializes in under a second.

6. **How would you merge two DataFrames and handle mismatched keys?**
   `pd.merge(df1, df2, how='left', on='key')`, then check for unmatched rows with `df['key_col'].isna().sum()` post-merge. `load_data.py` does this to map country names to their surrogate `country_id` before loading facts.

7. **What's the difference between `.loc[]` and `.iloc[]`?**
   `.loc[]` is label-based indexing (works with boolean masks and column names); `.iloc[]` is purely positional (integer row/column indices). This project uses `.loc[]` throughout for boolean-mask-based conditional assignment (e.g., injecting synthetic data-quality issues at random row indices).

8. **How do you profile and speed up a slow pandas pipeline?**
   Avoid row-wise `.apply()` where a vectorized operation exists; use `.groupby().transform()` instead of manual loops; consider `category` dtype for repeated strings like country names.

9. **What's the risk of using `SettingWithCopyWarning`-triggering code, and how do you avoid it?**
   It signals you might be modifying a view/slice of a DataFrame rather than the DataFrame itself, so the assignment may silently not persist. Avoided by chaining `.copy()` after any filter/slice you intend to mutate, or using `.loc[]` for the assignment directly on the original frame.

10. **How would you validate a cleaned dataset before loading it into a database?**
    Assertion checks on invariants that must always hold — this project's `validate()` function in `clean_data.py` checks no null dates, no negative case counts, deaths never exceeding cases, and no surviving duplicate keys, and raises before writing if any fail.

---

## Data Analytics Interview Questions

1. **How do you decide whether a correlation is meaningful or a confound?**
   Check whether a third variable plausibly drives both. This project found median age negatively correlated with CFR (r=-0.43) — the opposite of the expected direction — because GDP per capita (r=-0.78 with CFR) confounds it: wealthier countries in this dataset skew older *and* have better health outcomes. The fix is reporting both variables together, not picking whichever tells a cleaner story.

2. **How do you communicate a counter-intuitive finding to a non-technical stakeholder?**
   Lead with the surprising number, then immediately explain the likely mechanism in one sentence, then give the actionable takeaway — don't bury the caveat in a footnote if it changes what decision the number supports.

3. **What's the difference between correlation and causation, concretely, in this project?**
   The stringency-vs-growth finding (Q18) shows high-stringency periods had the *least* negative growth — but stringency was modeled to respond reactively to case load, so the correlation reflects governments tightening policy during active waves, not policy failing to work. Without a lagged or quasi-experimental design, the data can't distinguish "strict policy failed" from "strict policy was applied precisely when growth was hardest to control."

4. **How would you segment countries for a resource-allocation recommendation?**
   Bucket by a business-relevant driver (GDP tier, as in Q14) rather than by outcome alone — segmenting by outcome (e.g., "high CFR countries") describes the problem without pointing to an intervention lever; segmenting by GDP tier points directly at a financing intervention.

5. **What would you check before trusting a "top 10 countries" leaderboard?**
   Whether the ranking metric is population-adjusted (raw totals favor large countries) and whether it's confounded by testing rate (Q16 shows testing rate correlates at r=0.92 with reported cases per million — low-testing countries look artificially "safe").

6. **How do you decide which KPIs belong in an executive summary vs. an appendix?**
   Executive KPIs should be decision-relevant and hard to misread (global CFR, vaccination coverage); anything requiring a caveat to interpret correctly (like the recovery-rate KPI in this project, which is a modeling constant, not real variation) belongs in a footnote or appendix, clearly labeled.

7. **How would you handle a stakeholder who wants you to remove a caveat because it "complicates the story"?**
   Keep the number, shorten the caveat to one clause instead of a paragraph, but don't remove it — a headline number that misleads the reader is a bigger risk to your credibility (and their decision) than a slightly less clean narrative.

8. **What's your process for exploratory data analysis on an unfamiliar dataset?**
   Shape/dtypes/nulls first, then univariate distributions, then the specific business questions, checking each significant finding against a plausible alternative explanation before writing it up — exactly the process that surfaced the age/CFR confound in Finding #3.

9. **How do you validate that your cleaning logic didn't distort the underlying signal?**
   Compare key aggregate statistics (row counts, sums, group averages) before and after cleaning; in this project, `load_data.py`'s sanity checks confirm row counts and date ranges post-load, and `clean_data.py`'s assertions guard the specific invariants cleaning could break.

10. **How do you decide between reporting a mean vs. a median for a skewed metric?**
    Case counts are extremely right-skewed (Pareto — Q4 shows the top quintile holds 78.9% of cases), so a mean total-cases-per-country would be dominated by outliers; median or the explicit quintile/decile breakdown communicates the real shape better.

---

## Business Intelligence Interview Questions

1. **What makes a good KPI vs. a vanity metric?**
   A good KPI is comparable over time/across segments and tied to a decision. "Total cases" alone is a vanity metric across countries of different sizes; "cases per million" is the decision-useful version.

2. **How would you design a dashboard for a public-health executive vs. a data analyst audience?**
   Executive: 4-6 headline KPIs, one trend chart, one leaderboard, minimal interactivity. Analyst: full drill-down by country/continent/date, raw query access, and the underlying assumptions documented (as in this project's Data Dictionary).

3. **What's the value of a database view over querying raw tables in a BI tool?**
   Consistency and reduced burden on the BI layer — `vw_country_latest` guarantees every downstream chart uses the identical "most recent date per country" logic instead of each dashboard author re-deriving it slightly differently.

4. **How do you decide on the grain of a fact table?**
   Grain should match the finest level of detail any planned analysis needs — this project uses country-day because both daily trend charts and monthly rollups can be derived from it, whereas a pre-aggregated monthly table couldn't answer daily questions.

5. **How would you extend this project into a real-time dashboard?**
   Swap the one-time `load_data.py` batch load for an incremental daily ETL job (extract yesterday's new rows, transform, upsert), and point a BI tool (Power BI / Tableau / Streamlit) at the same schema/views rather than the raw table.

6. **What's the risk of a dashboard that only shows current totals with no trend context?**
   A snapshot without trend hides momentum — a country at "medium" absolute cases but accelerating (positive week-over-week growth) is a bigger near-term risk than one at "high" absolute cases but declining, and a totals-only view can't distinguish them.

7. **How do you handle conflicting numbers between two reports pulling from the same source?**
   Trace both back to the underlying view/query definition — usually the discrepancy is a different filter (e.g., "latest date" vs. "as of report month") or a different aggregation grain, not bad data.

8. **What would you monitor to catch a broken ETL pipeline before a stakeholder sees bad numbers?**
   Row-count and date-range sanity checks post-load (as in `load_data.py`), plus invariant assertions pre-load (as in `clean_data.py`) — catching "deaths exceed cases" or "duplicate keys" before they ever reach a dashboard.

9. **How would you prioritize which of the 25 SQL queries in this project to turn into a live dashboard page vs. keep as an ad-hoc query?**
   Dashboard pages for anything a stakeholder will ask repeatedly with the same shape but new numbers (headline KPIs, leaderboards, trend lines); ad-hoc for one-off investigative questions (the age/CFR confound, the stringency-endogeneity finding) that need a human to interpret the caveat each time.

10. **How do you communicate uncertainty or data-quality limitations in a BI report without undermining stakeholder confidence?**
    State it plainly and specifically (as in this project's "Known Limitation" note on total-recovered) rather than either hiding it or hedging every number — specific, bounded caveats read as rigor; vague ones read as lack of confidence.
