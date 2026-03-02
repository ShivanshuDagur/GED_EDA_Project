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
	- ⭐️Inputs (from the missing-value step):data/processed/candidate_cleaned.xlsx ; data/processed/test_cleaned.xlsx
	- ⭐️Outlier detection (IQR rule, k = 3.0):
	- Apply an IQR-based rule to all numeric columns in both tables.
	- Use k = 3.0 (chosen because k = 1.5 removed >10% rows, which was too aggressive).
    - ⭐️Outputs (row-level outlier flags):data/outliers/candidate_outliers_k3.csv ; data/outliers/test_outliers_k3.csv
    - ⭐️Outputs (datasets after outlier removal):data/processed/candidate_cleaned_no_outliers_k3.xlsx; data/processed/test_cleaned_no_outliers_k3.xlsx
- **Distribution checks (after outlier removal):Generate numeric distribution summaries:data/outliers/candidate_numeric_distribution_summary_k3.csv ; data/outliers/test_numeric_distribution_summary_k3.csv
	- Produce histograms and boxplots for each numeric variable to visually inspect after removal.

- **Result Understanding: Outlier removal summary and choice of k=3
We experimented with two IQR thresholds for outlier detection:
- **Initial run (k = 1.5)**  
  - **Candidate table**  
    - Total rows before: 5,000  
    - Rows removed as outliers: 148  
    - Percentage removed: **2.96%**  
  - **Test table**  
    - Total rows before: 27,830  
    - Rows removed as outliers: 2,861  
    - Percentage removed: **10.28%**  [10% is too big, so we used k=3]
While the candidate table removal rate was moderate, removing more than 10% of the test records was considered too aggressive for this dataset. This would risk discarding many potentially informative observations.
- **Final choice (k = 3.0)**  
  - **Candidate table**  
    - Total rows before: 5,000  
    - Rows removed as outliers: 51  
    - Percentage removed: **1.02%**  
  - **Test table**  
    - Total rows before: 27,830  
    - Rows removed as outliers: 2,135  
    - Percentage removed: **7.67%**  
Using **k = 3.0** provides a more conservative outlier definition: it still removes extreme values but keeps a larger portion of the data, especially in the test table. The downstream “no-outlier” datasets and distribution checks in this project are therefore based on the **k = 3.0** configuration.

## ⚙️ Large dataset guidance (3M+ rows)
For large runs, prefer CSV or Parquet input/output over Excel for speed and memory efficiency.

## 📁 Project Structure
```text

GED_EDA_Project/
├── data/
│   ├── raw_sample/                 # Original sample files (input)
│   ├── processed/                  # Cleaned outputs + reports generated from cleaning 
│   └── 2. Outliers+Distribution/   # Outputs from outlier detection + distribution 
├── notebooks/
│   ├── missing_value_handler.ipynb # Step 1: missing-value handling + cleaned datasets 
│   └── 2. Outlier_detecting.ipynb  # Step 2: outlier detection (IQR rule) + distribution 
├── sql/                            # SQL scripts for extraction/sampling
├── requirements.txt                # Dependencies
└── README.md

```
