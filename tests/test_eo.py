from sda_fusion.eo import run_ndvi_demo
from sda_fusion.providers.earthengine import SR_OFFSET, SR_SCALE


def test_offline_ndvi_is_seasonal_decrease():
    result = run_ndvi_demo(offline=True)
    assert result.source == "offline-synthetic"
    assert result.delta < 0
    assert "seasonal" in result.caveat.lower()


def test_landsat_c2_scale_constants():
    assert SR_SCALE == 0.0000275
    assert SR_OFFSET == -0.2
