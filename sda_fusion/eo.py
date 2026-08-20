"""EO pipeline demonstration.

This is not orbital-anomaly validation. NDVI has no physical coupling to
TLE eccentricity or maneuvers. The module exists to show a third modality
can be ingested without leaking GEE types into the rest of the package.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .providers import earthengine as ee_provider


@dataclass(frozen=True)
class NdviDemoResult:
    region_name: str
    period_a: ee_provider.NdviPeriodStats
    period_b: ee_provider.NdviPeriodStats
    delta: float
    source: str
    caveat: str


SEASONAL_CAVEAT = (
    "August vs March NDVI is dominated by the ordinary seasonal cycle. "
    "A decrease here is not evidence about YAOGAN-9 or any TLE flag."
)


def run_ndvi_demo(
    *,
    project: str | None = None,
    region_name: str = "Jinju",
    west: float = 127.8,
    south: float = 34.8,
    east: float = 129.5,
    north: float = 36.0,
    start_a: str = "2024-08-01",
    end_a: str = "2024-08-31",
    start_b: str = "2025-03-01",
    end_b: str = "2025-03-31",
    offline: bool = False,
) -> NdviDemoResult:
    if offline:
        # Deterministic stand-in so the rest of the repo can run without GEE.
        period_a = ee_provider.NdviPeriodStats(start_a, end_a, 4, 0.42)
        period_b = ee_provider.NdviPeriodStats(start_b, end_b, 3, 0.18)
        source = "offline-synthetic"
    else:
        ee_provider.initialize(project)
        period_a = ee_provider.period_mean_ndvi(
            west=west, south=south, east=east, north=north, start=start_a, end=end_a
        )
        period_b = ee_provider.period_mean_ndvi(
            west=west, south=south, east=east, north=north, start=start_b, end=end_b
        )
        source = "earth-engine-landsat-c2"

    return NdviDemoResult(
        region_name=region_name,
        period_a=period_a,
        period_b=period_b,
        delta=period_b.mean_ndvi - period_a.mean_ndvi,
        source=source,
        caveat=SEASONAL_CAVEAT,
    )


def synthetic_ndvi_grid(mean: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    grid = mean + 0.08 * rng.normal(size=(128, 128))
    return np.clip(grid, -1.0, 1.0)
