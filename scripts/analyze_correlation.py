#!/usr/bin/env python3
"""
Correlation Analysis: State & Regional Resource Supply vs. Completion Rates
"""

from pathlib import Path
import sys
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH
from src.metrics import aggregate_state_metrics, aggregate_regional_metrics
from src.modeling import calculate_simpsons_paradox_metrics


def main():
    if not FINAL_CLEANED_DATA_PATH.exists():
        print(f"[ERROR] Cleaned dataset not found at {FINAL_CLEANED_DATA_PATH}")
        sys.exit(1)

    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    state_agg = aggregate_state_metrics(df, min_candidates=10)
    reg_agg = aggregate_regional_metrics(state_agg)
    paradox = calculate_simpsons_paradox_metrics(state_agg)

    print("=" * 60)
    print("RESOURCE IMPACT CORRELATION ANALYSIS")
    print("=" * 60)
    print(f"State-Level Correlation (n ≥ 10):  {paradox['state_correlation']:.3f}")
    print(f"Regional-Level Correlation:         {paradox['regional_correlation']:.3f}")

    print("\nRegional Averages:")
    print("-" * 60)
    for _, row in reg_agg.iterrows():
        print(f"{row['census_region']:12s} | Prep Coverage: {row['prep_coverage']:.1%} | Completion: {row['completion_rate']:.1%}")

    print("\nTop 5 States by Prep Coverage:")
    print(state_agg.sort_values("prep_coverage", ascending=False).head(5)[["C_STATE", "prep_coverage", "completion_rate"]].to_string(index=False))

    print("\nTop 5 States by Completion Rate:")
    print(state_agg.sort_values("completion_rate", ascending=False).head(5)[["C_STATE", "prep_coverage", "completion_rate"]].to_string(index=False))


if __name__ == "__main__":
    main()
