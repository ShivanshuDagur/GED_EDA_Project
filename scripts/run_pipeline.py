#!/usr/bin/env python3
"""
Master Execution Script for GED Analytics Pipeline
=================================================
Usage:
    python scripts/run_pipeline.py [--data-path PATH] [--output-dir PATH]
"""

import argparse
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_full_analysis
from src.config import FINAL_CLEANED_DATA_PATH, VISUALS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Run end-to-end GED EDA & Econometric Disparity Pipeline"
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=FINAL_CLEANED_DATA_PATH,
        help="Path to cleaned input dataset (default: data/processed/5_test_candidate_cleaned_final.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=VISUALS_DIR,
        help="Directory to save generated visual figures and maps (default: visuals/)",
    )

    args = parser.parse_args()

    try:
        run_full_analysis(input_path=args.data_path, output_dir=args.output_dir, verbose=True)
    except Exception as e:
        print(f"\n[ERROR] Pipeline execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
