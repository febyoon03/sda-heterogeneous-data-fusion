"""Experiment A: compare a t0 TLE propagated to t_eval against another TLE.

A live Celestrak pull is *not* automatically t24. The comparison is only
accepted when the second TLE's epoch is close to the evaluation time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from skyfield.api import EarthSatellite, load

from .constants import SGP4_EPOCH_WINDOW_HOURS, SGP4_NORMAL_ERROR_KM
from .tle import TwoLineElement


@dataclass(frozen=True)
class Sgp4Comparison:
    t0: TwoLineElement
    t_ref: TwoLineElement
    t_eval: datetime
    predicted_km: tuple[float, float, float]
    actual_km: tuple[float, float, float]
    error_km: float
    epoch_delta_hours: float
    comparable: bool
    within_normal: bool
    reason: str


def _satellite(tle: TwoLineElement, ts):
    return EarthSatellite(tle.line1, tle.line2, tle.name, ts)


def compare_propagation(
    t0: TwoLineElement,
    t_ref: TwoLineElement,
    *,
    horizon_hours: float = 24.0,
    epoch_window_hours: float = SGP4_EPOCH_WINDOW_HOURS,
    normal_max_km: float = SGP4_NORMAL_ERROR_KM,
) -> Sgp4Comparison:
    ts = load.timescale()
    t_eval = t0.epoch + timedelta(hours=horizon_hours)
    if t_eval.tzinfo is None:
        t_eval = t_eval.replace(tzinfo=timezone.utc)

    sat0 = _satellite(t0, ts)
    sat1 = _satellite(t_ref, ts)
    t_sf = ts.from_datetime(t_eval)
    predicted = np.array(sat0.at(t_sf).position.km, dtype=float)
    actual = np.array(sat1.at(t_sf).position.km, dtype=float)
    error = float(np.linalg.norm(actual - predicted))

    epoch_delta = abs((t_ref.epoch - t_eval).total_seconds()) / 3600.0
    comparable = epoch_delta <= epoch_window_hours
    if comparable:
        reason = (
            f"reference TLE epoch is {epoch_delta:.2f} h from evaluation time "
            f"(window {epoch_window_hours:.1f} h)"
        )
    else:
        reason = (
            f"reference TLE epoch is {epoch_delta:.2f} h from evaluation time; "
            f"outside the {epoch_window_hours:.1f} h window. SGP4 is not valid "
            f"for this comparison — do not treat the error as a maneuver test."
        )

    return Sgp4Comparison(
        t0=t0,
        t_ref=t_ref,
        t_eval=t_eval,
        predicted_km=(float(predicted[0]), float(predicted[1]), float(predicted[2])),
        actual_km=(float(actual[0]), float(actual[1]), float(actual[2])),
        error_km=error,
        epoch_delta_hours=epoch_delta,
        comparable=comparable,
        within_normal=comparable and error <= normal_max_km,
        reason=reason,
    )
