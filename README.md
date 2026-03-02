# GED EDA Project

This repository is dedicated to exploratory data analysis (EDA) and data cleaning for GED datasets.

## 📊 Data Strategy
To iterate quickly, development is performed on sampled subsets:
- **Candidate Data:** `data/raw_sample/candidate_table_raw_sample.xlsx` (5,000 rows)
- **Test Data:** `data/raw_sample/test_data_table_raw_sample.xlsx` (27,830 rows)

## Missing Value Analysis Notebook
Use the notebook:

- `notebooks/missing_value_handler.ipynb`

The notebook:
1. Prints missing-value analysis for both tables.
2. Writes a combined report to `data/processed/missing_value_report.csv`.
3. Writes cleaned outputs (same extension as source) to `data/processed/`.

### Default missing-value handling rules
- **Candidate table (`candidate_table_raw_sample`)**
  - Fill categorical fields with `"UNKNOWN"` (e.g., `GENDER`, `ETHNICITY`, `PREP_CENTER`).
  - Fill `STUDIED_FOR_GED` with mode.
  - Keep `CREDENTIAL_DATE` as missing when absent, and create `CREDENTIAL_DATE_MISSING` indicator.
- **Test table (`test_data_table_raw_sample`)**
  - Fill center/location categorical fields with `"UNKNOWN"`.
  - Fill status flags (`FIRST_COMPLETE`, `FIRST_PASSED`, `MAKE_COMPLETE`, `MAKE_PASSED`) with `0`.
  - Keep `RESULT_ID`, `SCORE`, and `EXAM_START` values as-is and add `*_MISSING` indicator columns.

### Outlier Detection & Distribution Checks
- **Notebook: notebooks/2. Outlier_detecting.ipynb
	•	Inputs (from the missing-value step):data/processed/candidate_cleaned.xlsx ; data/processed/test_cleaned.xlsx
	•	Outlier detection (IQR rule, k = 3.0):
	•	Apply an IQR-based rule to all numeric columns in both tables.
	•	Use k = 3.0 (chosen because k = 1.5 removed >10% rows, which was too aggressive).
	•	Outputs (row-level outlier flags):data/outliers/candidate_outliers_k3.csv ; data/outliers/test_outliers_k3.csv
	•	Outputs (datasets after outlier removal):data/processed/candidate_cleaned_no_outliers_k3.xlsx; data/processed/test_cleaned_no_outliers_k3.xlsx
	•	Distribution checks (after outlier removal):
	•	Generate numeric distribution summaries:
	•	data/outliers/candidate_numeric_distribution_summary_k3.csv
	•	data/outliers/test_numeric_distribution_summary_k3.csv
	•	Produce histograms and boxplots for each numeric variable to visually inspect:
	•	distribution shape after removal
	•	whether any extreme values still remain
	•	Removal ratio summary:
	•	Report (for both candidate and test tables):
	•	total rows before removal
	•	number of rows removed
	•	% removed under k = 3.0


## ⚙️ Large dataset guidance (3M+ rows)
For large runs, prefer CSV or Parquet input/output over Excel for speed and memory efficiency.

## 📁 Project Structure
```text
GED_EDA_Project/
├── data/
│   ├── raw_sample/       # Original sample files (input)
│   └── processed/        # Output report + cleaned files
├── notebooks/            # EDA and cleaning notebooks
├── sql/                  # SQL scripts for extraction/sampling
├── requirements.txt      # Dependencies
└── README.md
```
