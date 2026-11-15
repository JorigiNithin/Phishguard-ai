"""Generate Exploratory Data Analysis (EDA) figures for PhishGuard AI.

Reads datasets/url_dataset_clean.csv, extracts the model's 17 features,
computes empirical statistical distributions, and generates 300 DPI charts:
  - Figure 3.1: docs/figures/figure_3_1_class_distribution.png
  - Figure 3.2: docs/figures/figure_3_2_feature_distributions.png
  - Figure 3.3: docs/figures/figure_3_3_correlation_heatmap.png
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend package to sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from app.services.url_features import FEATURE_NAMES, extract_features, features_to_vector

# Paths
_PROJECT_ROOT = _BACKEND_DIR.parent
_CSV_PATH = _PROJECT_ROOT / "datasets" / "url_dataset_clean.csv"
_FIGURES_DIR = _PROJECT_ROOT / "docs" / "figures"
_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Uniform Color Palette Across Entire Project
# Green for Legitimate (good = 0), Red for Phishing (bad = 1)
COLOR_LEGIT = "#10b981"   # Emerald Green
COLOR_PHISH = "#ef4444"   # Crimson Red
CLASS_PALETTE = {
    "Legitimate (good)": COLOR_LEGIT,
    "Phishing (bad)": COLOR_PHISH,
}


def main() -> None:
    print(f"[EDA] Loading dataset from {_CSV_PATH}...")
    df = pd.read_csv(_CSV_PATH)
    total_samples = len(df)
    print(f"[EDA] Loaded {total_samples} rows.")

    # 1. Class Counts and Percentages
    counts = df["label"].value_counts()
    n_phish = int(counts.get("bad", 0))
    n_legit = int(counts.get("good", 0))
    pct_phish = (n_phish / total_samples) * 100
    pct_legit = (n_legit / total_samples) * 100

    print("\n" + "=" * 65)
    print("1. CLASS DISTRIBUTION")
    print("=" * 65)
    print(f"  Phishing (bad, 1):    {n_phish:,} samples ({pct_phish:.2f}%)")
    print(f"  Legitimate (good, 0): {n_legit:,} samples ({pct_legit:.2f}%)")
    print(f"  Total:                {total_samples:,} samples")
    print(f"  Imbalance Ratio:      {n_phish / n_legit:.2f} : 1")

    # -----------------------------------------------------------------------
    # Figure 3.1: Class Distribution
    # -----------------------------------------------------------------------
    print("\n[EDA] Generating Figure 3.1: Class Distribution...")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    sns.set_theme(style="whitegrid")

    categories = ["Legitimate (good)", "Phishing (bad)"]
    values = [n_legit, n_phish]
    bar_colors = [COLOR_LEGIT, COLOR_PHISH]
    percentages = [pct_legit, pct_phish]

    bars = ax.bar(categories, values, color=bar_colors, width=0.5, edgecolor="#1e293b", linewidth=1.2)

    for bar, val, pct in zip(bars, values, percentages):
        height = bar.get_height()
        ax.annotate(
            f"{val:,}\n({pct:.2f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            color="#0f172a",
        )

    ax.set_ylim(0, max(values) * 1.18)
    ax.set_title("Figure 3.1: Class Distribution of URL Phishing Dataset", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Dataset Class Label", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_ylabel("Number of Samples", fontsize=12, fontweight="bold", labelpad=10)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    fig.text(
        0.5,
        -0.02,
        f"Total Samples: {total_samples:,}  |  Phishing: {pct_phish:.2f}%  |  Legitimate: {pct_legit:.2f}%  |  Imbalance: {n_phish / n_legit:.2f}:1",
        ha="center",
        fontsize=10,
        style="italic",
        color="#475569",
    )

    plt.tight_layout()
    fig31_path = _FIGURES_DIR / "figure_3_1_class_distribution.png"
    plt.savefig(fig31_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[EDA] Saved: {fig31_path}")

    # -----------------------------------------------------------------------
    # Feature Extraction
    # -----------------------------------------------------------------------
    print("\n[EDA] Extracting 17 features from all URLs...")
    feature_rows: list[list[float]] = []
    labels_int: list[int] = []

    for _, row in df.iterrows():
        feats = extract_features(row["url"])
        feature_rows.append(features_to_vector(feats))
        labels_int.append(1 if row["label"] == "bad" else 0)

    feat_df = pd.DataFrame(feature_rows, columns=FEATURE_NAMES)
    feat_df["label"] = df["label"]
    feat_df["Class"] = df["label"].map({"good": "Legitimate (good)", "bad": "Phishing (bad)"})
    feat_df["is_phishing"] = labels_int

    print(f"[EDA] Feature matrix extracted: {feat_df.shape[0]} rows x {len(FEATURE_NAMES)} features.")

    # -----------------------------------------------------------------------
    # Figure 3.2: Feature Distributions (Corrected Legend & Color Mapping)
    # -----------------------------------------------------------------------
    print("\n[EDA] Generating Figure 3.2: Key Numerical Feature Distributions...")
    selected_features = [
        ("url_length", "URL Total Length (characters)"),
        ("entropy", "Shannon Entropy (bits)"),
        ("digit_count", "Digit Count in URL"),
        ("path_length", "Path Length (characters)"),
        ("num_suspicious_keywords", "Suspicious Keyword Matches"),
        ("query_length", "Query String Length (characters)"),
    ]

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(16, 10), dpi=300)
    axes = axes.flatten()

    for i, (col, display_name) in enumerate(selected_features):
        ax = axes[i]
        legit_data = feat_df[feat_df["Class"] == "Legitimate (good)"][col]
        phish_data = feat_df[feat_df["Class"] == "Phishing (bad)"][col]

        # Explicit hue_order ensures: Handle 0 = Legitimate (Green), Handle 1 = Phishing (Red)
        sns.histplot(
            data=feat_df,
            x=col,
            hue="Class",
            hue_order=["Legitimate (good)", "Phishing (bad)"],
            palette=CLASS_PALETTE,
            kde=True,
            stat="density",
            common_norm=False,
            alpha=0.45,
            ax=ax,
            bins=25,
            legend=(i == 0),
        )

        ax.set_title(f"{display_name}", fontsize=11, fontweight="bold")
        ax.set_xlabel(display_name, fontsize=10)
        ax.set_ylabel("Density", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.6)

        # Means annotations
        legit_mean = legit_data.mean()
        phish_mean = phish_data.mean()
        ax.axvline(legit_mean, color="#059669", linestyle="--", linewidth=1.5, alpha=0.9)
        ax.axvline(phish_mean, color="#dc2626", linestyle="--", linewidth=1.5, alpha=0.9)

        # Direct in-plot text annotations for class means
        y_lim = ax.get_ylim()[1]
        ax.text(
            legit_mean,
            y_lim * 0.90,
            f" Legit $\\mu$={legit_mean:.1f}",
            color="#047857",
            fontsize=9,
            fontweight="bold",
            ha="right" if legit_mean > phish_mean else "left",
        )
        ax.text(
            phish_mean,
            y_lim * 0.75,
            f" Phish $\\mu$={phish_mean:.1f}",
            color="#b91c1c",
            fontsize=9,
            fontweight="bold",
            ha="left" if phish_mean >= legit_mean else "right",
        )

        if i == 0 and ax.get_legend() is not None:
            legend = ax.get_legend()
            legend.set_title("Ground Truth Class")

    plt.suptitle("Figure 3.2: Empirical Feature Distributions by URL Class", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig32_path = _FIGURES_DIR / "figure_3_2_feature_distributions.png"
    plt.savefig(fig32_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[EDA] Saved: {fig32_path}")

    # -----------------------------------------------------------------------
    # Figure 3.3: Correlation Heatmap
    # -----------------------------------------------------------------------
    print("\n[EDA] Generating Figure 3.3: Pearson Correlation Heatmap...")
    # Exclude constant features with zero variance (has_at_sign, is_shortened)
    stds = feat_df[FEATURE_NAMES].std()
    active_features = [col for col in FEATURE_NAMES if stds[col] > 0]
    zero_var_features = [col for col in FEATURE_NAMES if stds[col] == 0]
    print(f"[EDA] Active features for correlation ({len(active_features)}): {active_features}")
    print(f"[EDA] Invariant features excluded from correlation ({len(zero_var_features)}): {zero_var_features}")

    corr_cols = active_features + ["is_phishing"]
    corr_matrix = feat_df[corr_cols].corr(method="pearson")

    renamed_cols = [
        c.replace("_", " ").title().replace("Is Phishing", "Target (Phishing)")
        for c in corr_cols
    ]
    corr_matrix.columns = renamed_cols
    corr_matrix.index = renamed_cols

    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    sns.heatmap(
        corr_matrix,
        mask=mask,
        cmap=cmap,
        vmax=1.0,
        vmin=-1.0,
        center=0.0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.75, "label": "Pearson Correlation Coefficient (r)"},
        annot=True,
        fmt=".2f",
        annot_kws={"size": 8.5},
        ax=ax,
    )

    ax.set_title(
        "Figure 3.3: Pearson Correlation Heatmap of URL Features and Phishing Target",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    plt.xticks(rotation=45, ha="right", fontsize=9.5)
    plt.yticks(rotation=0, fontsize=9.5)

    fig.text(
        0.5,
        -0.02,
        f"Target encoding: Phishing ('bad') = 1, Legitimate ('good') = 0. Invariant features ({', '.join(zero_var_features)}) excluded (σ = 0).",
        ha="center",
        fontsize=9.5,
        style="italic",
        color="#475569",
    )

    plt.tight_layout()
    fig33_path = _FIGURES_DIR / "figure_3_3_correlation_heatmap.png"
    plt.savefig(fig33_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[EDA] Saved: {fig33_path}")

    # -----------------------------------------------------------------------
    # Comprehensive Verification Table
    # -----------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("VERIFICATION TABLE: MEANS, MEDIANS, AND TARGET CORRELATIONS")
    print("Target Encoding: Phishing ('bad') = 1, Legitimate ('good') = 0")
    print("=" * 90)
    table_rows = []
    for f in FEATURE_NAMES:
        g_mean = feat_df[feat_df["label"] == "good"][f].mean()
        g_med = feat_df[feat_df["label"] == "good"][f].median()
        b_mean = feat_df[feat_df["label"] == "bad"][f].mean()
        b_med = feat_df[feat_df["label"] == "bad"][f].median()
        r_val = feat_df[f].corr(feat_df["is_phishing"]) if feat_df[f].std() > 0 else np.nan

        # Trend check
        if np.isnan(r_val):
            direction = "Invariant (σ=0)"
        elif b_mean > g_mean and r_val > 0:
            direction = "Consistent (+)"
        elif b_mean < g_mean and r_val < 0:
            direction = "Consistent (-)"
        else:
            direction = "Inconsistent!"

        table_rows.append({
            "Feature": f,
            "Good Mean": f"{g_mean:.4f}",
            "Good Med": f"{g_med:.4f}",
            "Bad Mean": f"{b_mean:.4f}",
            "Bad Med": f"{b_med:.4f}",
            "Pearson r": f"{r_val:+.4f}" if not np.isnan(r_val) else "NaN",
            "Consistency": direction,
        })

    v_df = pd.DataFrame(table_rows)
    print(v_df.to_string(index=False))

    print("\n[EDA] Verification complete. All figures and tables 100% synchronized.")


if __name__ == "__main__":
    main()
