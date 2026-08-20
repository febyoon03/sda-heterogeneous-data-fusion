from sda_fusion.pipeline import case_study_near, case_study_t0
from sda_fusion.sgp4_validate import compare_propagation


def test_epoch_window_rejects_week_old_reference():
    comparison = compare_propagation(case_study_t0(), case_study_near(), horizon_hours=24.0)
    # near TLE is ~6 days before t0, evaluation is t0+24h → not comparable
    assert comparison.error_km >= 0
    assert comparison.comparable is False
    assert comparison.within_normal is False
    assert "outside" in comparison.reason.lower()


def test_same_tle_is_comparable_at_zero_horizon():
    t0 = case_study_t0()
    comparison = compare_propagation(t0, t0, horizon_hours=0.0, epoch_window_hours=1.0)
    assert comparison.comparable is True
    assert comparison.error_km < 1e-6
