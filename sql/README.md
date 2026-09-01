# SQL Data Extraction & Sampling Strategy

This directory contains the SQL extraction and stratified sampling logic used to generate the research dataset from enterprise GED database tables.

---

## 1. Scripts
* **[`sample_data_script.sql`](sample_data_script.sql):** SQL Server / T-SQL script that extracts a representative random sample of candidates and their complete exam attempt histories.

---

## 2. Sampling Methodology
Because production GED relational databases contain millions of historical candidate records, the data pipeline utilizes a stratified random extraction protocol:

```sql
-- Step 1: Create a temporary table with 5,000 randomized candidates
SELECT TOP 5000 CANDIDATE_ID
INTO #RandomCandidates
FROM dbo.candidate
ORDER BY NEWID();

-- Step 2: Extract complete candidate demographic & enrollment records
SELECT c.*
FROM dbo.candidate c
INNER JOIN #RandomCandidates rc ON c.CANDIDATE_ID = rc.CANDIDATE_ID
ORDER BY c.CANDIDATE_ID;

-- Step 3: Extract all longitudinal test attempts for the sampled candidates
SELECT t.*
FROM dbo.TEST_DATA t
INNER JOIN #RandomCandidates rc ON t.CANDIDATE_ID = rc.CANDIDATE_ID
ORDER BY t.CANDIDATE_ID, t.EXAM_SUBJECT;

-- Step 4: Cleanup
DROP TABLE #RandomCandidates;
```

---

## 3. Data Integrity & Join Consistency
* **Inner Join Integrity:** Extracting all exam records conditioned on the exact sampled `#RandomCandidates` ensures 100% relational integrity between candidate demographics and test attempts.
* **Longitudinal Exam Breadth:** Candidates with multiple retakes or multi-subject journeys are fully preserved, enabling accurate calculation of retake frequencies, subject completion funnels, and test method adoption rates.
