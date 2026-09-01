"""
End-to-End Analytical Pipeline Runner for GED Analytics
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd

from .config import (
    FINAL_CLEANED_DATA_PATH,
    RAW_CANDIDATE_PATH,
    RAW_TEST_PATH,
    VISUALS_DIR,
    REPORTS_DIR,
)
from .data_processing import (
    handle_missing_values,
    remove_outliers_iqr,
    clean_and_parse_types,
)
from .encoding import encode_qualitative_to_quantitative
from .metrics import (
    aggregate_candidate_metrics,
    calculate_funnel_kpis,
    aggregate_state_metrics,
    aggregate_regional_metrics,
    calculate_resource_impact,
    calculate_test_method_metrics,
)
from .clustering import (
    generate_candidate_personas,
    cluster_states,
    compute_persona_gap_summary,
)
from .modeling import (
    fit_enrollment_logit,
    fit_completion_logit,
    calculate_simpsons_paradox_metrics,
    compute_correlations,
)
from .visualization import (
    plot_kpi_rates,
    plot_score_distributions,
    plot_persona_profiles,
    plot_persona_distribution,
    plot_persona_gap_analysis,
    plot_resource_impact,
    plot_simpsons_paradox,
    plot_test_method_comparison,
    plot_regional_breakdowns,
    generate_state_choropleth,
)


def run_full_analysis(
    input_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Executes the entire end-to-end analytical pipeline:
    1. Loads cleaned final candidate-test dataset.
    2. Computes candidate KPIs and journey funnel.
    3. Calculates state and regional resource disparities.
    4. Segments candidates into 4 behavioral personas.
    5. Clusters states into 4 performance archetypes.
    6. Fits econometric Logit models and quantifies Simpson's paradox.
    7. Generates all visual figures and maps.

    Returns:
        Dictionary of analytical results, dataframes, and model summaries.
    """
    data_path = Path(input_path) if input_path else FINAL_CLEANED_DATA_PATH
    out_dir = Path(output_dir) if output_dir else VISUALS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("=" * 70)
        print("GED ANALYTICS & ECONOMETRIC DISPARITY PIPELINE")
        print("=" * 70)
        print(f"[1/6] Loading data from: {data_path.name}")

    if not data_path.exists():
        raise FileNotFoundError(f"Input data not found at: {data_path}")

    df = pd.read_csv(data_path)
    if verbose:
        print(f"      Loaded {len(df):,} exam attempt records.")

    # 1. Candidate Aggregations & KPIs
    if verbose:
        print("[2/6] Aggregating candidate-level metrics & funnel KPIs...")
    cand_df = aggregate_candidate_metrics(df)
    funnel_kpis = calculate_funnel_kpis(cand_df)

    # 2. State & Regional Aggregations
    if verbose:
        print("[3/6] Computing state & regional resource disparities...")
    state_metrics = aggregate_state_metrics(df, min_candidates=10)
    regional_metrics = aggregate_regional_metrics(state_metrics)
    resource_impact = calculate_resource_impact(df)
    method_overall, method_regional = calculate_test_method_metrics(cand_df)

    # 3. Personas & State Clustering
    if verbose:
        print("[4/6] Performing unsupervised segmentation (Personas & Archetypes)...")
    cand_personas, persona_summary = generate_candidate_personas(cand_df)
    state_clusters, cluster_profile = cluster_states(state_metrics, n_clusters=4)
    gap_summary = compute_persona_gap_summary(cand_personas)

    # 4. Econometric Modeling
    if verbose:
        print("[5/6] Fitting Logit models & testing Simpson's paradox...")
    enrollment_logit = fit_enrollment_logit(cand_personas, state_metrics)
    completion_logit = fit_completion_logit(cand_personas, state_metrics)
    paradox_metrics = calculate_simpsons_paradox_metrics(state_metrics)
    corr_matrix = compute_correlations(state_metrics)

    # 5. Visual Generation
    if verbose:
        print("[6/6] Rendering publication-grade charts & choropleth maps...")

    plot_kpi_rates(funnel_kpis, out_dir / "chart_1_kpi_rates.png")
    plot_score_distributions(df, out_dir / "chart_2_score_distribution.png")
    plot_persona_profiles(persona_summary, out_dir / "persona_profiles.png")
    plot_persona_distribution(persona_summary, out_dir / "persona_distribution.png")
    plot_persona_gap_analysis(cand_personas, out_dir / "persona_gap_analysis.png")
    plot_resource_impact(resource_impact, out_dir / "resource_impact.png")
    plot_simpsons_paradox(state_metrics, out_dir / "paradox_proof.png")
    plot_test_method_comparison(method_overall, method_regional, out_dir)
    plot_regional_breakdowns(regional_metrics, out_dir)

    # State maps
    generate_state_choropleth(state_metrics, "completion_rate", "State-Level GED Completion Rate", "map_state_completion_rate.png", out_dir)
    generate_state_choropleth(state_metrics, "center_density", "State-Level Testing Center Density", "map_state_center_density.png", out_dir)
    generate_state_choropleth(state_metrics, "prep_coverage", "State-Level Prep Center Coverage", "map_state_prep_coverage.png", out_dir)

    if verbose:
        print("\n" + "=" * 70)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 70)
        print(f"Candidates Analyzed:  {len(cand_df):,}")
        print(f"Overall Pass Rate:    {cand_df['pass_rate'].mean():.1%}")
        print(f"Credential Rate:      {cand_df['credential_earned'].mean():.1%}")
        print(f"Visuals Generated in: {out_dir}")
        print("=" * 70)

    return {
        "candidate_data": cand_personas,
        "funnel_kpis": funnel_kpis,
        "state_metrics": state_metrics,
        "regional_metrics": regional_metrics,
        "persona_summary": persona_summary,
        "state_clusters": state_clusters,
        "cluster_profile": cluster_profile,
        "gap_summary": gap_summary,
        "resource_impact": resource_impact,
        "paradox_metrics": paradox_metrics,
        "enrollment_logit": enrollment_logit,
        "completion_logit": completion_logit,
    }


if __name__ == "__main__":
    run_full_analysis()
