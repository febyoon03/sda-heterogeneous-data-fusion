"""Google Earth Engine adapter.

The rest of the pipeline must not import `ee`. If Earth Engine is missing
or unauthenticated, callers use the offline demo instead.
"""

from __future__ import annotations

from dataclasses import dataclass


class EarthEngineUnavailable(RuntimeError):
    pass


LANDSAT8 = "LANDSAT/LC08/C02/T1_L2"
LANDSAT9 = "LANDSAT/LC09/C02/T1_L2"
SR_SCALE = 0.0000275
SR_OFFSET = -0.2


@dataclass(frozen=True)
class NdviPeriodStats:
    start: str
    end: str
    n_images: int
    mean_ndvi: float


def _require_ee():
    try:
        import ee  # type: ignore
    except ImportError as exc:
        raise EarthEngineUnavailable(
            "earthengine-api is not installed"
        ) from exc
    return ee


def initialize(project: str | None) -> None:
    ee = _require_ee()
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as exc:  # auth failures are environment-specific
        raise EarthEngineUnavailable(str(exc)) from exc


def _mask_and_scale(image):
    """Apply C2 SR scale/offset and a basic QA_PIXEL cloud/shadow mask."""
    ee = _require_ee()
    optical = (
        image.select(["SR_B4", "SR_B5"]).multiply(SR_SCALE).add(SR_OFFSET)
    )
    qa = image.select("QA_PIXEL")
    # Bits 3 (cloud) and 4 (cloud shadow) must be 0.
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    ndvi = optical.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
    return ndvi.updateMask(mask).updateMask(ndvi.gte(-1).And(ndvi.lte(1)))


def period_mean_ndvi(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    start: str,
    end: str,
    cloud_cover_max: float = 20.0,
) -> NdviPeriodStats:
    ee = _require_ee()
    region = ee.Geometry.Rectangle([west, south, east, north])
    l8 = (
        ee.ImageCollection(LANDSAT8)
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_cover_max))
    )
    l9 = (
        ee.ImageCollection(LANDSAT9)
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_cover_max))
    )
    col = ee.ImageCollection(l8.merge(l9)).map(_mask_and_scale)
    n = int(col.size().getInfo())
    if n == 0:
        raise EarthEngineUnavailable(f"no Landsat scenes for {start}..{end}")
    mean = (
        col.median()
        .reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=30,
            maxPixels=1_000_000_000,
        )
        .getInfo()
    )
    value = mean.get("NDVI")
    if value is None:
        raise EarthEngineUnavailable("NDVI reduceRegion returned null")
    return NdviPeriodStats(
        start=start, end=end, n_images=n, mean_ndvi=float(value)
    )
