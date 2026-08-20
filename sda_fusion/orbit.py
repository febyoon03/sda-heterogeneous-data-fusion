"""Keplerian helpers derived from a TLE.

Altitude and mean motion are the same Keplerian degree of freedom.
Callers that build ML feature vectors must not treat them as independent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import (
    EARTH_RADIUS_MEAN_KM,
    EARTH_RADIUS_WGS84_KM,
    MU_EARTH_KM3_S2,
    SECONDS_PER_DAY,
)
from .tle import TwoLineElement


@dataclass(frozen=True)
class OrbitElements:
    norad_id: int
    name: str
    inclination_deg: float
    eccentricity: float
    mean_motion_rev_per_day: float
    semi_major_axis_km: float
    mean_altitude_km: float
    perigee_altitude_km: float
    apogee_altitude_km: float

    @property
    def is_leo_mean_alt(self) -> bool:
        from .constants import LEO_ALT_MAX_KM, LEO_ALT_MIN_KM

        return LEO_ALT_MIN_KM < self.mean_altitude_km < LEO_ALT_MAX_KM


def mean_motion_to_sma_km(mean_motion_rev_per_day: float) -> float:
    if mean_motion_rev_per_day <= 0:
        raise ValueError("mean motion must be positive")
    n_rad_s = mean_motion_rev_per_day * 2.0 * math.pi / SECONDS_PER_DAY
    return (MU_EARTH_KM3_S2 / n_rad_s**2) ** (1.0 / 3.0)


def elements_from_tle(
    tle: TwoLineElement, *, earth_radius_km: float = EARTH_RADIUS_MEAN_KM
) -> OrbitElements:
    sma = mean_motion_to_sma_km(tle.mean_motion_rev_per_day)
    e = tle.eccentricity
    if not 0.0 <= e < 1.0:
        raise ValueError(f"eccentricity out of range: {e}")
    return OrbitElements(
        norad_id=tle.norad_id,
        name=tle.name,
        inclination_deg=tle.inclination_deg,
        eccentricity=e,
        mean_motion_rev_per_day=tle.mean_motion_rev_per_day,
        semi_major_axis_km=sma,
        mean_altitude_km=sma - earth_radius_km,
        perigee_altitude_km=sma * (1.0 - e) - earth_radius_km,
        apogee_altitude_km=sma * (1.0 + e) - earth_radius_km,
    )


def wgs84_altitudes(tle: TwoLineElement) -> tuple[float, float, float]:
    """Return (mean, perigee, apogee) using the WGS-84 equatorial radius."""
    el = elements_from_tle(tle, earth_radius_km=EARTH_RADIUS_WGS84_KM)
    return el.mean_altitude_km, el.perigee_altitude_km, el.apogee_altitude_km
