#!/usr/bin/env python3
"""
Deep-Dive Analysis: Prep Center Effectiveness and Selection Bias
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
from src.metrics import aggregate_candidate_metrics
from src.visualization import set_visual_style


def main():
    set_visual_style()
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    cand = aggregate_candidate_metrics(df)

    # 1. Overall Comparison
    overall = cand.groupby("has_prep_center")["credential_earned"].mean().reset_index()
    overall["Label"] = overall["has_prep_center"].map({1: "Used Prep Center", 0: "Did NOT Use"})

    # 2. Regional Comparison
    regional = (
        cand.dropna(subset=["census_region"])
        .groupby(["census_region", "has_prep_center"])["credential_earned"]
        .mean()
        .reset_index()
    )
    regional["User Group"] = regional["has_prep_center"].map({1: "Used Prep Center", 0: "Did NOT Use"})

    # Visual 1: Overall Impact
    plt.figure(figsize=(8, 5))
    bars = sns.barplot(data=overall, x="Label", y="credential_earned", palette="Blues_d")
    plt.title("Overall Impact: Test Prep Center Users vs. Non-Users", fontsize=13, fontweight="bold")
    plt.ylabel("Completion Rate", fontsize=11)
    plt.xlabel("")
    for p in bars.patches:
        plt.annotate(f"{p.get_height():.1%}", (p.get_x() + p.get_width() / 2, p.get_height() + 0.01), ha="center", fontweight="bold")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "prep_center_overall.png")
    plt.close()

    # Visual 2: Regional Impact
    plt.figure(figsize=(10, 6))
    sns.barplot(data=regional, x="census_region", y="credential_earned", hue="User Group", palette="muted")
    plt.title("Regional Effectiveness of Test Prep Centers", fontsize=13, fontweight="bold")
    plt.ylabel("Completion Rate", fontsize=11)
    plt.xlabel("Census Region", fontsize=11)
    plt.legend(title="Study Group")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "prep_center_regional.png")
    plt.close()

    print("Prep Center Deep-Dive complete. Visuals saved to visuals/.")
    print("\nGlobal Comparison:")
    print(overall[["Label", "credential_earned"]].to_string(index=False))


if __name__ == "__main__":
    main()
