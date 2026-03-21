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
    - ⭐️Outputs (row-level outlier flags):2.candidate_outliers removed_k=3.csv ; 2.test_ outliers removed_k=3.csv
    - ⭐️Outputs (datasets after outlier removal):2.candidate_after missing value.csv & outliers detectors; 2.test_after missing value & outliers detectors.csv
- **Distribution checks (after outlier removal):2.candidate_numeric distribution summary k=3.csv ; 2.test_numeric distribution summary k=3.csv
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


## Final Data Cleaning and Type Fixing

**Output Notebook:** 
`5_test_candidate_cleaned_final.csv`

The notebook:
1. Loads the merged candidate and test data from `4_test_candidate_cleaned_qual_2_quant.xlsx`.
2. Standardize formats, correct data types(), and implementing robust cleaning rules for free-form text fields.
3. Writes the transformed dataset to `5_test_candidate_cleaned_final.csv`.

### **Data Preprocessing Steps:**

* **Encoding and Null Handling**
    * Unified various text-based null indicators (e.g., `"NULL"`, `"No street address available"`, `"NA"`) into standard `NaN` values to ensure consistent missing data treatment.

* **Date and Type Standardization**
    * **Date Parsing**: Converted `ACCOUNT_SETUP_COMPLETE_DATE` and `CREDENTIAL_DATE` into formal `datetime64[ns]` objects for time-series compatibility.
    * **Type Fixing**: Forced `CANDIDATE_ID`, `RESULT_ID`, and `TEST_CENTER_ID` to **String** format to prevent ID truncation or accidental scientific notation (e.g., `4.33E+06`).

* **Free-form Zip Code Cleaning**
    * Implemented a custom Regex-based logic to standardize `ZIP` and `T_POSTAL_CODE` fields.
    * **Cleaning Logic**:
        * **Noise Removal**: Strips all non-numeric characters (e.g., `"ls-12345"` → `"12345"`).
        * **Length Filtering**: Entries with $\le 2$ digits are discarded as invalid noise.
        * **Zero Padding**: 3 to 4-digit entries are padded with leading zeros (e.g., `"530"` → `"00530"`) to recover lost prefixes from Excel formatting.
        * **Standardization**: All valid entries are truncated to a fixed 5-digit format.

## **Data Analysis Steps:**
* **1.Clustering Analysis**
Input: 5_test_candidate_cleaned_final.csv  
Output: K=4  

Final cluster sizes:  
1 415  
2 1118  
3 1667  
4 497  

Cluster 1: High-performing, credentialed candidates with low use of support resources. They tended to pass quickly,
had very few retakes, and rarely used GED Ready or online testing.  
Cluster 2: High-performing, credentialed candidates with high use of support resources. Their outcomes were still
strong, but they relied more on GED Ready, prep centers, and repeated attempts.  
Cluster 3: Lower-performing, non-credentialed candidates with high support usage. They frequently used GED Ready
and prep centers, but these supports did not fully translate into credential completion.  
Cluster 4: Lowest-performing, non-credentialed candidates with low support usage. They showed weak outcomes,
little use of preparation resources, and low retake intensity, making them the most at-risk group.  
  
* **2. Topic 1: GED Candidate Profile Analysis - Davey**

* **3. Topic 2: GED Candidate Profile Analysis - Ankit**  

    * **3.1 Question: ‘Do regions with fewer testing or preparation resources also show lower GED exam participation or lower GED completion?’**    
    * **3.2 Key Takeaways:**  
        3.2.1 Exam participation changes little across states, but completion rate varies much more across states, implying that resource differences do not seem to strongly affect whether candidates take an exam, but impact their completion rate.  
        3.2.2 Logit model 1&2 show that testing-center availability does not significantly affect exam-taking, but it does significantly improve the likelihood of GED completion.  
        3.2.3 Prep-related resource measures are not statistically significant in the main completion model.  

    * **3.3 Metrics:**   
        Counts are derived from the cleaned exam-candidate file and rolled up to each candidate’s home state (C_STATE).  
        •	n_testing_centers: number of distinct testing centers  
        •	n_candidates: number of distinct candidates  
        •	n_prep_center_users: candidates with a non-missing prep-center identifier  
        •	n_exam_takers: candidates with at least one exam signal (RESULT_ID, EXAM_START, or SCORE non-missing)  
        •	n_completers: candidates with a credential date or ENROLLMENT_STATUS equal to 4 State-level metrics
        •	center_density = n_testing_centers / n_candidates (testing centers per candidate in the state)  
        •	prep_coverage = n_prep_center_users / n_candidates (share of candidates using a prep center)  
        •	enrollment_rate = n_exam_takers / n_candidates (share taking at least one GED exam)  
        •	completion_rate = n_completers / n_candidates (share earning the GED credential)  
        •	prep_center_density = n_prep_centers / n_candidates (distinct prep-center IDs per candidate, from prep-center supply merged at state level)  

    * **3.4.1 Logit Model 1 — Enrollment (no significant coefficients in the result)**    
logit P(has_exam_attempt_i=1) = β₀ + β₁·center_density + β₂·prep_coverage + β₃·prep_center_density + β₄·age + Σ controls + region FE + quarter FE  
•	where controls include:  
•	GENDER  
•	LAST_YEAR_INCOME  
•	HIGHEST_GRADE_COMPLETED  
•	ETHNICITY  
•	TESTING_REASON  
•	LANGUAGE_CODE  

    * **3.4.2 Logit Model 2 — Completion (only the center_density is significant in the result)**  
logit P(is_completer_i=1) = β₀ + β₁·center_density + β₂·prep_coverage + β₃·prep_center_density + β₄·age + Σ controls + region FE + quarter FE  
•	where controls include:  
•	GENDER  
•	LAST_YEAR_INCOME  
•	HIGHEST_GRADE_COMPLETED  
•	ETHNICITY  
•	TESTING_REASON  
•	LANGUAGE_CODE  


* 
* ...
* **Encoding and Null Handling**
## ⚙️ Large dataset guidance (3M+ rows)
For large runs, prefer CSV or Parquet input/output over Excel for speed and memory efficiency.

## 📁 Project Structure
```text

GED_EDA_Project/
├── data/
│   ├── raw_sample/                 # Original sample files (input)
│   ├── processed/                  # Cleaned outputs + reports generated from cleaning 
├── notebooks/
│   ├── missing_value_handler.ipynb # Step 1: missing-value handling + cleaned datasets 
│   └── 2. Outlier_detecting.ipynb  # Step 2: outlier detection (IQR rule) + distribution 
├── sql/                            # SQL scripts for extraction/sampling
├── requirements.txt                # Dependencies
└── README.md

```
