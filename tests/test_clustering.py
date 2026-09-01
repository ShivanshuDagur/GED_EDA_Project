"""
Unit Tests for Persona Segmentation and State Archetype Clustering
"""

import pandas as pd
import pytest

from src.clustering import (
    assign_candidate_persona,
    generate_candidate_personas,
    cluster_states,
    compute_persona_gap_summary,
)
from src.metrics import aggregate_candidate_metrics, aggregate_state_metrics


class TestClustering:
    @pytest.mark.parametrize(
        "credential_earned,used_ged_ready,has_prep_center,expected_persona",
        [
            (1, 0, 0, "High Achievers"),
            (1, 1, 0, "Strong Performers"),
            (1, 1, 1, "Strong Performers"),
            (0, 1, 0, "Solid Performers"),
            (0, 0, 1, "Solid Performers"),
            (0, 1, 1, "Solid Performers"),
            (0, 0, 0, "Developing Learners"),
        ],
    )
    def test_assign_candidate_persona(self, credential_earned, used_ged_ready, has_prep_center, expected_persona):
        row = pd.Series({
            "credential_earned": credential_earned,
            "used_ged_ready": used_ged_ready,
            "has_prep_center": has_prep_center,
        })
        assert assign_candidate_persona(row) == expected_persona

    def test_generate_candidate_personas(self, sample_merged_cleaned_df):
        cand = aggregate_candidate_metrics(sample_merged_cleaned_df)
        cand_personas, summary = generate_candidate_personas(cand)

        assert "Persona" in cand_personas.columns
        assert len(summary) > 0
        assert "Count" in summary.columns
        assert "Share (%)" in summary.columns

    def test_compute_persona_gap_summary(self, sample_merged_cleaned_df):
        cand = aggregate_candidate_metrics(sample_merged_cleaned_df)
        cand_personas, _ = generate_candidate_personas(cand)
        gap = compute_persona_gap_summary(cand_personas)

        assert "Persona" in gap.columns
        assert "avg_score" in gap.columns
