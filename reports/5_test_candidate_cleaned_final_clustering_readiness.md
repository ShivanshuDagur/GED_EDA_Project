# Clustering readiness review: `5_test_candidate_cleaned_final.csv`

## Dataset profile
- Rows: **25,657**
- Columns: **60**
- Exact duplicate rows: **0**
- Duplicate `CANDIDATE_ATTEMPT_ID`: **0**

## Key quality checks
- Missingness is still substantial in some fields:
  - `CREDENTIAL_DATE`: **50.65%** missing
  - `RESULT_ID`, `EXAM_START`, `SCORE`: **2.49%** missing each
  - `T_POSTAL_CODE`: **2.00%** missing
- High-cardinality text columns remain (not directly cluster-ready):
  - `CANDIDATE_ATTEMPT_ID` (25,657 unique)
  - `EXAM_START` (24,326 unique timestamps)
  - `T_NAME` (1,314), `T_ADDRESS` (1,288), `PREP_CENTER` (939), etc.
- Redundant indicators exist:
  - Perfectly correlated missing flags: `RESULT_ID_MISSING`, `SCORE_MISSING`, `EXAM_START_MISSING` (|r| = 1.0)
- Very sparse binary features exist:
  - `STUDY_HELPFUL_TV_STUDY_PROGRAM` mean = **0.0043**
  - `HAWAIIAN_OR_PACIFIC` mean = **0.0084**

## Verdict
**Not fully ready for clustering yet** (if used as-is).

Main blockers:
1. Raw identifiers and free-text/high-cardinality columns are still present.
2. Date/time columns are still strings and need feature engineering (or exclusion).
3. Missingness in key columns needs a final strategy (impute/drop/keep flag).
4. Perfectly redundant missing-indicator columns should be reduced to one flag.
5. Feature scaling/normalization is still required before distance-based clustering.

## Minimum prep before clustering
1. Drop pure identifiers (`CANDIDATE_ATTEMPT_ID`, likely `CANDIDATE_ID`, `RESULT_ID`).
2. Convert datetime columns (`EXAM_START`, `ACCOUNT_SETUP_COMPLETE_DATE`, `CREDENTIAL_DATE`) into engineered numeric features (e.g., year/month/lag) or remove.
3. Handle remaining nulls consistently.
4. Remove one or two of the perfectly duplicated missingness flags.
5. Encode categorical variables appropriately (one-hot/frequency/target-safe encoding depending on method).
6. Scale numeric features (standardization or robust scaling).
7. Optionally remove very sparse binary features if they add noise.

## Practical note
- If you plan to use **k-prototypes**, mixed numeric/categorical data can be used directly after removing IDs, handling missing values, and cleaning date fields.
- If you plan to use **k-means/hierarchical (Euclidean)**, you must fully numeric-encode plus scale first.
