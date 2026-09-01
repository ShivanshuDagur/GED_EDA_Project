#!/usr/bin/env python3
"""
Candidate Persona Generation, Profiling, and Visualizations
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
from src.clustering import generate_candidate_personas
from src.visualization import (
    plot_persona_profiles,
    plot_persona_distribution,
    plot_persona_gap_analysis,
    generate_state_choropleth,
    set_visual_style,
)


def main():
    set_visual_style()
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    cand = aggregate_candidate_metrics(df)

    cand_personas, persona_summary = generate_candidate_personas(cand)

    # 1. Performance Profile
    plot_persona_profiles(persona_summary, VISUALS_DIR / "persona_profiles.png")

    # 2. National Distribution (Donut Chart)
    plot_persona_distribution(persona_summary, VISUALS_DIR / "persona_distribution.png")

    # 3. Gap Analysis (Solid Performers vs. Developing Learners)
    plot_persona_gap_analysis(cand_personas, VISUALS_DIR / "persona_gap_analysis.png")

    # 4. Demographic Profiles
    if "age" in cand_personas.columns:
        plt.figure(figsize=(10, 5))
        sns.boxplot(data=cand_personas.dropna(subset=["age"]), x="Persona", y="age", palette="Set2")
        plt.title("Candidate Age Distribution by Persona", fontsize=14, fontweight="bold", pad=15)
        plt.ylabel("Age (Years)", fontsize=11)
        plt.xlabel("")
        plt.tight_layout()
        plt.savefig(VISUALS_DIR / "persona_demographics.png")
        plt.close()

    # 5. Solid Performer Concentration by State Map
    solid_counts = (
        cand_personas[cand_personas["Persona"] == "Solid Performers"]
        .groupby("C_STATE")
        .size()
        .reset_index(name="Solid_Count")
    )
    generate_state_choropleth(
        solid_counts,
        "Solid_Count",
        "Solid Performer Concentration by State (High Effort / Low Credential)",
        "solid_persona_map.png",
        VISUALS_DIR,
    )

    # 6. Top Resources for Solid Performers
    resource_cols = [c for c in df.columns if c.startswith("STUDY_HELPFUL_") or c == "STUDY_LOCATION_TEST_PREPARATION_CENTER"]
    if resource_cols:
        g = df.groupby("CANDIDATE_ID")
        for col in resource_cols:
            cand_personas[col] = g[col].max().values

        solid_data = cand_personas[cand_personas["Persona"] == "Solid Performers"]
        solid_resources = solid_data[resource_cols].mean().sort_values(ascending=False).reset_index()
        solid_resources.columns = ["Resource", "Usage Rate"]
        solid_resources["Resource"] = (
            solid_resources["Resource"]
            .str.replace("STUDY_HELPFUL_", "")
            .str.replace("STUDY_LOCATION_", "")
            .str.replace("_", " ")
            .str.title()
        )

        plt.figure(figsize=(10, 6))
        sns.barplot(data=solid_resources, x="Usage Rate", y="Resource", palette="mako")
        plt.title("Prep Tool Usage: Solid Performers", fontsize=14, fontweight="bold", pad=15)
        plt.xlabel("Usage Rate (0–1)", fontsize=11)
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(VISUALS_DIR / "solid_resources.png")
        plt.close()

    print("Candidate persona generation complete. Visuals saved to visuals/.")
    print("\nPersona Summary Table:")
    print(persona_summary.to_string(index=False))


if __name__ == "__main__":
    main()
