"""Ground-track sampling and peninsula-pass detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd
from skyfield.api import EarthSatellite, load, wgs84

from .constants import KOREA_BOX
from .tle import TwoLineElement


@dataclass(frozen=True)
class GroundTrack:
    tle: TwoLineElement
    points: pd.DataFrame
    region_samples: pd.DataFrame
    n_passes: int
    n_region_samples: int


def _count_runs(mask: np.ndarray) -> int:
    if mask.size == 0:
        return 0
    padded = np.concatenate(([False], mask.astype(bool), [False]))
    return int(np.sum((~padded[:-1]) & padded[1:]))


def compute_ground_track(
    tle: TwoLineElement,
    *,
    duration_hours: int = 24,
    step_minutes: int = 1,
    region: dict | None = None,
) -> GroundTrack:
    region = region or KOREA_BOX
    ts = load.timescale()
    sat = EarthSatellite(tle.line1, tle.line2, tle.name, ts)
    minutes = np.arange(0, duration_hours * 60, step_minutes)
    times = ts.from_datetimes(
        [tle.epoch + timedelta(minutes=float(m)) for m in minutes]
    )
    sub = wgs84.subpoint(sat.at(times))
    df = pd.DataFrame(
        {
            "lat": sub.latitude.degrees,
            "lon": sub.longitude.degrees,
            "minute": minutes,
        }
    )
    inside = (
        (df["lat"] > region["lat_min"])
        & (df["lat"] < region["lat_max"])
        & (df["lon"] > region["lon_min"])
        & (df["lon"] < region["lon_max"])
    )
    return GroundTrack(
        tle=tle,
        points=df,
        region_samples=df.loc[inside].copy(),
        n_passes=int(_count_runs(inside.to_numpy())),
        n_region_samples=int(inside.sum()),
    )
