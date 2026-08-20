import numpy as np

from sda_fusion.ground_track import _count_runs, compute_ground_track
from sda_fusion.pipeline import case_study_t0
from sda_fusion.stations import get_stations


def test_pass_count_is_runs_not_samples():
    mask = np.array([0, 1, 1, 1, 0, 1, 1, 0, 0], dtype=bool)
    assert _count_runs(mask) == 2


def test_korea_box_finds_at_least_one_sample():
    track = compute_ground_track(case_study_t0(), duration_hours=24, step_minutes=1)
    assert track.n_region_samples >= 1
    assert track.n_passes >= 1
    assert track.n_passes <= track.n_region_samples


def test_owlnet_korea_does_not_include_arizona():
    korea = get_stations("korea")
    assert {s.key for s in korea} == {"bohyun", "daedeok"}
    lemmon = [s for s in get_stations("all") if s.key == "lemmon"][0]
    assert lemmon.longitude_deg < 0
    assert lemmon.country == "USA"
