"""
GED Analytics & Econometric Modeling Package
============================================
A modular Python package for exploratory data analysis, unsupervised candidate
segmentation, econometric disparity modeling, and visualization generation for
GED Adult Education datasets.
"""

__version__ = "1.0.0"
__author__ = "GED Analytics Research Team"

from .config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    VISUALS_DIR,
    REPORTS_DIR,
    CENSUS_REGIONS,
    STATE_TO_REGION,
    EXAM_SUBJECTS,
)

from .data_processing import (
    handle_missing_values,
    detect_outliers_iqr,
    remove_outliers_iqr,
    standardize_zip_code,
    clean_and_parse_types,
)

from .encoding import (
    ENCODING_SCHEMAS,
    encode_qualitative_to_quantitative,
    strip_pii_columns,
)

from .metrics import (
    aggregate_candidate_metrics,
    calculate_funnel_kpis,
    aggregate_state_metrics,
    aggregate_regional_metrics,
    calculate_resource_impact,
    calculate_test_method_metrics,
)

from .clustering import (
    assign_candidate_persona,
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
    set_visual_style,
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
