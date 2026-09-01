"""
Econometric Logit Modeling, Statistical Tests, and Simpson's Paradox Analysis
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def fit_enrollment_logit(
    cand_df: pd.DataFrame,
    state_metrics_df: pd.DataFrame,
) -> Optional[Any]:
    """
    Fits Logit Model 1: Probability of taking at least one official GED exam.
    logit(P(has_exam_attempt_i = 1)) ~ center_density + prep_coverage + age + demographic controls
    """
    # Merge state metrics with candidate data
    state_subset = state_metrics_df[["C_STATE", "center_density", "prep_coverage"]].drop_duplicates()
    merged = cand_df.merge(state_subset, on="C_STATE", how="inner")

    # Define formula
    formula = "has_exam_attempt ~ center_density + prep_coverage"
    if "age" in merged.columns and merged["age"].notna().sum() > 50:
        formula += " + age"
    if "gender" in merged.columns and merged["gender"].nunique() > 1:
        formula += " + C(gender)"
    if "income_level" in merged.columns and merged["income_level"].nunique() > 1:
        formula += " + C(income_level)"

    merged["has_exam_attempt"] = (merged["total_attempts"] > 0).astype(int)

    try:
        model = smf.logit(formula=formula, data=merged).fit(disp=False)
        return model
    except Exception as e:
        print(f"[WARNING] Logit Model 1 fit failed: {e}")
        return None


def fit_completion_logit(
    cand_df: pd.DataFrame,
    state_metrics_df: pd.DataFrame,
) -> Optional[Any]:
    """
    Fits Logit Model 2: Probability of earning the GED credential.
    logit(P(credential_earned_i = 1)) ~ center_density + prep_coverage + age + demographic controls
    """
    state_subset = state_metrics_df[["C_STATE", "center_density", "prep_coverage"]].drop_duplicates()
    merged = cand_df.merge(state_subset, on="C_STATE", how="inner")

    formula = "credential_earned ~ center_density + prep_coverage"
    if "age" in merged.columns and merged["age"].notna().sum() > 50:
        formula += " + age"
    if "gender" in merged.columns and merged["gender"].nunique() > 1:
        formula += " + C(gender)"
    if "income_level" in merged.columns and merged["income_level"].nunique() > 1:
        formula += " + C(income_level)"

    try:
        model = smf.logit(formula=formula, data=merged).fit(disp=False)
        return model
    except Exception as e:
        print(f"[WARNING] Logit Model 2 fit failed: {e}")
        return None


def calculate_simpsons_paradox_metrics(
    state_metrics_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Computes correlation coefficients at the state level vs. the regional level
    to detect and quantify Simpson's Paradox in preparation center impact.

    Returns:
        Dict with state correlation, regional correlation, and regional breakdowns.
    """
    valid_states = state_metrics_df.dropna(subset=["prep_coverage", "completion_rate", "census_region"]).copy()

    # State-level correlation
    state_corr = valid_states[["prep_coverage", "completion_rate"]].corr().iloc[0, 1]

    # Regional aggregation & correlation
    reg_agg = valid_states.groupby("census_region").agg(
        prep_coverage=("prep_coverage", "mean"),
        completion_rate=("completion_rate", "mean"),
        n_candidates=("n_candidates", "sum"),
    ).reset_index()

    reg_corr = reg_agg[["prep_coverage", "completion_rate"]].corr().iloc[0, 1]

    return {
        "state_correlation": state_corr,
        "regional_correlation": reg_corr,
        "state_sample_size": len(valid_states),
        "regional_data": reg_agg,
    }


def compute_correlations(state_metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a correlation matrix for key state-level infrastructure and outcome variables.
    """
    cols = ["center_density", "prep_coverage", "enrollment_rate", "completion_rate", "avg_score"]
    available_cols = [c for c in cols if c in state_metrics_df.columns]
    return state_metrics_df[available_cols].corr()
