from sda_fusion.anomaly import FEATURE_COLUMNS, flag_anomalies
from sda_fusion.synthetic_catalog import demo_catalog


def test_feature_vector_does_not_include_mean_motion():
    assert "mean_motion_rev_per_day" not in FEATURE_COLUMNS
    assert "mean_altitude_km" in FEATURE_COLUMNS


def test_flagging_on_demo_catalog():
    result = flag_anomalies(demo_catalog(), contamination=0.05)
    assert result.n_leo >= 50
    # contamination is an input: flagged fraction should be near it
    frac = len(result.fusion) / result.n_leo
    assert 0.01 <= frac <= 0.15
    names = set(result.catalog.loc[list(result.fusion), "name"])
    assert "HIGH-ECC-DESIGNED" in names
    yaogan = result.catalog[result.catalog["norad_id"] == 36413]
    assert len(yaogan) == 1


def test_empty_std_does_not_crash():
    from sda_fusion.synthetic_catalog import make_tle

    clones = [
        make_tle(
            name=f"C{i}",
            norad=60000 + i,
            inclination=51.6,
            eccentricity=0.001,
            mean_motion=15.5,
        )
        for i in range(12)
    ]
    result = flag_anomalies(clones, contamination=0.1)
    assert result.n_leo == 12
