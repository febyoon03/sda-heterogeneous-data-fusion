"""Physical constants and analysis policies.

Policies (contamination, elevation mask, weather factor) live here so they
are not buried inside plot titles or print statements.
"""

from __future__ import annotations

# WGS-84 / conventional values used by the original scripts.
MU_EARTH_KM3_S2 = 398600.4418
EARTH_RADIUS_MEAN_KM = 6371.0
EARTH_RADIUS_WGS84_KM = 6378.137
SECONDS_PER_DAY = 86400.0

LEO_ALT_MIN_KM = 200.0
LEO_ALT_MAX_KM = 2000.0

# Optical visibility policy
ELEVATION_MASK_DEG = 10.0
# IAU astronomical night: Sun altitude < -18 deg.
# The original script used -10 deg (between civil and nautical).
ASTRONOMICAL_NIGHT_SUN_ALT_DEG = -18.0
NAUTICAL_NIGHT_SUN_ALT_DEG = -12.0
ORIGINAL_NIGHT_SUN_ALT_DEG = -10.0

# Not a measured weather model. A scenario multiplier applied after geometry.
WEATHER_CLEAR_FRACTION = 0.50

# SGP4 comparison is only meaningful when the comparison TLE epoch is near
# the evaluation time. The original script compared t0+24h against whatever
# TLE Celestrak returned *today*.
SGP4_EPOCH_WINDOW_HOURS = 12.0
SGP4_NORMAL_ERROR_KM = 5.0

# IsolationForest contamination is an *input assumption*, not a measured rate.
DEFAULT_CONTAMINATION = 0.05
ZSCORE_THRESHOLD = 3.0

YAOGAN9_NORAD = 36413
YAOGAN9_NAME = "YAOGAN-9 01A"

# Case-study TLE used in the original presentation (epoch 2026-03-15 17:11 UTC).
YAOGAN9_TLE_T0_L1 = "1 36413U 10009A   26074.71646067 -.00000015  00000+0  54471-4 0  9994"
YAOGAN9_TLE_T0_L2 = "2 36413  63.3646 240.0751 0529596  20.9898 341.2004 13.45683456787391"

# A second published TLE from the same week (epoch 2026-03-09), useful as a
# *near-epoch* comparison fixture. It is NOT 24 hours after t0.
YAOGAN9_TLE_NEAR_L1 = "1 36413U 10009A   26068.47428842  .00000008  00000-0  71208-4 0  9998"
YAOGAN9_TLE_NEAR_L2 = "2 36413  63.3639 256.2258 0529038  20.9470 341.2370 13.45682288786556"

CELESTRAK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php"
CELESTRAK_USER_AGENT = "sda-heterogeneous-data-fusion/2.0 (research; contact via repo)"

KOREA_BOX = {
    "lat_min": 33.0,
    "lat_max": 42.0,
    "lon_min": 124.0,
    "lon_max": 132.0,
}
