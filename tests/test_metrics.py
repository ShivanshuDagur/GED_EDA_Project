"""
Unit Tests for Candidate KPIs, State Metrics, and Regional Aggregations
"""

import pandas as pd
import pytest

from src.metrics import (
    aggregate_candidate_metrics,
    calculate_funnel_kpis,
    aggregate_state_metrics,
    aggregate_regional_metrics,
    calculate_test_method_metrics,
)


class TestMetrics:
    def test_aggregate_candidate_metrics(self, sample_merged_cleaned_df):
        cand = aggregate_candidate_metrics(sample_merged_cleaned_df)

        assert len(cand) == 5  # 5 distinct candidates: C1, C2, C3, C4, C5
        assert "avg_score" in cand.columns
        assert "credential_earned" in cand.columns
        assert "pass_rate" in cand.columns
        assert "test_method" in cand.columns

        # Check candidate C1
        c1 = cand[cand["CANDIDATE_ID"] == "C1"].iloc[0]
        assert c1["credential_earned"] == 1
        assert c1["avg_score"] == 157.5
        assert c1["pass_rate"] == 1.0

    def test_calculate_funnel_kpis(self, sample_merged_cleaned_df):
        cand = aggregate_candidate_metrics(sample_merged_cleaned_df)
        kpis = calculate_funnel_kpis(cand)

        assert len(kpis) == 7
        assert "Total Candidates (Enrolled)" in kpis["Funnel Stage"].values
        assert "Credential Earned" in kpis["Funnel Stage"].values

    def test_aggregate_state_metrics(self, sample_merged_cleaned_df):
        state_metrics = aggregate_state_metrics(sample_merged_cleaned_df, min_candidates=0)

        assert "C_STATE" in state_metrics.columns
        assert "center_density" in state_metrics.columns
        assert "prep_coverage" in state_metrics.columns
        assert "completion_rate" in state_metrics.columns
        assert len(state_metrics) > 0

    def test_aggregate_regional_metrics(self, sample_merged_cleaned_df):
        state_metrics = aggregate_state_metrics(sample_merged_cleaned_df, min_candidates=0)
        regional = aggregate_regional_metrics(state_metrics)

        assert "census_region" in regional.columns
        assert "completion_rate" in regional.columns
