#!/usr/bin/env python3
"""Thin experiment wrapper. Logic lives in sda_fusion.anomaly."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sda_fusion.pipeline import run_anomaly_stage
from sda_fusion.synthetic_catalog import write_demo_catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "outputs"))
    args = parser.parse_args()
    catalog = Path(args.catalog) if args.catalog else ROOT / "data" / "fixtures" / "demo_catalog.tle"
    if not catalog.exists():
        catalog.parent.mkdir(parents=True, exist_ok=True)
        write_demo_catalog(str(catalog))
        print(f"wrote demo catalog: {catalog}")
    run_anomaly_stage(catalog, Path(args.out))
    print(f"wrote outputs under {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
