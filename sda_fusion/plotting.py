"""Figures. Titles state what was actually computed."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from .anomaly import FEATURE_COLUMNS, AnomalyResult
from .eo import NdviDemoResult, synthetic_ndvi_grid
from .ground_track import GroundTrack
from .sgp4_validate import Sgp4Comparison
from .visibility import VisibilityStudy


def plot_anomaly(result: AnomalyResult, path: Path) -> Path:
    df = result.catalog
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Orbital outlier flagging — marginal z-score vs IsolationForest\n"
        f"LEO catalog N={result.n_leo}; contamination={result.contamination:.2f} is an input",
        fontsize=12,
        fontweight="bold",
    )
    normal = df[~df["fusion_flag"]]
    flagged = df[df["fusion_flag"]]

    ax = axes[0]
    ax.scatter(
        normal["mean_altitude_km"],
        normal["eccentricity"] * 1000,
        c="#90CAF9",
        alpha=0.35,
        s=10,
        label=f"Not flagged (n={len(normal)})",
    )
    ax.scatter(
        flagged["mean_altitude_km"],
        flagged["eccentricity"] * 1000,
        c="#F44336",
        alpha=0.9,
        s=50,
        marker="D",
        zorder=5,
        label=f"IsolationForest flag (n={len(flagged)})",
    )
    ax.set_xlabel("Mean altitude (km)")
    ax.set_ylabel("Eccentricity (x10^-3)")
    ax.set_title("(a) Altitude vs. eccentricity", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    ax2 = axes[1]
    labels = [c.split("_")[0][:4] for c in FEATURE_COLUMNS] + ["Union", "IF"]
    values = [len(result.single_by_feature[c]) for c in FEATURE_COLUMNS] + [
        len(result.union),
        len(result.fusion),
    ]
    colors = ["#90CAF9"] * len(FEATURE_COLUMNS) + ["#FFB74D", "#F44336"]
    bars = ax2.bar(labels, values, color=colors, edgecolor="white", width=0.6)
    ax2.bar_label(bars, fontsize=10, fontweight="bold", padding=3)
    ax2.set_ylabel("Flagged objects")
    ax2.set_title("(b) Flag counts (not detections)", fontweight="bold")
    ax2.set_ylim(0, max(values) * 1.2 if values else 1)
    ax2.grid(alpha=0.2, axis="y")
    ax2.legend(
        handles=[
            mpatches.Patch(color="#90CAF9", label=f"|z|>{result.z_threshold}"),
            mpatches.Patch(color="#FFB74D", label="z-score union"),
            mpatches.Patch(color="#F44336", label="IsolationForest"),
        ],
        fontsize=8,
    )

    ax3 = axes[2]
    ax3.hist(normal["fusion_score"], bins=40, color="#2196F3", alpha=0.6, density=True, label="Not flagged")
    ax3.hist(flagged["fusion_score"], bins=20, color="#F44336", alpha=0.85, density=True, label="Flagged")
    thresh = df["fusion_score"].quantile(1.0 - result.contamination)
    ax3.axvline(thresh, color="black", ls="--", lw=1.5, label=f"contamination cut ≈ {thresh:.3f}")
    ax3.set_xlabel("IsolationForest anomaly score")
    ax3.set_ylabel("Density")
    ax3.set_title("(c) Score distribution", fontweight="bold")
    ax3.legend(fontsize=8)
    ax3.grid(alpha=0.25)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_sgp4(comparison: Sgp4Comparison, path: Path, normal_max_km: float) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    status = "comparable" if comparison.comparable else "NOT comparable"
    fig.suptitle(
        f"SGP4 position difference at t0+24h ({status})\n"
        f"{comparison.t0.name}  error={comparison.error_km:.2f} km",
        fontsize=12,
        fontweight="bold",
    )
    x = np.arange(3)
    axes[0].bar(x - 0.2, comparison.predicted_km, 0.4, color="#2196F3", label="Propagated t0")
    axes[0].bar(x + 0.2, comparison.actual_km, 0.4, color="#F44336", label="Reference TLE")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(["X (km)", "Y (km)", "Z (km)"])
    axes[0].set_title("(a) Position at evaluation time", fontweight="bold")
    axes[0].legend()
    axes[0].grid(alpha=0.3, axis="y")

    color = "#4CAF50" if comparison.within_normal else "#F44336"
    axes[1].bar(
        ["Policy max", "This comparison"],
        [normal_max_km, comparison.error_km],
        color=["#4CAF50", color],
        width=0.4,
    )
    axes[1].set_title("(b) Error vs. 5 km policy threshold", fontweight="bold")
    axes[1].grid(alpha=0.3, axis="y")
    if not comparison.comparable:
        axes[1].text(
            0.5,
            0.9,
            "Epoch window failed\n— do not interpret",
            transform=axes[1].transAxes,
            ha="center",
            color="#B71C1C",
            fontweight="bold",
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_visibility(study: VisibilityStudy, path: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        f"OWL-Net optical visibility windows ({study.duration_hours}h)\n"
        "Observable-time ratio — not a detection probability. No RF data.",
        fontsize=12,
        fontweight="bold",
    )
    names = [s.station.name.replace("OWL-Net ", "") for s in study.per_station]
    horizon_pct = [s.observable_ratio_of_horizon * 100 for s in study.per_station]
    weather_pct = [
        s.observable_ratio_of_horizon * 100 * study.weather_clear_fraction
        for s in study.per_station
    ]
    x = np.arange(len(names))
    axes[0].bar(x - 0.2, horizon_pct, 0.4, color="#2196F3", label="Sunlit ∩ night ∩ elev.")
    axes[0].bar(x + 0.2, weather_pct, 0.4, color="#90CAF9", label=f"× weather {study.weather_clear_fraction:.0%}")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(names, rotation=20, ha="right")
    axes[0].set_ylabel("% of geometric above-horizon time")
    axes[0].set_title("(a) Per-station optical window", fontweight="bold")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3, axis="y")

    optical_passes = [s.n_optical_passes for s in study.per_station]
    axes[1].bar(names, optical_passes, color="#4CAF50", width=0.5)
    axes[1].set_title("(b) Distinct optical passes", fontweight="bold")
    axes[1].set_ylabel("Pass count")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(alpha=0.3, axis="y")

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_ground_track(track: GroundTrack, path: Path, region: dict) -> Path:
    fig, ax = plt.subplots(figsize=(14, 7))
    scatter = ax.scatter(
        track.points["lon"],
        track.points["lat"],
        c=track.points["minute"],
        cmap="plasma",
        s=8,
        alpha=0.7,
        label="Ground track",
    )
    if len(track.region_samples):
        ax.scatter(
            track.region_samples["lon"],
            track.region_samples["lat"],
            c="red",
            s=60,
            zorder=5,
            marker="*",
            label=f"Korea-box samples (n={track.n_region_samples}, passes={track.n_passes})",
        )
    rect = plt.Rectangle(
        (region["lon_min"], region["lat_min"]),
        region["lon_max"] - region["lon_min"],
        region["lat_max"] - region["lat_min"],
        linewidth=2,
        edgecolor="red",
        facecolor="red",
        alpha=0.1,
        label="Korean Peninsula box",
    )
    ax.add_patch(rect)
    fig.colorbar(scatter, ax=ax, label="Minutes from TLE epoch")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title(
        f"{track.tle.name} ground track from epoch {track.tle.epoch:%Y-%m-%d %H:%M UTC}",
        fontweight="bold",
    )
    ax.set_xlim(-180, 180)
    ax.set_ylim(-70, 70)
    ax.axhline(0, color="gray", lw=0.5, alpha=0.5)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9, loc="lower left")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_ndvi(result: NdviDemoResult, path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        f"Landsat NDVI pipeline demo — {result.region_name} ({result.source})\n"
        "Not a cross-validation of the TLE anomaly flag",
        fontsize=12,
        fontweight="bold",
    )
    a = synthetic_ndvi_grid(result.period_a.mean_ndvi, 1)
    b = synthetic_ndvi_grid(result.period_b.mean_ndvi, 2)
    change = b - a
    for ax, img, title in (
        (axes[0], a, f"(a) {result.period_a.start}\nmean={result.period_a.mean_ndvi:.4f}"),
        (axes[1], b, f"(b) {result.period_b.start}\nmean={result.period_b.mean_ndvi:.4f}"),
        (axes[2], change, f"(c) ΔNDVI={result.delta:.4f}"),
    ):
        cmap = "RdYlGn" if ax is not axes[2] else "RdBu"
        im = ax.imshow(img, cmap=cmap, vmin=-0.3 if ax is axes[2] else -0.2, vmax=0.3 if ax is axes[2] else 0.8)
        ax.set_title(title, fontweight="bold")
        ax.axis("off")
        fig.colorbar(im, ax=ax, fraction=0.046)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
