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


# ======================================================================
# process_ride_admissions
# ======================================================================

# ---------- input validation: both halves of the `or` ----------

def test_groups_not_a_list_raises():
    with pytest.raises(ValueError):
        process_ride_admissions("not a list", 5.0)


def test_groups_none_raises():
    with pytest.raises(ValueError):
        process_ride_admissions(None, 5.0)


def test_negative_fee_raises():
    with pytest.raises(ValueError):
        process_ride_admissions([], -1.0)


def test_zero_fee_is_valid():
    result = process_ride_admissions([make_group("family", [adult()], fast_lane=True)], 0.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


# ---------- outer loop: zero iterations / skipped groups ----------

def test_empty_group_list():
    assert process_ride_admissions([], 5.0) == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_closed_group_is_skipped():
    result = process_ride_admissions([make_group(patrons=[adult()], is_open=False)], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_missing_is_open_key_treated_as_closed():
    result = process_ride_admissions([{"ride_type": "family", "patrons": [adult()]}], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


# ---------- ride type: every branch of the if/elif/else chain ----------

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


def test_roller_coaster_adult():
    result = process_ride_admissions([make_group("roller_coaster", [adult()])], 5.0)
    assert result == {"total_revenue": 25.0, "status": "COMPLETED"}


def test_water_ride_adult():
    result = process_ride_admissions([make_group("water_ride", [adult()])], 5.0)
    assert result == {"total_revenue": 18.0, "status": "COMPLETED"}


def test_missing_ride_type_defaults_to_family():
    group = {"is_open": True, "patrons": [adult()]}
    result = process_ride_admissions([group], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


def test_unknown_ride_type_rejected():
    result = process_ride_admissions([make_group("bumper_cars", [adult()])], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


# ---------- patron loop: zero iterations ----------

def test_missing_patrons_key():
    result = process_ride_admissions([{"is_open": True, "ride_type": "family"}], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


def test_fast_lane_with_no_patrons_still_charges_fee():
    result = process_ride_admissions([make_group("family", [], fast_lane=True)], 5.0)
    assert result == {"total_revenue": 5.0, "status": "COMPLETED"}


def test_fast_lane_with_no_patrons_and_zero_fee():
    result = process_ride_admissions([make_group("family", [], fast_lane=True)], 0.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


# ---------- height checks: <= 0, < 120, boundary ----------

def test_zero_height_patron_rejected():
    result = process_ride_admissions([make_group("family", [adult(height=0)])], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_negative_height_patron_rejected():
    result = process_ride_admissions([make_group("family", [adult(height=-5)])], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_missing_height_patron_rejected():
    patron = {"health_warning": False, "is_child": False}
    result = process_ride_admissions([make_group("family", [patron])], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_height_119_rejected():
    result = process_ride_admissions([make_group("family", [adult(height=119)])], 5.0)
    assert result["status"] == "ZERO_ADMISSIONS"


def test_height_120_accepted():
    result = process_ride_admissions([make_group("family", [adult(height=120)])], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


# ---------- child pricing ----------

def test_child_family_ride():
    result = process_ride_admissions([make_group("family", [child()])], 5.0)
    assert result == {"total_revenue": 6.0, "status": "COMPLETED"}


def test_child_roller_coaster():
    result = process_ride_admissions([make_group("roller_coaster", [child()])], 5.0)
    assert result == {"total_revenue": 15.0, "status": "COMPLETED"}


def test_child_water_ride():
    result = process_ride_admissions([make_group("water_ride", [child()])], 5.0)
    assert result == {"total_revenue": 10.8, "status": "COMPLETED"}


def test_mixed_adult_and_child():
    result = process_ride_admissions([make_group("family", [adult(), child()])], 5.0)
    assert result == {"total_revenue": 16.0, "status": "COMPLETED"}


# ---------- health warning: roller coaster vs other rides ----------

def test_health_warning_on_family_ride_skips_patron_only():
    patrons = [adult(), adult(warning=True)]
    result = process_ride_admissions([make_group("family", patrons)], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


def test_health_warning_on_water_ride_skips_patron_only():
    patrons = [adult(warning=True), adult()]
    result = process_ride_admissions([make_group("water_ride", patrons)], 5.0)
    assert result == {"total_revenue": 18.0, "status": "COMPLETED"}


def test_health_warning_on_roller_coaster_cancels_group_revenue():
    patrons = [adult(), adult(warning=True), adult()]
    result = process_ride_admissions([make_group("roller_coaster", patrons, fast_lane=True)], 5.0)
    # group total is wiped, the loop breaks, then only the fast-lane fee is added
    assert result == {"total_revenue": 5.0, "status": "COMPLETED"}


def test_health_warning_on_roller_coaster_without_fast_lane():
    patrons = [adult(), adult(warning=True)]
    result = process_ride_admissions([make_group("roller_coaster", patrons)], 5.0)
    assert result == {"total_revenue": 0.0, "status": "ZERO_ADMISSIONS"}


# ---------- fast lane ----------

def test_fast_lane_adds_fee():
    result = process_ride_admissions([make_group("family", [adult()], fast_lane=True)], 5.0)
    assert result == {"total_revenue": 15.0, "status": "COMPLETED"}


def test_no_fast_lane_no_fee():
    result = process_ride_admissions([make_group("family", [adult()], fast_lane=False)], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


# ---------- final status: SAFETY_AUDIT / ZERO_ADMISSIONS / COMPLETED ----------

def test_exactly_four_rejected_is_not_audit():
    patrons = [adult(height=100)] * 4 + [adult()]
    result = process_ride_admissions([make_group("family", patrons)], 5.0)
    assert result == {"total_revenue": 10.0, "status": "COMPLETED"}


def test_five_rejected_triggers_safety_audit():
    patrons = [adult(height=100)] * 5 + [adult()]
    result = process_ride_admissions([make_group("family", patrons)], 5.0)
    assert result == {"total_revenue": 10.0, "status": "SAFETY_AUDIT"}


def test_rejections_accumulate_across_groups():
    groups = [
        make_group("family", [adult(height=100)] * 3),
        make_group("bumper_cars", [adult()]),
        make_group("water_ride", [adult(warning=True)]),
    ]
    result = process_ride_admissions(groups, 5.0)
    assert result == {"total_revenue": 0.0, "status": "SAFETY_AUDIT"}


def test_revenue_is_rounded_to_two_decimals():
    result = process_ride_admissions([make_group("family", [adult()], fast_lane=True)], 0.333)
    assert result == {"total_revenue": 10.33, "status": "COMPLETED"}


def test_multiple_groups_sum_revenue():
    groups = [
        make_group("family", [adult()]),
        make_group("water_ride", [adult()]),
        make_group("roller_coaster", [adult()]),
    ]
    result = process_ride_admissions(groups, 5.0)
    assert result == {"total_revenue": 53.0, "status": "COMPLETED"}


# ======================================================================
# inspect_safety_restraints
# ======================================================================

def test_restraints_empty_list_returns_no_data():
    assert inspect_safety_restraints([]) == "NO_DATA"


def test_restraints_none_returns_no_data():
    assert inspect_safety_restraints(None) == "NO_DATA"


def test_restraints_two_unlatched_in_a_row_locks():
    assert inspect_safety_restraints([[0, 0]]) == "EMERGENCY_LOCK"


def test_restraints_lock_after_latched_readings():
    assert inspect_safety_restraints([[1, 0, 0]]) == "EMERGENCY_LOCK"


def test_restraints_lock_found_in_later_stream():
    assert inspect_safety_restraints([[1, 1], [0, 0, 1]]) == "EMERGENCY_LOCK"


def test_restraints_all_latched_is_safe():
    assert inspect_safety_restraints([[1, 1, 1], [1, 1]]) == "SAFE"


def test_restraints_streak_resets_after_latch():
    assert inspect_safety_restraints([[0, 1, 0, 1]]) == "SAFE"


def test_restraints_streak_does_not_carry_between_streams():
    assert inspect_safety_restraints([[0], [0]]) == "SAFE"


def test_restraints_empty_sensor_stream_is_safe():
    assert inspect_safety_restraints([[]]) == "SAFE"
