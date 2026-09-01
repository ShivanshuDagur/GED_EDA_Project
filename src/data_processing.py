"""
Data Processing, Cleaning, Outlier Detection, and Imputation Utilities
"""

import re
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def handle_missing_values(
    candidate_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Applies the standardized GED EDA missing-value protocol to raw candidate and test tables.

    Rules:
    - Candidate table:
      * Fill categorical fields with 'UNKNOWN' (e.g. GENDER, ETHNICITY, PREP_CENTER).
      * Fill STUDIED_FOR_GED with mode.
      * Add CREDENTIAL_DATE_MISSING indicator (1 if missing, 0 otherwise).
    - Test table:
      * Fill center/location categorical fields with 'UNKNOWN'.
      * Fill attempt/pass flags with 0.
      * Retain numeric values and create *_MISSING indicator columns.

    Returns:
        Tuple of (cleaned_candidate_df, cleaned_test_df, missing_report_df)
    """
    cand = candidate_df.copy()
    test = test_df.copy()

    # 1. Candidate Table Imputations
    cand_categorical = ["GENDER", "ETHNICITY", "PREP_CENTER", "T_STATE", "C_STATE", "C_COUNTRY"]
    for col in cand_categorical:
        if col in cand.columns:
            cand[col] = cand[col].fillna("UNKNOWN").astype(str).replace({"": "UNKNOWN", "nan": "UNKNOWN"})

    if "STUDIED_FOR_GED" in cand.columns:
        mode_val = cand["STUDIED_FOR_GED"].mode().iloc[0] if not cand["STUDIED_FOR_GED"].mode().empty else 1
        cand["STUDIED_FOR_GED"] = cand["STUDIED_FOR_GED"].fillna(mode_val)

    if "CREDENTIAL_DATE" in cand.columns:
        cand["CREDENTIAL_DATE_MISSING"] = cand["CREDENTIAL_DATE"].isna().astype(int)

    # 2. Test Table Imputations
    test_categorical = ["TEST_CENTER_ID", "T_STATE", "T_COUNTRY", "LANGUAGE_CODE", "EXAM_SUBJECT"]
    for col in test_categorical:
        if col in test.columns:
            test[col] = test[col].fillna("UNKNOWN").astype(str).replace({"": "UNKNOWN", "nan": "UNKNOWN"})

    status_flags = ["FIRST_COMPLETE", "FIRST_PASSED", "MAKE_COMPLETE", "MAKE_PASSED", "PASS"]
    for col in status_flags:
        if col in test.columns:
            test[col] = test[col].fillna(0).astype(int)

    indicator_cols = ["RESULT_ID", "SCORE", "EXAM_START"]
    for col in indicator_cols:
        if col in test.columns:
            test[f"{col}_MISSING"] = test[col].isna().astype(int)

    # 3. Generate Missing Report Summary
    cand_nulls = candidate_df.isna().sum().reset_index()
    cand_nulls.columns = ["Column", "Null_Count"]
    cand_nulls["Table"] = "Candidate"
    cand_nulls["Total_Rows"] = len(candidate_df)
    cand_nulls["Null_Percentage"] = (cand_nulls["Null_Count"] / len(candidate_df)) * 100

    test_nulls = test_df.isna().sum().reset_index()
    test_nulls.columns = ["Column", "Null_Count"]
    test_nulls["Table"] = "Test_Data"
    test_nulls["Total_Rows"] = len(test_df)
    test_nulls["Null_Percentage"] = (test_nulls["Null_Count"] / len(test_df)) * 100

    missing_report = pd.concat([cand_nulls, test_nulls], ignore_index=True)

    return cand, test, missing_report


def detect_outliers_iqr(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    k: float = 3.0,
) -> pd.DataFrame:
    """
    Computes IQR-based outlier boundaries for numeric columns.

    Args:
        df: Input DataFrame
        numeric_cols: List of numeric column names (if None, all numeric columns used)
        k: IQR multiplier (default = 3.0 for conservative filtering)

    Returns:
        DataFrame summarizing [Column, Q1, Q3, IQR, Lower_Bound, Upper_Bound, Outlier_Count, Outlier_Pct]
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    summary_records = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr

        outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_count = int(outliers.sum())
        outlier_pct = (outlier_count / len(df)) * 100

        summary_records.append({
            "Column": col,
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "Lower_Bound": lower_bound,
            "Upper_Bound": upper_bound,
            "Outlier_Count": outlier_count,
            "Outlier_Pct": outlier_pct,
        })

    return pd.DataFrame(summary_records)


def remove_outliers_iqr(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    k: float = 3.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filters rows containing IQR outliers across specified numeric columns.

    Args:
        df: Input DataFrame
        numeric_cols: List of numeric columns to evaluate
        k: IQR multiplier (default 3.0)

    Returns:
        Tuple of (cleaned_df, outlier_rows_df)
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    outlier_mask = pd.Series(False, index=df.index)

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr

        col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_mask = outlier_mask | col_outliers.fillna(False)

    cleaned_df = df[~outlier_mask].copy()
    outlier_rows = df[outlier_mask].copy()

    return cleaned_df, outlier_rows


def standardize_zip_code(zip_val: object) -> Optional[str]:
    """
    Standardizes free-form US postal codes using robust regex rules:
    1. Converts value to string and strips whitespace.
    2. Strips all non-numeric characters (e.g. 'ls-12345' -> '12345').
    3. If length <= 2: discarded as invalid noise.
    4. If length is 3 or 4 digits: padded with leading zeros (e.g. '530' -> '00530').
    5. Truncates to standard 5-digit US ZIP format.

    Args:
        zip_val: Raw input ZIP code value (string, int, float, or NaN)

    Returns:
        Clean 5-digit string or None
    """
    if pd.isna(zip_val):
        return None

    raw_str = str(zip_val).strip()
    if raw_str.upper() in ["NULL", "NA", "NONE", "UNKNOWN", "NO STREET ADDRESS AVAILABLE"]:
        return None

    # Strip non-digits
    digits = re.sub(r"\D", "", raw_str)

    if len(digits) <= 2:
        return None

    if len(digits) in [3, 4]:
        digits = digits.zfill(5)

    return digits[:5]


def clean_and_parse_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes data formats, string IDs, dates, and ZIP codes across the merged dataset.
    """
    cleaned = df.copy()

    # 1. Standardize string IDs
    id_cols = ["CANDIDATE_ID", "RESULT_ID", "TEST_CENTER_ID"]
    for col in id_cols:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype(str).str.replace(r"\.0$", "", regex=True)
            cleaned[col] = cleaned[col].replace({"nan": None, "UNKNOWN": None})

    # 2. Date parsing
    date_cols = ["ACCOUNT_SETUP_COMPLETE_DATE", "CREDENTIAL_DATE", "EXAM_START"]
    for col in date_cols:
        if col in cleaned.columns:
            cleaned[col] = pd.to_datetime(cleaned[col], errors="coerce")

    # 3. ZIP Code standardizations
    zip_cols = ["ZIP", "T_POSTAL_CODE"]
    for col in zip_cols:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].apply(standardize_zip_code)

    return cleaned
