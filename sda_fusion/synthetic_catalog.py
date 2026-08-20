"""Build a tiny but checksum-valid LEO catalog for offline tests."""

from __future__ import annotations

from .tle import TwoLineElement, tle_checksum


def _checksum_line(body68: str) -> str:
    if len(body68) != 68:
        raise ValueError(f"TLE body must be 68 chars, got {len(body68)}")
    return body68 + str(tle_checksum(body68 + "0"))


def make_tle(
    *,
    name: str,
    norad: int,
    inclination: float,
    eccentricity: float,
    mean_motion: float,
    epoch: str = "26074.71646067",
) -> TwoLineElement:
    ecc_digits = f"{eccentricity:.7f}".split(".")[1][:7]
    line1_body = (
        f"1 {norad:05d}U 00000A   {epoch}  .00000000  00000-0  00000-0 0  999"
    )
    line2_body = (
        f"2 {norad:05d} {inclination:8.4f} 000.0000 {ecc_digits}  000.0000 000.0000 "
        f"{mean_motion:11.8f}"
    )
    # Mean-motion field is 11 chars; pad/trim to keep line2 at 68 before checksum.
    line2_body = (line2_body + " " * 68)[:68]
    line1_body = (line1_body + " " * 68)[:68]
    return TwoLineElement.from_lines(
        _checksum_line(line1_body), _checksum_line(line2_body), name=name
    )


def demo_catalog() -> list[TwoLineElement]:
    """~60 LEO-like objects plus YAOGAN-9 and a few designed-odd orbits."""
    from .constants import YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2

    tles = [
        TwoLineElement.from_lines(YAOGAN9_TLE_T0_L1, YAOGAN9_TLE_T0_L2, "YAOGAN-9 01A")
    ]
    # Cluster of typical SSO-ish LEO
    for i in range(40):
        tles.append(
            make_tle(
                name=f"SSO-{i:02d}",
                norad=50000 + i,
                inclination=97.4 + (i % 5) * 0.2,
                eccentricity=0.0010 + (i % 7) * 0.0002,
                mean_motion=15.20 - (i % 9) * 0.04,
            )
        )
    # Cluster of mid-inclination circular
    for i in range(15):
        tles.append(
            make_tle(
                name=f"MID-{i:02d}",
                norad=51000 + i,
                inclination=53.0 + (i % 4) * 0.3,
                eccentricity=0.0008 + (i % 5) * 0.0001,
                mean_motion=15.05 - (i % 6) * 0.03,
            )
        )
    # Designed-unusual (should be easy IF flags)
    tles.append(
        make_tle(
            name="HIGH-ECC-DESIGNED",
            norad=52001,
            inclination=63.4,
            eccentricity=0.25,
            mean_motion=13.4,
        )
    )
    tles.append(
        make_tle(
            name="VERY-LOW-LEO",
            norad=52002,
            inclination=51.6,
            eccentricity=0.0012,
            mean_motion=16.1,
        )
    )
    return tles


def write_demo_catalog(path: str) -> int:
    tles = demo_catalog()
    with open(path, "w", encoding="utf-8") as handle:
        for tle in tles:
            handle.write(f"{tle.name}\n{tle.line1}\n{tle.line2}\n")
    return len(tles)
