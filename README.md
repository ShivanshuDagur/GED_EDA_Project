# GED EDA Project

This repository is dedicated to the Exploratory Data Analysis (EDA) and data cleaning of the GED dataset. We utilize a modular, notebook-driven approach to develop and document our cleaning logic.

## 📊 Data Strategy
To ensure efficiency and rapid iteration, we are working with **sampled subsets** of the original data:
* **Candidate Data:** `data/raw_sample/candidate_table_raw_sample.xlsx` (5,000 records).
* **Test Data:** `data/raw_sample/test_data_table_raw_sample.xlsx` (Test records associated with the 5,000 sampled candidates).

## 📁 Project Structure
```text
GED_EDA_Project/
├── data/
│   ├── raw_sample/       # Original Excel sample files (Immutable)
│   └── processed_sample/ # Output for cleaned/transformed sample data
├── notebooks/            # EDA & Cleaning scripts (Primary Workspace)
├── sql/                  # SQL scripts for data extraction and sampling
├── src/                  # For utility python scripts.
├── .gitignore            # Prevents venv and temporary files from being tracked
├── requirements.txt      # Project dependencies (pandas, openpyxl, etc.)
└── README.md             # Project documentation