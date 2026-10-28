import pytest
from amusement_park_ride_access import process_ride_admissions, inspect_safety_restraints


def make_group(ride_type="family", patrons=None, is_open=True, fast_lane=False):
    return {
        "is_open": is_open,
        "ride_type": ride_type,
        "has_fast_lane": fast_lane,
        "patrons": patrons if patrons is not None else [],
    }


def adult(height=150, warning=False):
    return {"height_cm": height, "health_warning": warning, "is_child": False}


def child(height=130, warning=False):
    return {"height_cm": height, "health_warning": warning, "is_child": True}


# ---------- process_ride_admissions ----------

def test_single_adult_family_ride():
    groups = [
        {
            "is_open": True,
            "ride_type": "family",
            "has_fast_lane": False,
            "patrons": [{"height_cm": 150, "health_warning": False, "is_child": False}]
        }
    ]
    result = process_ride_admissions(groups, 5.0)
    assert result["total_revenue"] == 10.0
    assert result["status"] == "COMPLETED"


def test_groups_not_a_list_raises():
    with pytest.raises(ValueError):
        process_ride_admissions("not a list", 5.0)


def test_negative_fee_raises():
    with pytest.raises(ValueError):
        process_ride_admissions([], -1.0)


def test_closed_group_is_skipped():
    result = process_ride_admissions([make_group(patrons=[adult()], is_open=False)], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_roller_coaster_adult():
    result = process_ride_admissions([make_group("roller_coaster", [adult()])], 5.0)
    assert result == {"total_revenue": 25.0, "status": "COMPLETED"}


def test_water_ride_adult():
    result = process_ride_admissions([make_group("water_ride", [adult()])], 5.0)
    assert result == {"total_revenue": 18.0, "status": "COMPLETED"}


def test_child_pays_sixty_percent():
    result = process_ride_admissions([make_group("family", [child()])], 5.0)
    assert result == {"total_revenue": 6.0, "status": "COMPLETED"}


def test_unknown_ride_type_rejected():
    result = process_ride_admissions([make_group("bumper_cars", [adult()])], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_zero_height_patron_rejected():
    result = process_ride_admissions([make_group("family", [adult(height=0)])], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_health_warning_on_family_ride_skips_patron_only():
    patrons = [adult(), adult(warning=True)]
    result = process_ride_admissions([make_group("family", patrons)], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


def test_health_warning_on_roller_coaster_cancels_group_revenue():
    patrons = [adult(), adult(warning=True), adult()]
    result = process_ride_admissions([make_group("roller_coaster", patrons, fast_lane=True)], 5.0)
    # group total is wiped, then only the fast-lane fee is added
    assert result == {"total_revenue": 5.0, "status": "COMPLETED"}


def test_too_short_patron_rejected():
    result = process_ride_admissions([make_group("family", [adult(height=119)])], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_fast_lane_adds_fee():
    result = process_ride_admissions([make_group("family", [adult()], fast_lane=True)], 5.0)
    assert result == {"total_revenue": 15.0, "status": "COMPLETED"}


def test_safety_audit_when_more_than_four_rejected():
    patrons = [adult(height=100)] * 5 + [adult()]
    result = process_ride_admissions([make_group("family", patrons)], 5.0)
    assert result == {"total_revenue": 10.0, "status": "SAFETY_AUDIT"}


# ---------- inspect_safety_restraints ----------

def test_restraints_empty_returns_no_data():
    assert inspect_safety_restraints([]) == "NO_DATA"


def test_restraints_two_unlatched_in_a_row_locks():
    assert inspect_safety_restraints([[1, 0, 0]]) == "EMERGENCY_LOCK"


def test_restraints_all_latched_is_safe():
    assert inspect_safety_restraints([[1, 1, 1], [1, 1]]) == "SAFE"


def test_restraints_streak_resets_after_latch():
    assert inspect_safety_restraints([[0, 1, 0, 1]]) == "SAFE"
