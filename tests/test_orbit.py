from sda_fusion.constants import YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2
from sda_fusion.orbit import elements_from_tle
from sda_fusion.tle import TwoLineElement


def test_yaogan9_mean_altitude_matches_known_value():
    tle = TwoLineElement.from_lines(YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2, "Y9")
    el = elements_from_tle(tle)
    assert abs(el.mean_altitude_km - 1095.32) < 0.05
    assert 690 < el.perigee_altitude_km < 710
    assert 1480 < el.apogee_altitude_km < 1500
    assert el.apogee_altitude_km - el.perigee_altitude_km > 700
