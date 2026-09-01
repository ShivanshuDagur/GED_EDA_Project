"""
Candidate Persona Segmentation and State Archetype Clustering
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .config import PERSONA_NAMES, PERSONA_COLORS


def assign_candidate_persona(row: pd.Series) -> str:
    """
    Categorizes a candidate into one of 4 empirically derived behavioral personas:
    - High Achievers: Credentialed candidates with low support tool dependency (direct passes).
    - Strong Performers: Credentialed candidates with heavy support usage (GED Ready / prep tools).
    - Solid Performers: Non-credentialed candidates with high support usage (effort-outcome gap).
    - Developing Learners: Non-credentialed candidates with low support usage (most at-risk).
    """
    credentialed = row.get("credential_earned", 0) == 1
    used_ready = row.get("used_ged_ready", 0) == 1
    has_prep = row.get("has_prep_center", 0) == 1

    if credentialed:
        if not used_ready:
            return "High Achievers"
        else:
            return "Strong Performers"
    else:
        if used_ready or has_prep:
            return "Solid Performers"
        else:
            return "Developing Learners"


def generate_candidate_personas(cand_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Assigns candidate personas and calculates descriptive profiling metrics.

    Args:
        cand_df: Candidate-level feature matrix

    Returns:
        Tuple of (cand_df_with_persona, persona_summary_df)
    """
    cand = cand_df.copy()
    cand["Persona"] = cand.apply(assign_candidate_persona, axis=1)

    # Compute profiling aggregations
    agg_dict = {
        "CANDIDATE_ID": "count",
        "avg_score": "mean",
        "credential_earned": "mean",
        "pass_rate": "mean",
        "college_ready_rate": "mean",
        "avg_retakes": "mean",
        "used_ged_ready": "mean",
        "has_prep_center": "mean",
        "pct_online": "mean",
    }

    if "age" in cand.columns:
        agg_dict["age"] = "mean"

    summary = cand.groupby("Persona").agg(agg_dict).reset_index()
    summary = summary.rename(columns={"CANDIDATE_ID": "Count"})

    total_candidates = len(cand)
    summary["Share (%)"] = (summary["Count"] / total_candidates) * 100

    # Ensure consistent ordering
    summary["Persona_Order"] = summary["Persona"].map({name: i for i, name in enumerate(PERSONA_NAMES)})
    summary = summary.sort_values("Persona_Order").drop(columns=["Persona_Order"]).reset_index(drop=True)

    return cand, summary


def cluster_states(
    state_metrics_df: pd.DataFrame,
    n_clusters: int = 4,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs K-Means clustering on state-level infrastructure and outcome metrics.

    Features:
    - center_density (testing centers per candidate)
    - prep_coverage (share of candidates using prep centers)
    - enrollment_rate (exam attempt rate)
    - completion_rate (credential achievement rate)

    Returns:
        Tuple of (state_data_with_clusters, cluster_profile_summary)
    """
    state_data = state_metrics_df.copy()
    features = ["center_density", "prep_coverage", "enrollment_rate", "completion_rate"]

    # Filter complete feature rows
    valid_mask = state_data[features].notna().all(axis=1)
    cluster_df = state_data[valid_mask].copy()

    X = cluster_df[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_df["cluster_id"] = kmeans.fit_predict(X_scaled)

    # Map cluster IDs to performance ranks
    rank_map = (
        cluster_df.groupby("cluster_id")["completion_rate"]
        .mean()
        .sort_values(ascending=False)
        .index
    )

    archetype_labels = [
        "High Achievers (High Density / High Completion)",
        "Strong Performers (Balanced Resources)",
        "Solid Performers (High Prep / Moderate Completion)",
        "Developing Learners (Resource Constrained)",
    ]

    cluster_label_map = {cluster_id: archetype_labels[i] for i, cluster_id in enumerate(rank_map)}
    cluster_df["cluster_archetype"] = cluster_df["cluster_id"].map(cluster_label_map)

    # Compute standardized profile
    cluster_profile = cluster_df.groupby("cluster_archetype")[features].mean().reset_index()

    return cluster_df, cluster_profile


def compute_persona_gap_summary(cand_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the gap analysis between 'Solid Performers' and 'Developing Learners'.
    """
    gap_data = cand_df[cand_df["Persona"].isin(["Solid Performers", "Developing Learners"])].copy()

    gap_summary = gap_data.groupby("Persona").agg(
        candidate_count=("CANDIDATE_ID", "count"),
        avg_score=("avg_score", "mean"),
        avg_subjects_passed=("n_passed_exams", "mean"),
        used_ged_ready=("used_ged_ready", "mean"),
        has_prep_center=("has_prep_center", "mean"),
        avg_retakes=("avg_retakes", "mean"),
    ).reset_index()

    return gap_summary
