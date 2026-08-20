"""Flag unusual TLE-derived orbits.

This is unsupervised outlier *flagging*, not detection of maneuvers.
Altitude is a deterministic function of mean motion, so the feature
vector does not include both.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .constants import (
    DEFAULT_CONTAMINATION,
    LEO_ALT_MAX_KM,
    LEO_ALT_MIN_KM,
    ZSCORE_THRESHOLD,
)
from .orbit import elements_from_tle
from .tle import TwoLineElement

# Independent-enough Keplerian descriptors. Mean motion is omitted because
# it is 1-1 with semi-major axis / mean altitude.
FEATURE_COLUMNS = ("mean_altitude_km", "inclination_deg", "eccentricity")


@dataclass(frozen=True)
class AnomalyResult:
    catalog: pd.DataFrame
    single_by_feature: dict[str, set[int]]
    union: set[int]
    fusion: set[int]
    fusion_only: set[int]
    contamination: float
    z_threshold: float

    @property
    def n_leo(self) -> int:
        return len(self.catalog)


def catalog_to_frame(tles: list[TwoLineElement]) -> pd.DataFrame:
    rows = []
    for tle in tles:
        try:
            el = elements_from_tle(tle)
        except ValueError:
            continue
        if not (LEO_ALT_MIN_KM < el.mean_altitude_km < LEO_ALT_MAX_KM):
            continue
        rows.append(
            {
                "name": el.name,
                "norad_id": el.norad_id,
                "mean_altitude_km": el.mean_altitude_km,
                "perigee_altitude_km": el.perigee_altitude_km,
                "apogee_altitude_km": el.apogee_altitude_km,
                "inclination_deg": el.inclination_deg,
                "eccentricity": el.eccentricity,
                "mean_motion_rev_per_day": el.mean_motion_rev_per_day,
                "tle_line1": tle.line1,
                "tle_line2": tle.line2,
            }
        )
    if not rows:
        raise ValueError("no LEO objects after TLE parse / altitude filter")
    return pd.DataFrame(rows).drop_duplicates("norad_id").reset_index(drop=True)


def _z_outlier_indices(series: pd.Series, threshold: float) -> set[int]:
    std = series.std(ddof=1)
    if std == 0 or np.isnan(std):
        return set()
    z = (series - series.mean()) / std
    return set(series.index[z.abs() > threshold])


def flag_anomalies(
    tles: list[TwoLineElement],
    *,
    contamination: float = DEFAULT_CONTAMINATION,
    z_threshold: float = ZSCORE_THRESHOLD,
    random_state: int = 42,
) -> AnomalyResult:
    if not 0.0 < contamination < 0.5:
        raise ValueError("contamination must be in (0, 0.5)")

    df = catalog_to_frame(tles)
    single = {col: _z_outlier_indices(df[col], z_threshold) for col in FEATURE_COLUMNS}
    union = set.union(*single.values()) if single else set()

    scaler = StandardScaler()
    x = scaler.fit_transform(df.loc[:, list(FEATURE_COLUMNS)])
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )
    pred = model.fit_predict(x)
    scores = -model.score_samples(x)
    df = df.copy()
    df["fusion_flag"] = pred == -1
    df["fusion_score"] = scores
    # The 95th percentile line on the score histogram is a *display* threshold
    # for the plot; IsolationForest already used `contamination`.
    df["score_quantile_95"] = df["fusion_score"].quantile(0.95)

    fusion = set(df.index[df["fusion_flag"]])
    return AnomalyResult(
        catalog=df,
        single_by_feature=single,
        union=union,
        fusion=fusion,
        fusion_only=fusion - union,
        contamination=contamination,
        z_threshold=z_threshold,
    )


def summarize(result: AnomalyResult) -> dict:
    df = result.catalog
    return {
        "n_leo": result.n_leo,
        "contamination_assumption": result.contamination,
        "z_threshold": result.z_threshold,
        "single_counts": {k: len(v) for k, v in result.single_by_feature.items()},
        "single_union": len(result.union),
        "fusion_count": len(result.fusion),
        "fusion_fraction": len(result.fusion) / result.n_leo,
        "fusion_only": len(result.fusion_only),
        "jaccard_union_vs_fusion": (
            len(result.union & result.fusion) / len(result.union | result.fusion)
            if result.union or result.fusion
            else 0.0
        ),
        "top10": df.loc[df["fusion_flag"]]
        .nlargest(10, "fusion_score")[
            [
                "name",
                "norad_id",
                "mean_altitude_km",
                "inclination_deg",
                "eccentricity",
                "fusion_score",
            ]
        ]
        .to_dict(orient="records"),
    }
