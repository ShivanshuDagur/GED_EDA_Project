"""
Qualitative-to-Quantitative Feature Encoding and Privacy Utilities
"""

from typing import Dict, List, Optional
import pandas as pd

# -----------------------------------------------------------------------------
# Encoding Schemas (Standardized Qualitative -> Numeric Mappings)
# -----------------------------------------------------------------------------
ENCODING_SCHEMAS: Dict[str, Dict[str, int]] = {
    "LANGUAGE_CODE": {
        "ENU": 1,
        "ENGLISH": 1,
        "ESP": 2,
        "SPANISH": 2,
        "UNKNOWN": 0,
    },
    "EXAM_SUBJECT": {
        "MATHEMATICS": 1,
        "MATH": 1,
        "SCIENCE": 2,
        "REASONING": 3,
        "SOCIAL_STUDIES": 4,
        "UNKNOWN": 0,
    },
    "GENDER": {
        "MALE": 1,
        "FEMALE": 2,
        "NONBINARY": 3,
        "DECLINE": 4,
        "UNKNOWN": 0,
    },
    "ETHNICITY": {
        "NON_HISPANIC_LATINO": 1,
        "HISPANIC_LATINO": 2,
        "DECLINE": 3,
        "UNKNOWN": 0,
    },
    "ENROLLMENT_STATUS": {
        "INTERESTED": 1,
        "CONTACTED": 2,
        "ENROLLED": 3,
        "CREDENTIALED": 4,
        "DISMISSED": 5,
        "UNKNOWN": 0,
    },
    "HIGHEST_GRADE_COMPLETED": {
        "C_PRE_5": 1,
        "C_6_8": 2,
        "C_9": 3,
        "C_10": 4,
        "C_11": 5,
        "C_12": 6,
        "DONT_REMEMBER": 7,
        "OTHER": 8,
        "NEVER": 9,
        "UNKNOWN": 0,
    },
    "LAST_YEAR_INCOME": {
        "UNDER_5000": 1,
        "R_5000_9999": 2,
        "R_10000_19999": 3,
        "R_20000_29999": 4,
        "R_30000_39999": 5,
        "R_40000_49999": 6,
        "R_50000_74999": 7,
        "R_75000_ABOVE": 8,
        "UNKNOWN": 0,
    },
    "TESTING_REASON": {
        "WORK_RELATED": 1,
        "EDUCATIONAL_GAIN": 2,
        "PERSONAL_GAIN": 3,
        "ENTRANCE_TO_MILITARY": 4,
        "SPECIAL_REQUIREMENT": 5,
        "UNKNOWN": 0,
    },
    "SCHOOL_INCOMPLETE_REASON": {
        "ACADEMIC": 1,
        "PERSONAL": 2,
        "PERSONAL_AND_ACADEMIC": 3,
        "NEITHER_PERSONAL_NOR_ACADEMIC": 4,
        "HOME_SCHOOLED": 5,
        "HIGH_SCHOOL_DIPLOMA_FROM_ANOTHER_COUNTRY": 6,
        "UNKNOWN": 0,
    },
}

PII_COLUMNS: List[str] = ["C_ADDRESS", "DATE_OF_BIRTH", "FIRST_NAME", "LAST_NAME", "SSN", "PHONE"]


def strip_pii_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops personally identifiable information (PII) to ensure data privacy compliance.
    """
    cols_to_drop = [col for col in PII_COLUMNS if col in df.columns]
    return df.drop(columns=cols_to_drop)


def encode_qualitative_to_quantitative(
    df: pd.DataFrame,
    filter_civics: bool = True,
    drop_pii: bool = True,
) -> pd.DataFrame:
    """
    Transforms categorical columns into numeric encodings based on the predefined schema.

    Args:
        df: Input DataFrame
        filter_civics: Whether to remove rows where EXAM_SUBJECT == 'CIVICS'
        drop_pii: Whether to drop PII columns (C_ADDRESS, DATE_OF_BIRTH)

    Returns:
        Transformed DataFrame with encoded numeric values
    """
    encoded_df = df.copy()

    # 1. Filter out CIVICS subject records if requested
    if filter_civics and "EXAM_SUBJECT" in encoded_df.columns:
        encoded_df = encoded_df[encoded_df["EXAM_SUBJECT"].astype(str).str.upper() != "CIVICS"].copy()

    # 2. Drop PII
    if drop_pii:
        encoded_df = strip_pii_columns(encoded_df)

    # 3. Apply Schema Transformations
    for col, mapping in ENCODING_SCHEMAS.items():
        if col in encoded_df.columns:
            # Map string representation to numeric code
            str_series = encoded_df[col].astype(str).str.upper().str.strip()
            encoded_df[col] = str_series.map(mapping).fillna(0).astype(int)

    return encoded_df
