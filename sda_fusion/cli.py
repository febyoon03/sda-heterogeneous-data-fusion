"""Command-line entry points."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import PipelineConfig, run_anomaly_stage, run_case_study, run_eo_stage, run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sda-fusion")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_anom = sub.add_parser("anomaly", help="flag LEO TLE outliers")
    p_anom.add_argument("--catalog", required=True)
    p_anom.add_argument("--out", default="outputs")

    p_case = sub.add_parser("case-study", help="SGP4 + ground track + OWL-Net")
    p_case.add_argument("--out", default="outputs")
    p_case.add_argument("--stations", default="korea")
    p_case.add_argument("--skip-visibility", action="store_true")

    p_eo = sub.add_parser("eo", help="NDVI pipeline demo")
    p_eo.add_argument("--out", default="outputs")
    p_eo.add_argument("--offline", action="store_true", default=True)
    p_eo.add_argument("--live", action="store_true")
    p_eo.add_argument("--project", default=None)

    p_all = sub.add_parser("pipeline", help="run every stage that has inputs")
    p_all.add_argument("--catalog", default=None)
    p_all.add_argument("--out", default="outputs")
    p_all.add_argument("--stations", default="korea")
    p_all.add_argument("--skip-visibility", action="store_true")
    p_all.add_argument("--live-ee", action="store_true")
    p_all.add_argument("--project", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    out = Path(args.out)
    if args.cmd == "anomaly":
        run_anomaly_stage(Path(args.catalog), out)
    elif args.cmd == "case-study":
        run_case_study(out, station_set=args.stations, skip_visibility=args.skip_visibility)
    elif args.cmd == "eo":
        run_eo_stage(out, offline=not args.live, project=args.project)
    elif args.cmd == "pipeline":
        run_pipeline(
            PipelineConfig(
                catalog_path=Path(args.catalog) if args.catalog else None,
                output_dir=out,
                station_set=args.stations,
                eo_offline=not args.live_ee,
                ee_project=args.project,
                skip_visibility=args.skip_visibility,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
