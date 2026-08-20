#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sda_fusion.constants import KOREA_BOX
from sda_fusion.ground_track import compute_ground_track
from sda_fusion.pipeline import case_study_t0
from sda_fusion.plotting import plot_ground_track


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "outputs"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    track = compute_ground_track(case_study_t0())
    path = plot_ground_track(track, out / "yaogan9_ground_track.png", KOREA_BOX)
    print(f"passes={track.n_passes} samples_in_box={track.n_region_samples}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
