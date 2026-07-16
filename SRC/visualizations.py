"""
visualizations.py
-------------------
Generates the core visualization set used in reports/Business_Insights.md,
reading directly from the live SQLite database (not the raw CSV) so the charts
match exactly what the SQL layer reports.

Run:
    python3 src/visualizations.py
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", context="talk")
DB = "/home/claude/covid-tracker/database/covid_tracker.db"
OUT = "/home/claude/covid-tracker/images/charts"

conn = sqlite3.connect(DB)


def chart_global_trend():
    df = pd.read_sql("""
        SELECT report_date, SUM(new_cases) AS new_cases, SUM(new_deaths) AS new_deaths
        FROM covid_facts GROUP BY report_date ORDER BY report_date
    """, conn)
    df["report_date"] = pd.to_datetime(df["report_date"])
    df["cases_7d"] = df["new_cases"].rolling(7).mean()
    df["deaths_7d"] = df["new_deaths"].rolling(7).mean()

    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax1.plot(df["report_date"], df["cases_7d"], color="#2563eb", linewidth=2, label="New cases (7d avg)")
    ax1.set_ylabel("Global new cases (7-day avg)", color="#2563eb")
    ax1.tick_params(axis="y", labelcolor="#2563eb")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}K"))

    ax2 = ax1.twinx()
    ax2.plot(df["report_date"], df["deaths_7d"], color="#dc2626", linewidth=2, label="New deaths (7d avg)")
    ax2.set_ylabel("Global new deaths (7-day avg)", color="#dc2626")
    ax2.tick_params(axis="y", labelcolor="#dc2626")
    ax2.grid(False)

    plt.title("Global COVID-19 Wave Pattern: New Cases vs. New Deaths (2021–2022)", fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT}/01_global_trend.png", dpi=140)
    plt.close(fig)


def chart_pareto():
    df = pd.read_sql("SELECT country_name, total_cases FROM vw_country_latest ORDER BY total_cases DESC", conn)
    df["cum_pct"] = df["total_cases"].cumsum() / df["total_cases"].sum() * 100
    top15 = df.head(15)

    fig, ax1 = plt.subplots(figsize=(13, 6))
    bars = ax1.bar(top15["country_name"], top15["total_cases"], color="#2563eb")
    ax1.set_ylabel("Total cases", color="#2563eb")
    ax1.tick_params(axis="x", rotation=55)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))

    ax2 = ax1.twinx()
    ax2.plot(top15["country_name"], top15["cum_pct"], color="#dc2626", marker="o", linewidth=2)
    ax2.set_ylabel("Cumulative % of global cases", color="#dc2626")
    ax2.set_ylim(0, 105)
    ax2.grid(False)
    ax2.axhline(80, color="#dc2626", linestyle="--", alpha=0.4)

    plt.title("Pareto Concentration: Top 15 Countries Drive ~79% of Global Cases", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT}/02_pareto_concentration.png", dpi=140)
    plt.close(fig)


def chart_vax_vs_cfr():
    df = pd.read_sql("""
        SELECT country_name, vaccination_rate_pct, case_fatality_rate, gdp_per_capita, continent
        FROM vw_country_latest
    """, conn)
    fig, ax = plt.subplots(figsize=(11, 7))
    scatter = ax.scatter(
        df["vaccination_rate_pct"], df["case_fatality_rate"],
        s=df["gdp_per_capita"] / 400, c=df["gdp_per_capita"], cmap="viridis", alpha=0.75, edgecolor="white"
    )
    ax.set_xlabel("Fully vaccinated (% of population)")
    ax.set_ylabel("Case Fatality Rate (%)")
    ax.set_title("Vaccination Rate vs. Case Fatality Rate\n(bubble size/color = GDP per capita) — r = -0.79", fontsize=14, fontweight="bold")
    cbar = plt.colorbar(scatter)
    cbar.set_label("GDP per capita (USD)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/03_vaccination_vs_cfr.png", dpi=140)
    plt.close(fig)


def chart_continent_comparison():
    df = pd.read_sql("""
        SELECT continent, SUM(total_cases) AS total_cases, SUM(total_deaths) AS total_deaths,
               ROUND(100.0*SUM(total_deaths)/SUM(total_cases),2) AS cfr
        FROM vw_country_latest GROUP BY continent ORDER BY total_cases DESC
    """, conn)
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.barplot(data=df, x="continent", y="total_cases", ax=axes[0], color="#2563eb")
    axes[0].set_title("Total Cases by Continent")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
    axes[0].tick_params(axis="x", rotation=30)

    sns.barplot(data=df, x="continent", y="cfr", ax=axes[1], color="#dc2626")
    axes[1].set_title("Case Fatality Rate by Continent (%)")
    axes[1].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(f"{OUT}/04_continent_comparison.png", dpi=140)
    plt.close(fig)


def chart_vax_rollout_lines():
    df = pd.read_sql("""
        SELECT c.country_name, f.report_date, f.vaccination_rate_pct
        FROM covid_facts f JOIN countries c ON c.country_id = f.country_id
        WHERE c.country_name IN ('United States','Germany','India','South Africa','Brazil','Japan')
        ORDER BY f.report_date
    """, conn)
    df["report_date"] = pd.to_datetime(df["report_date"])
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for country, grp in df.groupby("country_name"):
        ax.plot(grp["report_date"], grp["vaccination_rate_pct"], linewidth=2.2, label=country)
    ax.set_ylabel("Fully vaccinated (% of population)")
    ax.set_title("Vaccination Rollout Speed: Selected Countries (2021–2022)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{OUT}/05_vaccination_rollout.png", dpi=140)
    plt.close(fig)


def chart_heatmap_monthly():
    df = pd.read_sql("""
        SELECT country_name, report_month, monthly_new_cases FROM vw_monthly_country_summary
        WHERE country_name IN ('United States','India','Brazil','United Kingdom','Germany','South Africa','Japan','Russia','France','Australia')
    """, conn)
    pivot = df.pivot(index="country_name", columns="report_month", values="monthly_new_cases")
    fig, ax = plt.subplots(figsize=(16, 6))
    sns.heatmap(pivot, cmap="Reds", ax=ax, cbar_kws={"label": "Monthly new cases"})
    ax.set_title("Monthly New Case Heatmap: Wave Timing by Country (2021–2022)", fontsize=14, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(f"{OUT}/06_wave_heatmap.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    chart_global_trend()
    chart_pareto()
    chart_vax_vs_cfr()
    chart_continent_comparison()
    chart_vax_rollout_lines()
    chart_heatmap_monthly()
    print("All 6 charts generated in images/charts/")
