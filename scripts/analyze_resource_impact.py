#!/usr/bin/env python3
"""
Analysis of Preparation Resource Effectiveness on Completion Rates
"""

from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH, VISUALS_DIR
from src.metrics import calculate_resource_impact
from src.visualization import plot_resource_impact


def main():
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    res_df = calculate_resource_impact(df, min_sample=10)

    # Save visual
    plot_resource_impact(res_df, VISUALS_DIR / "resource_impact.png")

    print("Resource impact analysis complete. Visual saved to visuals/resource_impact.png.")
    print("\nRanked Resource Effectiveness:")
    print(res_df[["Resource", "Used_Completion_Rate", "Score_Diff", "Sample_Size"]].to_string(index=False))


if __name__ == "__main__":
    main()
