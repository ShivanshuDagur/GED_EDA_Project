#!/usr/bin/env python3
"""
Generate State-Level Prep Coverage Summary Markdown Table
"""

from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH
from src.metrics import aggregate_state_metrics


def main():
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    state_counts = aggregate_state_metrics(df, min_candidates=0)

    display_df = state_counts[["C_STATE", "n_candidates", "n_prep_users", "prep_coverage", "completion_rate"]].copy()
    display_df["prep_coverage"] = display_df["prep_coverage"].apply(lambda x: f"{x:.1%}")
    display_df["completion_rate"] = display_df["completion_rate"].apply(lambda x: f"{x:.1%}")
    display_df.columns = ["State", "Total Candidates", "Prep Center Users", "Prep Coverage", "Completion Rate"]

    markdown_table = display_df.to_markdown(index=False)

    print("State-Level Prep Coverage Summary:")
    print(markdown_table)


if __name__ == "__main__":
    main()
