#!/usr/bin/env python3
"""
Generate State and Regional Choropleth Maps for Supply & Outcome Metrics
"""

from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH, VISUALS_DIR
from src.metrics import aggregate_state_metrics, aggregate_regional_metrics
from src.visualization import generate_state_choropleth


def main():
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    state_metrics = aggregate_state_metrics(df, min_candidates=0)
    region_avg = aggregate_regional_metrics(state_metrics)

    metrics = [
        ("center_density", "State-Level Testing Center Density", "map_state_center_density.png"),
        ("prep_coverage", "State-Level Prep Center Coverage", "map_state_prep_coverage.png"),
        ("enrollment_rate", "State-Level Exam Enrollment Rate", "map_state_enrollment_rate.png"),
        ("completion_rate", "State-Level GED Completion Rate", "map_state_completion_rate.png"),
    ]

    print("Generating State Choropleth Maps...")
    for metric_col, title, filename in metrics:
        generate_state_choropleth(state_metrics, metric_col, title, filename, VISUALS_DIR)

    # Regional Maps (merge regional average to each state)
    regional_map_df = state_metrics[["C_STATE", "census_region"]].copy()
    regional_map_df = regional_map_df.merge(region_avg, on="census_region", suffixes=("", "_avg"))

    regional_metrics = [
        ("center_density", "Regional Center Density (Avg)", "map_region_center_density.png"),
        ("prep_coverage", "Regional Prep Coverage (Avg)", "map_region_prep_coverage.png"),
        ("enrollment_rate", "Regional Enrollment Rate (Avg)", "map_region_enrollment_rate.png"),
        ("completion_rate", "Regional Completion Rate (Avg)", "map_region_completion_rate.png"),
    ]

    print("Generating Regional Choropleth Maps...")
    for metric_col, title, filename in regional_metrics:
        generate_state_choropleth(regional_map_df, metric_col, title, filename, VISUALS_DIR)

    print(f"Maps generation complete. Saved to {VISUALS_DIR}.")


if __name__ == "__main__":
    main()
