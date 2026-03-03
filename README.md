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

## Qualitative to Quantitative Data Analysis

**Output Notebook:**
* '4_test_candidate_cleaned_qual_2_quant.xlsx`

The notebook:
1. Loads the merged candidate and test data from `3_candidate_test_attempts.xlsx`.
2. Removes rows containing 'CIVICS' in the `EXAM_SUBJECT` column.
3. Removes personally identifiable information columns (`C_ADDRESS`, `DATE_OF_BIRTH`).
4. Transforms all categorical variables to numeric codes using predefined mappings.
5. Writes the transformed dataset to `4_test_candidate_cleaned_qual_2_quant.xlsx`.

**Data Preprocessing Steps:**

* **Row Removal**
   * Removed all records where `EXAM_SUBJECT = 'CIVICS'` to focus analysis on the four core subject areas (Mathematics, Science, Reasoning, Social Studies).
   * Removal count and percentage documented in notebook output.

* **Column Removal**
   * Dropped `C_ADDRESS` and `DATE_OF_BIRTH` columns to protect candidate privacy and comply with data minimization principles.

* **Categorical to Numeric Transformation**
   * All categorical variables were encoded using consistent numeric schemes (detailed in Encoding Schema section).
   * Original column values were replaced in-place with numeric codes rather than creating separate columns.
   * Missing values that had been previously replaced with `"UNKNOWN"` were encoded as `0` across all variables.

**Qualitative to Quantitative Encoding Schema:**

* **LANGUAGE_CODE**
   * English (ENU) = `1`
   * Spanish (ESP) = `2`
   * Unknown = `0`

* **EXAM_SUBJECT**
   * Mathematics (MATH) = `1`
   * Science (SCIENCE) = `2`
   * Reasoning (REASONING) = `3`
   * Social Studies (SOCIAL_STUDIES) = `4`
   * Unknown = `0`

* **GENDER**
   * Male (MALE) = `1`
   * Female (FEMALE) = `2`
   * Nonbinary (NONBINARY) = `3`
   * Decline (DECLINE) = `4`
   * Unknown = `0`

* **ETHNICITY**
   * Non-Hispanic/Latino (NON_HISPANIC_LATINO) = `1`
   * Hispanic/Latino (HISPANIC_LATINO) = `2`
   * Decline (DECLINE) = `3`
   * Unknown = `0`

* **ENROLLMENT_STATUS**
   * Interested (INTERESTED) = `1`
   * Contacted (CONTACTED) = `2`
   * Enrolled (ENROLLED) = `3`
   * Credentialed (CREDENTIALED) = `4`
   * Dismissed (DISMISSED) = `5`
   * Unknown = `0`

* **HIGHEST_GRADE_COMPLETED**
   * Pre-K through 5th grade (C_PRE_5) = `1`
   * 6th through 8th grade (C_6_8) = `2`
   * 9th grade (C_9) = `3`
   * 10th grade (C_10) = `4`
   * 11th grade (C_11) = `5`
   * 12th grade (C_12) = `6`
   * Don't Remember (DONT_REMEMBER) = `7`
   * Other (OTHER) = `8`
   * Never (NEVER) = `9`
   * Unknown = `0`

* **LAST_YEAR_INCOME**
   * Under $5,000 (UNDER_5000) = `1`
   * $5,000-$9,999 (R_5000_9999) = `2`
   * $10,000-$19,999 (R_10000_19999) = `3`
   * $20,000-$29,999 (R_20000_29999) = `4`
   * $30,000-$39,999 (R_30000_39999) = `5`
   * $40,000-$49,999 (R_40000_49999) = `6`
   * $50,000-$74,999 (R_50000_74999) = `7`
   * $75,000 and above (R_75000_ABOVE) = `8`
   * Unknown = `0`

* **TESTING_REASON**
   * Work-Related (WORK_RELATED) = `1`
   * Educational Gain (EDUCATIONAL_GAIN) = `2`
   * Personal Gain (PERSONAL_GAIN) = `3`
   * Entrance to Military (ENTRANCE_TO_MILITARY) = `4`
   * Special Requirement (SPECIAL_REQUIREMENT) = `5`
   * Unknown = `0`

* **SCHOOL_INCOMPLETE_REASON**
   * Academic (ACADEMIC) = `1`
   * Personal (PERSONAL) = `2`
   * Personal and Academic (PERSONAL_AND_ACADEMIC) = `3`
   * Neither Personal nor Academic (NEITHER_PERSONAL_NOR_ACADEMIC) = `4`
   * Home Schooled (HOME_SCHOOLED) = `5`
   * High School Diploma from Another Country (HIGH_SCHOOL_DIPLOMA_FROM_ANOTHER_COUNTRY) = `6`
   * Unknown = `0`

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
