"""
Pytest Fixtures with Synthetic Candidate and Exam Test Data
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_candidate_df() -> pd.DataFrame:
    """Returns a synthetic raw candidate DataFrame."""
    return pd.DataFrame({
        "CANDIDATE_ID": [101, 102, 103, 104, 105],
        "GENDER": ["MALE", "FEMALE", None, "MALE", "FEMALE"],
        "ETHNICITY": ["NON_HISPANIC_LATINO", "HISPANIC_LATINO", "UNKNOWN", None, "NON_HISPANIC_LATINO"],
        "PREP_CENTER": ["PC_01", None, "UNKNOWN", "PC_02", None],
        "STUDIED_FOR_GED": [1.0, 1.0, None, 0.0, 1.0],
        "CREDENTIAL_DATE": [pd.Timestamp("2023-05-15"), None, None, pd.Timestamp("2023-08-20"), None],
        "C_STATE": ["FL", "CA", "TX", "NY", "IL"],
        "C_ADDRESS": ["123 Main St", "456 Oak Ave", "789 Pine Rd", "101 Elm St", "202 Maple Dr"],
        "DATE_OF_BIRTH": ["1995-04-12", "1988-11-23", "2001-02-14", "1992-09-30", "2000-07-07"],
        "LAST_YEAR_INCOME": ["UNDER_5000", "R_20000_29999", "R_50000_74999", "UNDER_5000", "R_10000_19999"],
        "HIGHEST_GRADE_COMPLETED": ["C_11", "C_12", "C_10", "C_9", "C_11"],
        "ZIP": ["ls-12345", "530", "90210", "12", None],
    })


@pytest.fixture
def sample_test_df() -> pd.DataFrame:
    """Returns a synthetic raw exam attempts test DataFrame."""
    return pd.DataFrame({
        "RESULT_ID": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"],
        "CANDIDATE_ID": [101, 101, 102, 102, 103, 104, 104, 105],
        "EXAM_SUBJECT": ["MATH", "SCIENCE", "MATH", "CIVICS", "MATH", "MATH", "SCIENCE", "REASONING"],
        "SCORE": [155.0, 160.0, 142.0, 150.0, 148.0, 170.0, 168.0, 138.0],
        "PASS": [1, 1, 0, 1, 1, 1, 1, 0],
        "GED_READY": [0, 0, 1, 0, 1, 1, 1, 0],
        "ON_VUE": [0, 0, 1, 1, 0, 1, 1, 0],
        "TEST_CENTER_ID": ["TC_01", "TC_01", "TC_02", "TC_02", "TC_03", "TC_04", "TC_04", "TC_05"],
        "T_STATE": ["FL", "FL", "CA", "CA", "TX", "NY", "NY", "IL"],
        "EXAM_START": [pd.Timestamp("2023-01-10"), pd.Timestamp("2023-02-10"), None, None, None, None, None, None],
    })


@pytest.fixture
def sample_merged_cleaned_df() -> pd.DataFrame:
    """Returns a pre-processed merged candidate and test DataFrame."""
    return pd.DataFrame({
        "CANDIDATE_ID": ["C1", "C1", "C2", "C2", "C3", "C4", "C5"],
        "EXAM_SUBJECT": [1, 2, 1, 3, 1, 1, 2],
        "SCORE": [155.0, 160.0, 150.0, 152.0, 142.0, 138.0, 146.0],
        "SCORE_MISSING": [0, 0, 0, 0, 0, 0, 0],
        "CREDENTIAL_DATE": ["2023-05-15", "2023-05-15", "2023-06-20", "2023-06-20", None, None, None],
        "ENROLLMENT_STATUS": [4, 4, 4, 4, 3, 3, 3],
        "GED_READY": [0, 0, 1, 1, 1, 0, 1],
        "PREP_CENTER": [None, None, "PC1", "PC1", "PC2", None, "PC3"],
        "ON_VUE": [0, 0, 1, 1, 0, 0, 0],
        "C_STATE": ["FL", "FL", "CA", "CA", "TX", "NY", "IL"],
        "T_STATE": ["FL", "FL", "CA", "CA", "TX", "NY", "IL"],
        "TEST_CENTER_ID": ["TC1", "TC1", "TC2", "TC2", "TC3", "TC4", "TC5"],
        "GENDER": [1, 1, 2, 2, 1, 2, 1],
        "ETHNICITY": [1, 1, 2, 2, 1, 1, 2],
        "BIRTH_YEAR": [1995, 1995, 1988, 1988, 2000, 1992, 1998],
    })
