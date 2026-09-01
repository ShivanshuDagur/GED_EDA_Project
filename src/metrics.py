"""
Candidate KPIs, State/Regional Aggregations, and Resource Impact Metrics
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .config import PASS_SCORE_THRESHOLD, COLLEGE_READY_SCORE_THRESHOLD, STATE_TO_REGION, VALID_US_STATES


def aggregate_candidate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates exam-level records into a unified candidate-level feature matrix.

    Args:
        df: Merged exam and candidate DataFrame (e.g. 5_test_candidate_cleaned_final.csv)

    Returns:
        DataFrame with one row per unique CANDIDATE_ID with performance & behavior KPIs.
    """
    data = df.copy()

    # Clean sentinel values in PREP_CENTER
    if "PREP_CENTER" in data.columns:
        data["PREP_CENTER"] = data["PREP_CENTER"].replace({"UNKNOWN": None, "nan": None, np.nan: None})

    # Ensure clean score column
    if "SCORE_MISSING" in data.columns:
        data["score_clean"] = np.where(data["SCORE_MISSING"] == 1, np.nan, data["SCORE"])
    else:
        data["score_clean"] = pd.to_numeric(data["SCORE"], errors="coerce")

    g = data.groupby("CANDIDATE_ID")

    cand = pd.DataFrame(index=list(g.groups.keys())).reset_index(names="CANDIDATE_ID")

    # 1. Performance KPIs
    cand["avg_score"] = g["score_clean"].mean().values
    cand["max_score"] = g["score_clean"].max().values
    cand["min_score"] = g["score_clean"].min().values

    # Credential completion flag
    if "CREDENTIAL_DATE" in data.columns and "ENROLLMENT_STATUS" in data.columns:
        cand["credential_earned"] = g.apply(
            lambda x: int(x["CREDENTIAL_DATE"].notna().any() or (x["ENROLLMENT_STATUS"] == 4).any())
        ).values
    elif "CREDENTIAL_DATE" in data.columns:
        cand["credential_earned"] = g["CREDENTIAL_DATE"].apply(lambda s: int(s.notna().any())).values
    else:
        cand["credential_earned"] = 0

    # Pass rates
    cand["pass_rate"] = g.apply(
        lambda x: float(np.nanmean((x["score_clean"].notna() & (x["score_clean"] >= PASS_SCORE_THRESHOLD)).astype(int)))
    ).values

    cand["college_ready_rate"] = g.apply(
        lambda x: float(np.nanmean((x["score_clean"].notna() & (x["score_clean"] >= COLLEGE_READY_SCORE_THRESHOLD)).astype(int)))
    ).values

    # Subject count & pass counts
    if "EXAM_SUBJECT" in data.columns:
        cand["n_unique_subjects"] = g["EXAM_SUBJECT"].nunique().values
        cand["total_attempts"] = g["EXAM_SUBJECT"].count().values
        cand["avg_retakes"] = g["EXAM_SUBJECT"].apply(
            lambda x: (x.size / x.nunique() - 1) if x.nunique() > 0 else 0
        ).values
    else:
        cand["n_unique_subjects"] = 0
        cand["total_attempts"] = 0
        cand["avg_retakes"] = 0

    cand["n_passed_exams"] = g.apply(
        lambda x: int((x["score_clean"].notna() & (x["score_clean"] >= PASS_SCORE_THRESHOLD)).sum())
    ).values

    # 2. Preparation Behaviors
    if "GED_READY" in data.columns:
        cand["used_ged_ready"] = g["GED_READY"].apply(lambda x: int((x == 1).any())).values
    else:
        cand["used_ged_ready"] = 0

    if "PREP_CENTER" in data.columns:
        cand["has_prep_center"] = g["PREP_CENTER"].apply(lambda x: int(x.notna().any())).values
    else:
        cand["has_prep_center"] = 0

    if "ON_VUE" in data.columns:
        cand["pct_online"] = g["ON_VUE"].apply(lambda x: float((x == 1).mean())).values
        cand["test_method"] = cand["pct_online"].apply(lambda x: "Online (OnVUE)" if x > 0.5 else "Physical Center")
    else:
        cand["pct_online"] = 0.0
        cand["test_method"] = "Physical Center"

    # 3. Geography & Demographics
    cand["C_STATE"] = g["C_STATE"].first().values if "C_STATE" in data.columns else "UNKNOWN"
    cand["census_region"] = cand["C_STATE"].map(STATE_TO_REGION)

    if "BIRTH_YEAR" in data.columns:
        cand["birth_year"] = pd.to_numeric(g["BIRTH_YEAR"].first().values, errors="coerce")
        cand["age"] = 2024 - cand["birth_year"]
    elif "DATE_OF_BIRTH" in data.columns:
        dob = pd.to_datetime(g["DATE_OF_BIRTH"].first().values, errors="coerce")
        cand["age"] = 2024 - dob.dt.year
    else:
        cand["age"] = np.nan

    cand["gender"] = g["GENDER"].first().values if "GENDER" in data.columns else 0
    cand["ethnicity"] = g["ETHNICITY"].first().values if "ETHNICITY" in data.columns else 0
    cand["enrollment_status"] = g["ENROLLMENT_STATUS"].first().values if "ENROLLMENT_STATUS" in data.columns else 0

    if "LAST_YEAR_INCOME" in data.columns:
        cand["income_level"] = g["LAST_YEAR_INCOME"].first().values
    if "HIGHEST_GRADE_COMPLETED" in data.columns:
        cand["highest_grade"] = g["HIGHEST_GRADE_COMPLETED"].first().values

    return cand


