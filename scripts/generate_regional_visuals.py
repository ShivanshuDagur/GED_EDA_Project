#!/usr/bin/env python3
"""
Generate Regional and State-Level Infrastructure Visualizations
"""

from pathlib import Path
import sys
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH, VISUALS_DIR
from src.metrics import aggregate_state_metrics, aggregate_regional_metrics
from src.visualization import set_visual_style, plot_regional_breakdowns


def main():
    set_visual_style()
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    state_metrics = aggregate_state_metrics(df, min_candidates=0)
    region_agg = aggregate_regional_metrics(state_metrics)

    # 1. Top 10 States by Center Density
    plt.figure(figsize=(9, 5))
    top_density = state_metrics.sort_values("center_density", ascending=False).head(10)
    sns.barplot(data=top_density, x="center_density", y="C_STATE", palette="viridis")
    plt.title("Top 10 States by Center Density (Centers per Candidate)", fontsize=13, fontweight="bold")
    plt.xlabel("Centers per Candidate", fontsize=11)
    plt.ylabel("State", fontsize=11)
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "top_center_density.png")
    plt.close()

    # 2. Top 10 States by Prep Coverage
    plt.figure(figsize=(9, 5))
    top_prep = state_metrics.sort_values("prep_coverage", ascending=False).head(10)
    sns.barplot(data=top_prep, x="prep_coverage", y="C_STATE", palette="viridis")
    plt.title("Top 10 States by Prep Coverage (% using Prep Center)", fontsize=13, fontweight="bold")
    plt.xlabel("Prep Coverage Rate", fontsize=11)
    plt.ylabel("State", fontsize=11)
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "top_prep_coverage.png")
    plt.close()

    # 3. Regressions: Center Density vs Completion Rate
    plt.figure(figsize=(9, 5))
    sns.regplot(data=state_metrics, x="center_density", y="completion_rate", scatter_kws={"alpha": 0.6}, line_kws={"color": "#d9534f"})
    plt.title("Impact of Center Density on Completion Rate", fontsize=13, fontweight="bold")
    plt.xlabel("Center Density (Centers per Candidate)", fontsize=11)
    plt.ylabel("Completion Rate", fontsize=11)
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "density_vs_completion.png")
    plt.close()

    # 4. Regressions: Prep Coverage vs Completion Rate
    plt.figure(figsize=(9, 5))
    sns.regplot(data=state_metrics, x="prep_coverage", y="completion_rate", scatter_kws={"alpha": 0.6}, line_kws={"color": "#3e8e7e"})
    plt.title("Impact of Prep Coverage on Completion Rate", fontsize=13, fontweight="bold")
    plt.xlabel("Prep Coverage Rate", fontsize=11)
    plt.ylabel("Completion Rate", fontsize=11)
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "prep_vs_completion.png")
    plt.close()

    # 5. Regional Breakdown Charts
    plot_regional_breakdowns(region_agg, VISUALS_DIR)

    # 6. Regional Performance: Enrollment vs Completion
    region_plot = region_agg.melt(
        id_vars="census_region",
        value_vars=["enrollment_rate", "completion_rate"],
        var_name="Metric",
        value_name="Rate",
    )
    region_plot["Metric"] = region_plot["Metric"].map({"enrollment_rate": "Enrollment Rate", "completion_rate": "Completion Rate"})

    plt.figure(figsize=(10, 5))
    sns.barplot(data=region_plot, x="census_region", y="Rate", hue="Metric", palette="mako")
    plt.title("Regional Performance: Enrollment vs. Completion Breakdown", fontsize=13, fontweight="bold")
    plt.xlabel("Census Region", fontsize=11)
    plt.ylabel("Rate", fontsize=11)
    plt.legend(title="")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "regional_performance.png")
    plt.close()

    print(f"Regional visuals generated successfully in {VISUALS_DIR}.")


if __name__ == "__main__":
    main()
