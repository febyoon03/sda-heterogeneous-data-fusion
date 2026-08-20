#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sda_fusion.pipeline import run_eo_stage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "outputs"))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--project", default=None)
    args = parser.parse_args()
    payload = run_eo_stage(Path(args.out), offline=not args.live, project=args.project)
    print(f"source={payload['source']} delta={payload['delta']:.4f}")
    print(payload["caveat"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
