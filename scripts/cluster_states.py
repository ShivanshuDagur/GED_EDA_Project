#!/usr/bin/env python3
"""
Unsupervised State Archetype Clustering (K-Means, K=4)
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
from src.metrics import aggregate_state_metrics
from src.clustering import cluster_states
from src.visualization import generate_state_choropleth, set_visual_style


def main():
    set_visual_style()
    df = pd.read_csv(FINAL_CLEANED_DATA_PATH)
    state_metrics = aggregate_state_metrics(df, min_candidates=10)

    state_clusters, cluster_profile = cluster_states(state_metrics, n_clusters=4)

    # 1. Cluster Profile Visual
    features = ["center_density", "prep_coverage", "enrollment_rate", "completion_rate"]
    profile_melted = cluster_profile.melt(id_vars="cluster_archetype", value_vars=features, var_name="Metric", value_name="Value")

    plt.figure(figsize=(12, 6))
    sns.barplot(data=profile_melted, x="Metric", y="Value", hue="cluster_archetype", palette="viridis")
    plt.title("State Performance Archetype Profiles", fontsize=14, fontweight="bold", pad=15)
    plt.ylabel("Average Value", fontsize=11)
    plt.xlabel("")
    plt.legend(title="Archetype", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "cluster_profiles.png")
    plt.close()

    # 2. Map of Clusters
    generate_state_choropleth(state_clusters, "cluster_archetype", "State Performance Clusters (Archetypes)", "cluster_map.png", VISUALS_DIR)

    print("State clustering complete. Visuals saved to visuals/.")
    print("\nArchetype Averages:")
    print(cluster_profile.to_string(index=False))


if __name__ == "__main__":
    main()
