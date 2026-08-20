"""Celestrak GP download.

Failure mode: network errors return None and let the caller fall back to
bundled fixtures. This module never silently treats "latest TLE" as t24.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from ..constants import CELESTRAK_TLE_URL, CELESTRAK_USER_AGENT
from ..tle import TwoLineElement, parse_catalog_text


class CatalogDownloadError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResult:
    tles: list[TwoLineElement]
    url: str
    raw_text: str


def fetch_tle(
    *,
    norad_id: int | None = None,
    group: str | None = None,
    timeout: float = 20.0,
) -> FetchResult:
    if norad_id is not None:
        params = {"CATNR": str(norad_id), "FORMAT": "tle"}
    elif group is not None:
        params = {"GROUP": group, "FORMAT": "tle"}
    else:
        raise ValueError("provide norad_id or group")

    try:
        response = requests.get(
            CELESTRAK_TLE_URL,
            params=params,
            timeout=timeout,
            headers={"User-Agent": CELESTRAK_USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CatalogDownloadError(str(exc)) from exc

    text = response.text
    if "No GP data found" in text or not text.strip():
        raise CatalogDownloadError(f"Celestrak returned no GP data: {response.url}")
    tles = parse_catalog_text(text, check=True)
    if not tles:
        # Some endpoints omit names; retry without being strict on names.
        tles = parse_catalog_text(text, check=False)
    if not tles:
        raise CatalogDownloadError(f"could not parse TLE from {response.url}")
    return FetchResult(tles=tles, url=response.url, raw_text=text)
