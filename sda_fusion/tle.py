"""TLE parse, checksum, and catalog-line walking.

Responsibility: turn text into TwoLineElement objects. No Skyfield, no
plots, no anomaly policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Iterator


class TleError(ValueError):
    """Malformed TLE text or checksum."""


def tle_checksum(line: str) -> int:
    """NORAD checksum: sum of digits plus 1 for each '-', mod 10."""
    total = 0
    for char in line[:68]:
        if char.isdigit():
            total += int(char)
        elif char == "-":
            total += 1
    return total % 10


def validate_tle_line(line: str, expected_prefix: str) -> str:
    line = line.rstrip("\n\r")
    if len(line) < 69:
        line = line.ljust(69)
    if not line.startswith(expected_prefix):
        raise TleError(f"TLE line must start with {expected_prefix!r}: {line!r}")
    given = line[68]
    if not given.isdigit():
        raise TleError(f"Missing checksum digit: {line!r}")
    expected = tle_checksum(line)
    if int(given) != expected:
        raise TleError(
            f"TLE checksum mismatch (got {given}, expected {expected}): {line}"
        )
    return line[:69]


def parse_tle_epoch(line1: str) -> datetime:
    """Parse TLE epoch (YYDDD.frac) to an aware UTC datetime."""
    yy = int(line1[18:20])
    year = 1900 + yy if yy >= 57 else 2000 + yy
    day_of_year = float(line1[20:32])
    # day 1.0 = January 1 00:00
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1.0)


@dataclass(frozen=True)
class TwoLineElement:
    name: str
    line1: str
    line2: str

    @property
    def norad_id(self) -> int:
        return int(self.line1[2:7])

    @property
    def epoch(self) -> datetime:
        return parse_tle_epoch(self.line1)

    @property
    def inclination_deg(self) -> float:
        return float(self.line2[8:16])

    @property
    def eccentricity(self) -> float:
        return float("0." + self.line2[26:33])

    @property
    def mean_motion_rev_per_day(self) -> float:
        return float(self.line2[52:63])

    @classmethod
    def from_lines(
        cls, line1: str, line2: str, name: str = "", *, check: bool = True
    ) -> "TwoLineElement":
        if check:
            line1 = validate_tle_line(line1, "1")
            line2 = validate_tle_line(line2, "2")
        else:
            line1 = line1.rstrip()
            line2 = line2.rstrip()
        return cls(name=name.strip() or f"NORAD-{int(line1[2:7])}", line1=line1, line2=line2)


def iter_tles(lines: Iterable[str], *, check: bool = True) -> Iterator[TwoLineElement]:
    """Accept 2LE or 3LE catalogs. Skip records that fail checksum/parse."""
    buf: list[str] = []
    pending_name = "UNKNOWN"
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("1 "):
            buf = [line]
        elif line.startswith("2 ") and buf:
            try:
                yield TwoLineElement.from_lines(
                    buf[0], line, name=pending_name, check=check
                )
            except (TleError, ValueError):
                pass
            buf = []
            pending_name = "UNKNOWN"
        else:
            pending_name = line
            buf = []


def parse_catalog_text(text: str, *, check: bool = True) -> list[TwoLineElement]:
    return list(iter_tles(text.splitlines(), check=check))


def load_catalog(path: str, *, check: bool = True) -> list[TwoLineElement]:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return list(iter_tles(handle, check=check))