def calculate_funnel_kpis(cand_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes overall candidate journey funnel metrics.
    """
    total_candidates = len(cand_df)
    if total_candidates == 0:
        return pd.DataFrame()

    attempted_at_least_one = (cand_df["total_attempts"] > 0).sum()
    attempted_all_four = (cand_df["n_unique_subjects"] >= 4).sum()
    credentialed = (cand_df["credential_earned"] == 1).sum()

    used_ged_ready = (cand_df["used_ged_ready"] == 1).sum()
    ready_and_attempted_all = ((cand_df["used_ged_ready"] == 1) & (cand_df["n_unique_subjects"] >= 4)).sum()
    ready_and_credentialed = ((cand_df["used_ged_ready"] == 1) & (cand_df["credential_earned"] == 1)).sum()

    kpi_records = [
        {"Funnel Stage": "Total Candidates (Enrolled)", "Count": total_candidates, "Rate (%)": 100.0},
        {"Funnel Stage": "Attempted ≥1 Exam", "Count": attempted_at_least_one, "Rate (%)": (attempted_at_least_one / total_candidates) * 100},
        {"Funnel Stage": "Attempted All 4 Exams", "Count": attempted_all_four, "Rate (%)": (attempted_all_four / total_candidates) * 100},
        {"Funnel Stage": "Credential Earned", "Count": credentialed, "Rate (%)": (credentialed / total_candidates) * 100},
        {"Funnel Stage": "Used GED Ready", "Count": used_ged_ready, "Rate (%)": (used_ged_ready / total_candidates) * 100},
        {"Funnel Stage": "GED Ready: Attempted All 4", "Count": ready_and_attempted_all, "Rate (%)": (ready_and_attempted_all / max(1, used_ged_ready)) * 100},
        {"Funnel Stage": "GED Ready: Credentialed", "Count": ready_and_credentialed, "Rate (%)": (ready_and_credentialed / max(1, used_ged_ready)) * 100},
    ]

    return pd.DataFrame(kpi_records)


def aggregate_state_metrics(
    df: pd.DataFrame,
    min_candidates: int = 10,
    valid_states_only: bool = True,
) -> pd.DataFrame:
    """
    Computes state-level supply metrics (test center density, prep coverage)
    and outcome rates (enrollment rate, completion rate).

    Args:
        df: Exam-level or merged dataset
        min_candidates: Minimum candidate count threshold to reduce noise
        valid_states_only: Filter to valid US 50 states + DC

    Returns:
        DataFrame with state-level aggregates and supply metrics
    """
    data = df.copy()
    if "PREP_CENTER" in data.columns:
        data["PREP_CENTER"] = data["PREP_CENTER"].replace({"UNKNOWN": None, np.nan: None})

    # 1. State-level test center supply
    if "T_STATE" in data.columns and "TEST_CENTER_ID" in data.columns:
        centers = data.groupby("T_STATE")["TEST_CENTER_ID"].nunique().reset_index()
        centers.columns = ["C_STATE", "n_testing_centers"]
    else:
        centers = pd.DataFrame(columns=["C_STATE", "n_testing_centers"])

    # 2. Candidate level aggregation
    cand = aggregate_candidate_metrics(data)
    cand["has_exam_attempt"] = (cand["total_attempts"] > 0).astype(int)

    # 3. State-level metric rollups
    state_metrics = cand.groupby("C_STATE").agg(
        n_candidates=("CANDIDATE_ID", "count"),
        n_exam_takers=("has_exam_attempt", "sum"),
        n_completers=("credential_earned", "sum"),
        n_prep_users=("has_prep_center", "sum"),
        avg_score=("avg_score", "mean"),
    ).reset_index()

    state_metrics["enrollment_rate"] = state_metrics["n_exam_takers"] / state_metrics["n_candidates"]
    state_metrics["completion_rate"] = state_metrics["n_completers"] / state_metrics["n_candidates"]
    state_metrics["prep_coverage"] = state_metrics["n_prep_users"] / state_metrics["n_candidates"]

    # Merge center supply
    state_metrics = state_metrics.merge(centers, on="C_STATE", how="left").fillna({"n_testing_centers": 0})
    state_metrics["center_density"] = state_metrics["n_testing_centers"] / state_metrics["n_candidates"]

    # Region mapping
    state_metrics["census_region"] = state_metrics["C_STATE"].map(STATE_TO_REGION)

    if valid_states_only:
        state_metrics = state_metrics[state_metrics["C_STATE"].isin(VALID_US_STATES)].copy()

    if min_candidates > 0:
        state_metrics = state_metrics[state_metrics["n_candidates"] >= min_candidates].copy()

    return state_metrics


def aggregate_regional_metrics(state_metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Rolls up state-level metrics into Census Region averages.
    """
    valid_data = state_metrics_df.dropna(subset=["census_region"])
    regional = valid_data.groupby("census_region").agg(
        n_states=("C_STATE", "count"),
        total_candidates=("n_candidates", "sum"),
        center_density=("center_density", "mean"),
        prep_coverage=("prep_coverage", "mean"),
        enrollment_rate=("enrollment_rate", "mean"),
        completion_rate=("completion_rate", "mean"),
    ).reset_index()

    return regional.sort_values("completion_rate", ascending=False)


def calculate_resource_impact(df: pd.DataFrame, min_sample: int = 10) -> pd.DataFrame:
    """
    Evaluates completion rates and score impacts for specific preparation resources.
    """
    cand = aggregate_candidate_metrics(df)
    resource_cols = [c for c in df.columns if c.startswith("STUDY_HELPFUL_") or c == "STUDY_LOCATION_TEST_PREPARATION_CENTER"]

    # Candidate level max for each resource flag
    g = df.groupby("CANDIDATE_ID")
    for col in resource_cols:
        cand[col] = g[col].max().values

    results = []
    for col in resource_cols:
        used = cand[cand[col] == 1]
        not_used = cand[cand[col] == 0]

        if len(used) >= min_sample:
            used_rate = used["credential_earned"].mean()
            not_used_rate = not_used["credential_earned"].mean() if len(not_used) > 0 else 0
            used_score = used["avg_score"].mean()
            not_used_score = not_used["avg_score"].mean() if len(not_used) > 0 else 0

            clean_name = (
                col.replace("STUDY_HELPFUL_", "")
                .replace("STUDY_LOCATION_", "")
                .replace("_", " ")
                .title()
            )

            results.append({
                "Resource": clean_name,
                "Used_Completion_Rate": used_rate,
                "Not_Used_Completion_Rate": not_used_rate,
                "Completion_Rate_Diff": used_rate - not_used_rate,
                "Used_Avg_Score": used_score,
                "Not_Used_Avg_Score": not_used_score,
                "Score_Diff": used_score - not_used_score,
                "Sample_Size": len(used),
            })

    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values("Used_Completion_Rate", ascending=False)
    return res_df


def calculate_test_method_metrics(cand_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculates overall and regional completion rates and adoption for Online (OnVUE) vs Physical Centers.
    """
    overall = cand_df.groupby("test_method").agg(
        candidate_count=("CANDIDATE_ID", "count"),
        completion_rate=("credential_earned", "mean"),
        avg_score=("avg_score", "mean"),
    ).reset_index()

    valid_region = cand_df.dropna(subset=["census_region"])
    regional = valid_region.groupby(["census_region", "test_method"]).agg(
        candidate_count=("CANDIDATE_ID", "count"),
        completion_rate=("credential_earned", "mean"),
    ).reset_index()

    return overall, regional
