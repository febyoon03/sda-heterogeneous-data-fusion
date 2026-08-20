#!/usr/bin/env python3
"""SGP4 comparison + OWL-Net visibility. Logic is in sda_fusion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sda_fusion.pipeline import run_case_study


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "outputs"))
    parser.add_argument("--stations", default="korea")
    parser.add_argument("--skip-visibility", action="store_true")
    args = parser.parse_args()
    payload = run_case_study(
        Path(args.out), station_set=args.stations, skip_visibility=args.skip_visibility
    )
    sgp4 = payload["sgp4"]
    print(f"SGP4 comparable={sgp4['comparable']} error_km={sgp4['error_km']:.3f}")
    print(sgp4["reason"])
    if payload["visibility"]:
        for row in payload["visibility"]:
            print(
                f"{row['station']}: optical_min={row['optical_minutes']} "
                f"passes={row['n_optical_passes']} "
                f"ratio={row['observable_ratio_of_horizon']:.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
