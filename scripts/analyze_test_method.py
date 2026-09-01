#!/usr/bin/env python3
"""
Analysis of Testing Delivery Method: Online (OnVUE) vs Physical Test Centers
"""

from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH, VISUALS_DIR
from src.metrics import aggregate_candidate_metrics, calculate_test_method_metrics
from src.visualization import plot_test_method_comparison


def main():
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    cand = aggregate_candidate_metrics(df)
    overall, regional = calculate_test_method_metrics(cand)

    # Regional adoption percentage
    regional_counts = cand.dropna(subset=["census_region"]).groupby(["census_region", "test_method"]).size().unstack(fill_value=0)
    regional_pct = regional_counts.div(regional_counts.sum(axis=1), axis=0).reset_index().melt(
        id_vars="census_region", var_name="Method", value_name="Share"
    )

    plot_test_method_comparison(overall, regional_pct, VISUALS_DIR)

    print("Test method analysis complete. Visuals saved to visuals/.")
    print("\nOverall Method Performance:")
    print(overall.to_string(index=False))


if __name__ == "__main__":
    main()
