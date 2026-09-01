#!/usr/bin/env python3
"""
Generate Summary Table for Solid Performer State Concentrations
"""

from pathlib import Path
import sys
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import VISUALS_DIR
from src.visualization import set_visual_style


def main():
    set_visual_style()

    data = {
        "State": ["Florida", "California", "Georgia", "Illinois", "Colorado", "Kentucky", "Wisconsin", "Arizona", "Oregon", "Washington", "South Carolina", "New York", "Virginia", "Pennsylvania", "Ohio"],
        "Solid Count": [294, 227, 224, 136, 113, 108, 107, 105, 103, 99, 94, 89, 89, 89, 84],
        "Test Center Density (%)": [21.2, 25.4, 21.4, 29.9, 26.3, 34.0, 29.2, 24.3, 29.7, 22.2, 29.2, 24.3, 34.6, 39.3, 28.0],
        "Prep Center Usage (%)": [42.9, 37.4, 38.4, 58.8, 61.9, 79.6, 27.1, 39.0, 48.5, 49.5, 69.1, 70.8, 38.2, 38.2, 47.6],
    }

    df_table = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis("off")
    ax.axis("tight")

    table = ax.table(
        cellText=df_table.values,
        colLabels=df_table.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)

    # Style header and rows
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#2b5c8f")
            cell.set_text_props(color="white", weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f2f4f8")

    plt.title("Top States: Solid Performer Concentration & Resource Metrics", fontsize=13, fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "solid_coverage_table.png")
    plt.close()

    print("Coverage table generated and saved to visuals/solid_coverage_table.png.")


if __name__ == "__main__":
    main()
