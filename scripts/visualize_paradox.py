#!/usr/bin/env python3
"""
Visualize Simpson's Paradox: State Prep Coverage vs. Completion Rate
"""

from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import FINAL_CLEANED_DATA_PATH, VISUALS_DIR
from src.metrics import aggregate_state_metrics
from src.visualization import plot_simpsons_paradox


def main():
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    state_agg = aggregate_state_metrics(df, min_candidates=5)

    plot_simpsons_paradox(state_agg, VISUALS_DIR / "paradox_proof.png")

    print(f"Paradox visualization generated successfully in {VISUALS_DIR / 'paradox_proof.png'}.")


if __name__ == "__main__":
    main()
