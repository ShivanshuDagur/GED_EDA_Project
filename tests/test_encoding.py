"""
Unit Tests for Qualitative-to-Quantitative Encoding and PII Protection
"""

import pandas as pd
import pytest

from src.encoding import (
    ENCODING_SCHEMAS,
    encode_qualitative_to_quantitative,
    strip_pii_columns,
)


class TestEncoding:
    def test_pii_stripping(self, sample_candidate_df):
        stripped = strip_pii_columns(sample_candidate_df)
        assert "C_ADDRESS" not in stripped.columns
        assert "DATE_OF_BIRTH" not in stripped.columns
        assert "CANDIDATE_ID" in stripped.columns

    def test_qualitative_to_quantitative_encoding(self, sample_candidate_df, sample_test_df):
        encoded_cand = encode_qualitative_to_quantitative(sample_candidate_df, drop_pii=True)

        assert encoded_cand["GENDER"].iloc[0] == 1  # MALE = 1
        assert encoded_cand["GENDER"].iloc[1] == 2  # FEMALE = 2
        assert encoded_cand["ETHNICITY"].iloc[0] == 1  # NON_HISPANIC_LATINO = 1
        assert encoded_cand["ETHNICITY"].iloc[1] == 2  # HISPANIC_LATINO = 2
        assert "C_ADDRESS" not in encoded_cand.columns

    def test_civics_filtering(self, sample_test_df):
        assert "CIVICS" in sample_test_df["EXAM_SUBJECT"].values
        encoded_test = encode_qualitative_to_quantitative(sample_test_df, filter_civics=True)
        assert len(encoded_test) == len(sample_test_df) - 1
        assert (encoded_test["EXAM_SUBJECT"] == 1).sum() >= 1  # MATH = 1
