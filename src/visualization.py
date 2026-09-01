"""
Publication-Quality Visualization Suite for GED Analytics
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .config import (
    COLOR_PALETTE_PRIMARY,
    PASS_SCORE_THRESHOLD,
    COLLEGE_READY_SCORE_THRESHOLD,
    PERSONA_COLORS,
    VISUALS_DIR,
)


def set_visual_style() -> None:
    """Sets a clean, modern aesthetic for matplotlib and seaborn figures."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["grid.color"] = "#eaeaea"
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["figure.dpi"] = 300
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.bbox"] = "tight"


def plot_kpi_rates(kpi_df: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Plots the candidate journey funnel KPI conversion rates."""
    set_visual_style()
    fig, ax = plt.subplots(figsize=(11, 6))

    bars = sns.barplot(
        data=kpi_df,
        x="Funnel Stage",
        y="Rate (%)",
        palette="crest",
        ax=ax,
    )

    ax.set_title("GED Candidate Journey: Funnel Conversion Rates", fontsize=15, fontweight="bold", pad=15)
    ax.set_ylabel("Conversion Rate (%)", fontsize=12)
    ax.set_xlabel("")
    ax.set_ylim(0, 115)
    plt.xticks(rotation=20, ha="right", fontsize=10)

    # Add data labels
    for p in bars.patches:
        height = p.get_height()
        ax.annotate(
            f"{height:.1f}%",
            (p.get_x() + p.get_width() / 2.0, height + 2),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="semibold",
        )

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_score_distributions(test_df: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Plots score distributions across subjects with pass and college-ready thresholds."""
    set_visual_style()
    data = test_df.copy()

    if "score_clean" not in data.columns and "SCORE" in data.columns:
        data["score_clean"] = pd.to_numeric(data["SCORE"], errors="coerce")

    # Map subject codes to names if numeric
    subject_map = {1: "Math", 2: "Science", 3: "Reasoning", 4: "Social Studies"}
    if "EXAM_SUBJECT" in data.columns:
        if pd.api.types.is_numeric_dtype(data["EXAM_SUBJECT"]):
            data["Subject_Name"] = data["EXAM_SUBJECT"].map(subject_map)
        else:
            data["Subject_Name"] = data["EXAM_SUBJECT"].astype(str).str.title()
    else:
        data["Subject_Name"] = "All Subjects"

    valid_scores = data.dropna(subset=["score_clean"])
    valid_scores = valid_scores[(valid_scores["score_clean"] >= 100) & (valid_scores["score_clean"] <= 200)]

    fig, ax = plt.subplots(figsize=(12, 7))

    sns.kdeplot(
        data=valid_scores,
        x="score_clean",
        hue="Subject_Name",
        common_norm=False,
        fill=True,
        alpha=0.25,
        palette="tab10",
        linewidth=2,
        ax=ax,
    )

    # Add threshold lines
    ax.axvline(PASS_SCORE_THRESHOLD, color="#d9534f", linestyle="--", linewidth=2, label="Pass Threshold (145)")
    ax.axvline(COLLEGE_READY_SCORE_THRESHOLD, color="#5cb85c", linestyle=":", linewidth=2, label="College Ready (165)")

    ax.set_title("Score Density Distributions by Exam Subject", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Exam Score (Scale: 100–200)", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.legend(title="Subject & Milestones", loc="upper right")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_persona_profiles(persona_summary: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Plots comparative performance metric profiles across the 4 candidate personas."""
    set_visual_style()
    summary = persona_summary.copy()

    # Scale score to 0-1 range for unified comparison with percentage rates
    summary["Normalized Score (Score/160)"] = summary["avg_score"] / 160.0
    summary["Credential Rate"] = summary["credential_earned"]
    summary["Pass Rate"] = summary["pass_rate"]

    melted = summary.melt(
        id_vars="Persona",
        value_vars=["Normalized Score (Score/160)", "Credential Rate", "Pass Rate"],
        var_name="Metric",
        value_name="Value",
    )

    fig, ax = plt.subplots(figsize=(13, 7))
    sns.barplot(
        data=melted,
        x="Persona",
        y="Value",
        hue="Metric",
        palette="Set2",
        ax=ax,
    )

    ax.set_title("Candidate Persona Performance Profiles", fontsize=15, fontweight="bold", pad=15)
    ax.set_ylabel("Normalized Metric Value", fontsize=12)
    ax.set_xlabel("")
    ax.set_ylim(0, 1.15)
    ax.legend(title="Performance Indicator", loc="upper right")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_persona_distribution(persona_summary: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Plots a donut chart showing the national candidate distribution across personas."""
    set_visual_style()
    fig, ax = plt.subplots(figsize=(9, 9))

    colors = [PERSONA_COLORS.get(name, "#888888") for name in persona_summary["Persona"]]

    wedges, texts, autotexts = ax.pie(
        persona_summary["Count"],
        labels=persona_summary["Persona"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        pctdistance=0.80,
        textprops={"fontsize": 11, "fontweight": "medium"},
    )

    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight("bold")
        autotext.set_color("white")

    # Center circle for donut aesthetic
    centre_circle = plt.Circle((0, 0), 0.62, fc="white")
    ax.add_artist(centre_circle)

    ax.set_title("National Candidate Persona Segmentation", fontsize=15, fontweight="bold", pad=20)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_persona_gap_analysis(cand_df: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Plots gap analysis comparing Solid Performers vs. Developing Learners."""
    set_visual_style()
    gap_data = cand_df[cand_df["Persona"].isin(["Solid Performers", "Developing Learners"])].copy()

    gap_summary = gap_data.groupby("Persona").agg(
        n_passed=("n_passed_exams", "mean"),
        used_ready=("used_ged_ready", "mean"),
        has_prep=("has_prep_center", "mean"),
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(11, 6))

    # Bar chart for exams passed
    sns.barplot(
        data=gap_summary,
        x="Persona",
        y="n_passed",
        palette=["#e27d60", "#c38d9e"],
        ax=ax1,
        alpha=0.85,
    )
    ax1.set_ylabel("Avg Subjects Passed (0–4)", color="#2b5c8f", fontsize=12, fontweight="bold")
    ax1.set_xlabel("")
    ax1.set_ylim(0, 4)

    # Secondary line for prep engagement
    ax2 = ax1.twinx()
    melted_prep = gap_summary.melt(
        id_vars="Persona",
        value_vars=["used_ready", "has_prep"],
        var_name="Tool",
        value_name="Rate",
    )
    tool_names = {"used_ready": "GED Ready Usage", "has_prep": "Prep Center Usage"}
    melted_prep["Tool"] = melted_prep["Tool"].map(tool_names)

    sns.lineplot(
        data=melted_prep,
        x="Persona",
        y="Rate",
        hue="Tool",
        marker="o",
        markersize=10,
        linewidth=3,
        palette=["#2b5c8f", "#3e8e7e"],
        ax=ax2,
    )
    ax2.set_ylabel("Tool Engagement Rate (0–1)", color="#e27d60", fontsize=12, fontweight="bold")
    ax2.set_ylim(0, 1.15)
    ax2.grid(False)

    plt.title("Gap Analysis: The Support-Outcome Disconnect (Solid vs. Developing)", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_resource_impact(resource_df: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Plots completion rate by preparation resource used."""
    set_visual_style()
    fig, ax = plt.subplots(figsize=(12, 7))

    res_df = resource_df.sort_values("Used_Completion_Rate", ascending=True)

    bars = ax.barh(res_df["Resource"], res_df["Used_Completion_Rate"], color="#3e8e7e", alpha=0.85)

    ax.set_title("GED Completion Rate by Study Resource Utilized", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("Completion Rate", fontsize=12)
    ax.set_xlim(0, 0.65)

    for bar, (_, row) in zip(bars, res_df.iterrows()):
        width = bar.get_width()
        ax.text(
            width + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1%} (n={int(row['Sample_Size'])})",
            va="center",
            fontsize=9,
            fontweight="semibold",
        )

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_simpsons_paradox(state_metrics_df: pd.DataFrame, save_path: Optional[Union[str, Path]] = None) -> None:
    """Visualizes Simpson's Paradox: Prep Coverage vs Completion Rate by Census Region."""
    set_visual_style()
    plot_df = state_metrics_df.dropna(subset=["prep_coverage", "completion_rate", "census_region"]).copy()

    g = sns.lmplot(
        data=plot_df,
        x="prep_coverage",
        y="completion_rate",
        hue="census_region",
        palette="Set2",
        height=6,
        aspect=1.3,
        scatter_kws={"s": 80, "alpha": 0.7},
    )

    # Global dashed regression line
    sns.regplot(
        data=plot_df,
        x="prep_coverage",
        y="completion_rate",
        scatter=False,
        color="black",
        line_kws={"linestyle": "--", "label": "Global Aggregate Trend"},
        ax=g.ax,
    )

    g.ax.set_title("Simpson's Paradox in Resource Impact\nRegional Slopes vs. Global Aggregate Trend", fontsize=14, fontweight="bold", pad=15)
    g.ax.set_xlabel("State Prep Center Coverage Rate", fontsize=11)
    g.ax.set_ylabel("State Completion Rate", fontsize=11)
    g.ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Census Region")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.close()


def plot_test_method_comparison(
    method_df: pd.DataFrame,
    regional_pct_df: pd.DataFrame,
    save_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Plots online vs physical test center completion rates and regional adoption."""
    set_visual_style()
    out_dir = Path(save_dir) if save_dir else VISUALS_DIR

    # 1. Overall Completion by Method
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = sns.barplot(data=method_df, x="test_method", y="completion_rate", palette="mako", ax=ax)
    ax.set_title("Completion Rate: Online (OnVUE) vs. Physical Test Center", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Completion Rate", fontsize=11)
    ax.set_xlabel("")
    ax.set_ylim(0, 0.6)

    for p in bars.patches:
        height = p.get_height()
        ax.annotate(f"{height:.1%}", (p.get_x() + p.get_width() / 2.0, height + 0.01), ha="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plt.savefig(out_dir / "test_method_overall.png")
    plt.close()


def plot_regional_breakdowns(region_agg: pd.DataFrame, save_dir: Optional[Union[str, Path]] = None) -> None:
    """Generates regional breakdown charts for center density, prep coverage, and completion."""
    set_visual_style()
    out_dir = Path(save_dir) if save_dir else VISUALS_DIR

    metrics = [
        ("center_density", "Average Center Density by Census Region", "Avg Centers per Candidate", "regional_density.png"),
        ("prep_coverage", "Average Prep Coverage by Census Region", "Prep Coverage Rate", "regional_prep.png"),
        ("completion_rate", "Average Completion Rate by Census Region", "Completion Rate", "regional_completion.png"),
        ("enrollment_rate", "Average Enrollment Rate by Census Region", "Enrollment Rate", "regional_enrollment.png"),
    ]

    for col, title, ylabel, filename in metrics:
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.barplot(data=region_agg, x="census_region", y=col, palette="viridis", ax=ax)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_xlabel("Census Region", fontsize=11)
        plt.tight_layout()
        plt.savefig(out_dir / filename)
        plt.close()


def generate_state_choropleth(
    state_df: pd.DataFrame,
    metric_col: str,
    title: str,
    filename: str,
    save_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Generates an interactive Plotly US state choropleth map and exports PNG."""
    if not PLOTLY_AVAILABLE:
        print(f"[INFO] Plotly not available, skipping map generation for {filename}")
        return

    out_dir = Path(save_dir) if save_dir else VISUALS_DIR
    fig = px.choropleth(
        state_df,
        locations="C_STATE",
        locationmode="USA-states",
        color=metric_col,
        scope="usa",
        title=title,
        color_continuous_scale="Viridis",
        labels={metric_col: metric_col.replace("_", " ").title()},
    )
    fig.update_layout(
        title={"font": {"size": 16, "family": "Arial, sans-serif"}, "x": 0.5, "xanchor": "center"},
        margin={"r": 10, "t": 40, "l": 10, "b": 10},
    )

    try:
        fig.write_image(str(out_dir / filename))
    except Exception as e:
        # If kaleido is not installed, save HTML version as fallback
        html_filename = filename.replace(".png", ".html")
        fig.write_html(str(out_dir / html_filename))
        print(f"[INFO] Saved interactive HTML map: {html_filename} ({e})")
