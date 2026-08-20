"""Orchestration: candidate list → case study → optional EO demo.

Modules talk through dataclasses and files, not by importing each other's
script-level globals.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .anomaly import AnomalyResult, flag_anomalies, summarize
from .constants import (
    KOREA_BOX,
    SGP4_NORMAL_ERROR_KM,
    YAOGAN9_NORAD,
    YAOGAN9_TLE_NEAR_L1,
    YAOGAN9_TLE_NEAR_L2,
    YAOGAN9_TLE_T0_L1,
    YAOGAN9_TLE_T0_L2,
)
from .eo import run_ndvi_demo
from .ground_track import compute_ground_track
from .plotting import (
    plot_anomaly,
    plot_ground_track,
    plot_ndvi,
    plot_sgp4,
    plot_visibility,
)
from .sgp4_validate import compare_propagation
from .stations import get_stations
from .tle import TwoLineElement, load_catalog
from .visibility import analyze_visibility


@dataclass(frozen=True)
class PipelineConfig:
    catalog_path: Path | None
    output_dir: Path
    station_set: str = "korea"
    eo_offline: bool = True
    ee_project: str | None = None
    skip_visibility: bool = False


def case_study_t0() -> TwoLineElement:
    return TwoLineElement.from_lines(YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2, "YAOGAN-9 01A")


def case_study_near() -> TwoLineElement:
    return TwoLineElement.from_lines(YAOGAN9_TLE_NEAR_L1, YAOGAN9_TLE_NEAR_L2, "YAOGAN-9 01A")


def run_anomaly_stage(catalog_path: Path, output_dir: Path) -> AnomalyResult:
    tles = load_catalog(str(catalog_path))
    result = flag_anomalies(tles)
    output_dir.mkdir(parents=True, exist_ok=True)
    flagged = result.catalog.loc[result.catalog["fusion_flag"]].copy()
    flagged_path = output_dir / "anomaly_candidates.csv"
    flagged.to_csv(flagged_path, index=False)
    (output_dir / "anomaly_summary.json").write_text(
        json.dumps(summarize(result), indent=2, default=str), encoding="utf-8"
    )
    plot_anomaly(result, output_dir / "anomaly_detection_fusion.png")
    return result


def run_case_study(output_dir: Path, *, station_set: str, skip_visibility: bool) -> dict:
    t0 = case_study_t0()
    near = case_study_near()
    comparison = compare_propagation(t0, near, horizon_hours=24.0)
    plot_sgp4(comparison, output_dir / "fig3_experiment_A_sgp4.png", SGP4_NORMAL_ERROR_KM)

    track = compute_ground_track(t0)
    plot_ground_track(track, output_dir / "yaogan9_ground_track.png", KOREA_BOX)

    vis_summary = None
    if not skip_visibility:
        study = analyze_visibility(t0, get_stations(station_set))
        plot_visibility(study, output_dir / "fig4_experiment_B_owlnet.png")
        vis_summary = [
            {
                "station": s.station.name,
                "country": s.station.country,
                "above_horizon_minutes": s.above_horizon_minutes,
                "optical_minutes": s.optical_minutes,
                "weather_adjusted_minutes": s.weather_adjusted_minutes,
                "observable_ratio_of_horizon": s.observable_ratio_of_horizon,
                "n_optical_passes": s.n_optical_passes,
            }
            for s in study.per_station
        ]

    payload = {
        "norad_id": YAOGAN9_NORAD,
        "t0_epoch": t0.epoch.isoformat(),
        "reference_tle_epoch": near.epoch.isoformat(),
        "sgp4": {
            "error_km": comparison.error_km,
            "comparable": comparison.comparable,
            "within_normal": comparison.within_normal,
            "epoch_delta_hours": comparison.epoch_delta_hours,
            "reason": comparison.reason,
        },
        "ground_track": {
            "n_passes": track.n_passes,
            "n_region_samples": track.n_region_samples,
        },
        "visibility": vis_summary,
    }
    (output_dir / "case_study.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def run_eo_stage(output_dir: Path, *, offline: bool, project: str | None) -> dict:
    result = run_ndvi_demo(project=project, offline=offline)
    plot_ndvi(result, output_dir / "ndvi_analysis_jinju.png")
    payload = {
        "region": result.region_name,
        "source": result.source,
        "period_a": asdict(result.period_a),
        "period_b": asdict(result.period_b),
        "delta": result.delta,
        "caveat": result.caveat,
    }
    (output_dir / "eo_demo.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def run_pipeline(config: PipelineConfig) -> dict:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {}
    if config.catalog_path is not None:
        anomaly = run_anomaly_stage(config.catalog_path, config.output_dir)
        report["anomaly"] = summarize(anomaly)
        in_catalog = anomaly.catalog[anomaly.catalog["norad_id"] == YAOGAN9_NORAD]
        report["yaogan9_in_catalog"] = bool(len(in_catalog))
        if len(in_catalog):
            row = in_catalog.iloc[0]
            report["yaogan9_fusion_flag"] = bool(row["fusion_flag"])
            report["yaogan9_score"] = float(row["fusion_score"])
    report["case_study"] = run_case_study(
        config.output_dir,
        station_set=config.station_set,
        skip_visibility=config.skip_visibility,
    )
    report["eo"] = run_eo_stage(
        config.output_dir, offline=config.eo_offline, project=config.ee_project
    )
    (config.output_dir / "pipeline_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return report
