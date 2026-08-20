from sda_fusion.constants import YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2
from sda_fusion.tle import TwoLineElement, parse_catalog_text, tle_checksum, validate_tle_line


def test_checksum_matches_published_yaogan9():
    assert tle_checksum(YAOGAN9_TLE_T0_L1) == int(YAOGAN9_TLE_T0_L1[-1])
    assert tle_checksum(YAOGAN9_TLE_T0_L2) == int(YAOGAN9_TLE_T0_L2[-1])
    validate_tle_line(YAOGAN9_TLE_T0_L1, "1")
    validate_tle_line(YAOGAN9_TLE_T0_L2, "2")


def test_epoch_and_fields():
    tle = TwoLineElement.from_lines(YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2, "YAOGAN-9 01A")
    assert tle.norad_id == 36413
    assert abs(tle.eccentricity - 0.0529596) < 1e-9
    assert abs(tle.inclination_deg - 63.3646) < 1e-6
    assert tle.epoch.year == 2026
    assert tle.epoch.month == 3
    assert tle.epoch.day == 15


def test_3le_and_2le_catalog():
    text = "\n".join(
        [
            "YAOGAN-9 01A",
            YAOGAN9_TLE_T0_L1,
            YAOGAN9_TLE_T0_L2,
            YAOGAN9_TLE_T0_L1,
            YAOGAN9_TLE_T0_L2,
        ]
    )
    tles = parse_catalog_text(text)
    assert len(tles) == 2
    assert tles[0].name == "YAOGAN-9 01A"
    assert tles[1].norad_id == 36413


def test_bad_checksum_is_skipped():
    bad = YAOGAN9_TLE_T0_L1[:-1] + "0"
    text = f"BAD\n{bad}\n{YAOGAN9_TLE_T0_L2}\n"
    assert parse_catalog_text(text) == []
