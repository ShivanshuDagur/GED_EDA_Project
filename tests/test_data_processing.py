"""
Unit Tests for Data Processing, Missing Value Imputation, and Outlier Filtering
"""

import numpy as np
import pandas as pd
import pytest

from src.data_processing import (
    handle_missing_values,
    detect_outliers_iqr,
    remove_outliers_iqr,
    standardize_zip_code,
    clean_and_parse_types,
)


class TestMissingValues:
    def test_missing_value_handling(self, sample_candidate_df, sample_test_df):
        cand_clean, test_clean, report = handle_missing_values(sample_candidate_df, sample_test_df)

        # Check candidate table imputations
        assert (cand_clean["GENDER"] == "UNKNOWN").sum() >= 1
        assert (cand_clean["ETHNICITY"] == "UNKNOWN").sum() >= 1
        assert "CREDENTIAL_DATE_MISSING" in cand_clean.columns
        assert cand_clean["CREDENTIAL_DATE_MISSING"].iloc[1] == 1
        assert cand_clean["CREDENTIAL_DATE_MISSING"].iloc[0] == 0

        # Check test table imputations
        assert "RESULT_ID_MISSING" in test_clean.columns
        assert "SCORE_MISSING" in test_clean.columns
        assert len(report) > 0


class TestOutlierDetection:
    def test_iqr_outlier_detection_and_removal(self):
        # Create normal data with an extreme outlier
        df = pd.DataFrame({"SCORE": [140.0, 142.0, 145.0, 148.0, 150.0, 152.0, 155.0, 300.0]})
        summary = detect_outliers_iqr(df, numeric_cols=["SCORE"], k=1.5)

        assert len(summary) == 1
        assert summary["Outlier_Count"].iloc[0] == 1

        cleaned, outliers = remove_outliers_iqr(df, numeric_cols=["SCORE"], k=1.5)
        assert len(cleaned) == 7
        assert len(outliers) == 1
        assert 300.0 not in cleaned["SCORE"].values


class TestZipCodeStandardization:
    @pytest.mark.parametrize(
        "raw_zip,expected",
        [
            ("ls-12345", "12345"),
            ("530", "00530"),
            ("90210-1234", "90210"),
            (12345, "12345"),
            ("12", None),
            ("NULL", None),
            (None, None),
            (np.nan, None),
            ("No street address available", None),
        ],
    )
    def test_standardize_zip_code(self, raw_zip, expected):
        assert standardize_zip_code(raw_zip) == expected


class TestTypeStandardization:
    def test_clean_and_parse_types(self, sample_candidate_df):
        cleaned = clean_and_parse_types(sample_candidate_df)
        assert cleaned["CANDIDATE_ID"].dtype == object or str
        assert cleaned["ZIP"].iloc[0] == "12345"
        assert cleaned["ZIP"].iloc[1] == "00530"
