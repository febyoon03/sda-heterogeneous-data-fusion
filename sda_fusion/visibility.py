"""Experiment B: optical visibility windows.

Reports observable-time *ratios*, not detection probabilities.
RF/fusion multipliers are not computed here — they are not measured.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from skyfield.api import EarthSatellite, load, wgs84

from .constants import (
    ASTRONOMICAL_NIGHT_SUN_ALT_DEG,
    ELEVATION_MASK_DEG,
    WEATHER_CLEAR_FRACTION,
)
from .stations import OpticalStation
from .tle import TwoLineElement


@dataclass(frozen=True)
class StationVisibility:
    station: OpticalStation
    duration_minutes: int
    above_horizon_minutes: int
    optical_minutes: int
    weather_adjusted_minutes: float
    observable_ratio_of_horizon: float
    observable_ratio_of_window: float
    n_horizon_passes: int
    n_optical_passes: int


@dataclass(frozen=True)
class VisibilityStudy:
    tle: TwoLineElement
    duration_hours: int
    elevation_mask_deg: float
    sun_alt_max_deg: float
    weather_clear_fraction: float
    per_station: list[StationVisibility]


def _count_runs(mask: np.ndarray) -> int:
    if mask.size == 0:
        return 0
    padded = np.concatenate(([False], mask.astype(bool), [False]))
    return int(np.sum((~padded[:-1]) & padded[1:]))


def analyze_visibility(
    tle: TwoLineElement,
    stations: tuple[OpticalStation, ...] | list[OpticalStation],
    *,
    duration_hours: int = 72,
    step_minutes: int = 1,
    elevation_mask_deg: float = ELEVATION_MASK_DEG,
    sun_alt_max_deg: float = ASTRONOMICAL_NIGHT_SUN_ALT_DEG,
    weather_clear_fraction: float = WEATHER_CLEAR_FRACTION,
    eph=None,
) -> VisibilityStudy:
    if duration_hours <= 0 or step_minutes <= 0:
        raise ValueError("duration and step must be positive")
    if not 0.0 <= weather_clear_fraction <= 1.0:
        raise ValueError("weather_clear_fraction must be in [0, 1]")

    ts = load.timescale()
    if eph is None:
        eph = load("de421.bsp")
    sun = eph["sun"]
    earth = eph["earth"]
    sat = EarthSatellite(tle.line1, tle.line2, tle.name, ts)

    minutes = np.arange(0, duration_hours * 60, step_minutes)
    times = ts.from_datetimes(
        [tle.epoch + timedelta(minutes=float(m)) for m in minutes]
    )

    is_sunlit = sat.at(times).is_sunlit(eph)
    results: list[StationVisibility] = []

    for station in stations:
        topo = wgs84.latlon(
            station.latitude_deg,
            station.longitude_deg,
            elevation_m=station.elevation_m,
        )
        alt, _az, _dist = (sat - topo).at(times).altaz()
        above = alt.degrees > elevation_mask_deg
        observer = earth + topo
        sun_alt, _az2, _d2 = observer.at(times).observe(sun).apparent().altaz()
        night = sun_alt.degrees < sun_alt_max_deg
        optical = above & is_sunlit & night

        above_min = int(np.sum(above))
        optical_min = int(np.sum(optical))
        weather_min = optical_min * weather_clear_fraction
        horizon_ratio = (optical_min / above_min) if above_min else 0.0
        window_ratio = optical_min / len(minutes) if len(minutes) else 0.0

        results.append(
            StationVisibility(
                station=station,
                duration_minutes=int(len(minutes)),
                above_horizon_minutes=above_min,
                optical_minutes=optical_min,
                weather_adjusted_minutes=weather_min,
                observable_ratio_of_horizon=horizon_ratio,
                observable_ratio_of_window=window_ratio,
                n_horizon_passes=_count_runs(above),
                n_optical_passes=_count_runs(optical),
            )
        )

    return VisibilityStudy(
        tle=tle,
        duration_hours=duration_hours,
        elevation_mask_deg=elevation_mask_deg,
        sun_alt_max_deg=sun_alt_max_deg,
        weather_clear_fraction=weather_clear_fraction,
        per_station=results,
    )
