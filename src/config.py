"""
Configuration and Path Management for GED Analytics Project
"""

import os
from pathlib import Path
from typing import Dict, List

# -----------------------------------------------------------------------------
# Base Directory Paths (Resolved dynamically from package location)
# -----------------------------------------------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw_sample"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VISUALS_DIR = PROJECT_ROOT / "visuals"
REPORTS_DIR = PROJECT_ROOT / "reports"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SQL_DIR = PROJECT_ROOT / "sql"

# Default file paths
RAW_CANDIDATE_PATH = RAW_DATA_DIR / "candidate_table_raw_sample.xlsx"
RAW_TEST_PATH = RAW_DATA_DIR / "test_data_table_raw_sample.xlsx"
FINAL_CLEANED_DATA_PATH = PROCESSED_DATA_DIR / "5_test_candidate_cleaned_final.csv"
CANDIDATE_AGG_PATH = PROCESSED_DATA_DIR / "6.candidates_cleaned.xlsx"

# Ensure essential output directories exist
for path in [VISUALS_DIR, REPORTS_DIR, PROCESSED_DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Geographic Constants (US Census Bureau Regions)
# -----------------------------------------------------------------------------
CENSUS_REGIONS: Dict[str, List[str]] = {
    "Northeast": ["CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
    "Midwest": ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"],
    "South": ["DE", "DC", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
    "West": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
}

# Reverse mapping: State abbreviation -> Census Region
STATE_TO_REGION: Dict[str, str] = {
    state: region
    for region, states in CENSUS_REGIONS.items()
    for state in states
}

VALID_US_STATES: List[str] = [state for states in CENSUS_REGIONS.values() for state in states]

# -----------------------------------------------------------------------------
# Exam and Academic Thresholds
# -----------------------------------------------------------------------------
PASS_SCORE_THRESHOLD: float = 145.0
COLLEGE_READY_SCORE_THRESHOLD: float = 165.0
HONORS_SCORE_THRESHOLD: float = 175.0

EXAM_SUBJECTS: Dict[str, int] = {
    "MATHEMATICS": 1,
    "SCIENCE": 2,
    "REASONING": 3,
    "SOCIAL_STUDIES": 4,
}

CORE_SUBJECT_NAMES: List[str] = ["MATHEMATICS", "SCIENCE", "REASONING", "SOCIAL_STUDIES"]

# -----------------------------------------------------------------------------
# Persona Names and Archetypes
# -----------------------------------------------------------------------------
PERSONA_NAMES: List[str] = [
    "High Achievers",
    "Strong Performers",
    "Solid Performers",
    "Developing Learners",
]

# -----------------------------------------------------------------------------
# Visual Styling Constants
# -----------------------------------------------------------------------------
COLOR_PALETTE_PRIMARY = ["#2b5c8f", "#3e8e7e", "#e27d60", "#c38d9e", "#41b3a3"]
PERSONA_COLORS = {
    "High Achievers": "#2b5c8f",       # Deep Blue
    "Strong Performers": "#3e8e7e",   # Teal/Green
    "Solid Performers": "#e27d60",    # Coral/Orange
    "Developing Learners": "#c38d9e", # Muted Crimson
}
