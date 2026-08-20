"""OWL-Net site catalog.

The original script placed Mt. Lemmon in south-east Korea and listed
Sobaeksan as an OWL-Net site. Both are wrong. OWL-Net is a *global*
0.5 m network (Korea, Mongolia, Morocco, Israel, USA).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpticalStation:
    key: str
    name: str
    country: str
    latitude_deg: float
    longitude_deg: float
    elevation_m: float
    mpc_code: str | None = None
    notes: str = ""


# Coordinates from published OWL-Net papers / MPC observatory list.
OWLNET_STATIONS: tuple[OpticalStation, ...] = (
    OpticalStation(
        key="bohyun",
        name="OWL-Net Mt. Bohyun",
        country="Korea",
        latitude_deg=36.163884,
        longitude_deg=128.97595,
        elevation_m=1169.0,
        mpc_code="P72",
    ),
    OpticalStation(
        key="daedeok",
        name="OWL-Net Daedeok (test-bed)",
        country="Korea",
        latitude_deg=36.397627,
        longitude_deg=127.37568,
        elevation_m=161.0,
        mpc_code="P65",
        notes="Headquarters / test-bed, not a dark-sky remote site.",
    ),
    OpticalStation(
        key="songino",
        name="OWL-Net Songino",
        country="Mongolia",
        latitude_deg=47.886134,
        longitude_deg=106.33476,
        elevation_m=1638.0,
        mpc_code="O72",
    ),
    OpticalStation(
        key="lemmon",
        name="OWL-Net Mt. Lemmon",
        country="USA",
        latitude_deg=32.442,
        longitude_deg=-110.789,
        elevation_m=2791.0,
        mpc_code="V15",
        notes="Arizona. The original script placed this near Busan.",
    ),
    OpticalStation(
        key="wise",
        name="OWL-Net Wise / Mitzpe Ramon",
        country="Israel",
        latitude_deg=30.5958,
        longitude_deg=34.7620,
        elevation_m=875.0,
        mpc_code="M33",
    ),
    OpticalStation(
        key="oukaimeden",
        name="OWL-Net Oukaimeden",
        country="Morocco",
        latitude_deg=31.206,
        longitude_deg=-7.866,
        elevation_m=2700.0,
        mpc_code=None,
    ),
)

# What the original script *intended* to study: Korea-based observability.
KOREA_OWLNET = tuple(s for s in OWLNET_STATIONS if s.country == "Korea")


def get_stations(selection: str = "korea") -> tuple[OpticalStation, ...]:
    key = selection.lower()
    if key in {"korea", "korean"}:
        return KOREA_OWLNET
    if key in {"all", "global", "owlnet"}:
        return OWLNET_STATIONS
    wanted = {part.strip() for part in key.split(",")}
    found = tuple(s for s in OWLNET_STATIONS if s.key in wanted)
    if not found:
        raise KeyError(f"unknown station selection: {selection}")
    return found
