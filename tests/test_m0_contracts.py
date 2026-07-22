"""Tests for M0 contracts: EvidenceTier, ContributionMode, PR-C1, PR-C2."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from calibrance_data_contracts import (
    ActivityFingerprint,
    CalibrationOutcomeEnvelope,
    ContributionMode,
    EvidenceTier,
)
from calibrance_data_contracts.calibration_outcome import FORBIDDEN_PAYLOAD_KEYS


def test_evidence_tier_members():
    assert len(EvidenceTier) == 5
    assert EvidenceTier.SYNTHETIC.value == "synthetic"
    assert EvidenceTier.RECORDED_REAL_REPLAY.value == "recorded_real_replay"
    assert EvidenceTier.URSIM_HIL.value == "ursim_hil"
    assert EvidenceTier.LIVE_SHADOW.value == "live_shadow"
    assert EvidenceTier.LIVE_HUMAN_APPROVED.value == "live_human_approved"


def test_contribution_mode_members():
    assert len(ContributionMode) == 3
    assert ContributionMode.PRIVATE.value == "private"
    assert ContributionMode.COHORT.value == "cohort"
    assert ContributionMode.RESEARCH_PARTNER.value == "research_partner"


def _complete_envelope_kwargs(**overrides):
    kwargs = {
        "event_id": "evt-001",
        "event_type": "calibration.candidate_created.v1",
        "organization_id": "org-1",
        "site_id": "site-1",
        "asset_id": "asset-1",
        "configuration_digest": "sha256:cfg",
        "evidence_tier": EvidenceTier.SYNTHETIC,
        "source_record_type": "calibration_sessions",
        "source_record_id": "sess-1",
        "provenance_digest": "sha256:prov",
        "created_at": datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc),
    }
    kwargs.update(overrides)
    return kwargs


def test_calibration_outcome_envelope_validates():
    envelope = CalibrationOutcomeEnvelope(**_complete_envelope_kwargs())
    assert envelope.event_id == "evt-001"
    assert envelope.schema_version == "1.0"
    assert envelope.evidence_tier == EvidenceTier.SYNTHETIC
    assert envelope.source_record_version == 1
    assert envelope.source_event_ids == []
    assert envelope.payload == {}


def test_calibration_outcome_envelope_rejects_unknown_evidence_tier():
    with pytest.raises(ValidationError):
        CalibrationOutcomeEnvelope(**_complete_envelope_kwargs(evidence_tier="not_a_real_tier"))


def test_calibration_outcome_envelope_rejects_unknown_contribution_mode():
    with pytest.raises(ValidationError):
        CalibrationOutcomeEnvelope(**_complete_envelope_kwargs(contribution_mode="not_a_real_mode"))


def test_calibration_outcome_envelope_defaults_contribution_mode_to_private():
    envelope = CalibrationOutcomeEnvelope(**_complete_envelope_kwargs())
    assert envelope.contribution_mode == ContributionMode.PRIVATE


def test_activity_fingerprint_validates():
    fp = ActivityFingerprint(
        robot_model="UR3e",
        configuration_digest="sha256:cfg",
        activity_family="FAST_ACCELERATION_DECELERATION",
        duration_s=12.5,
        sample_rate_hz=500.0,
        position_range_by_joint={"j0": (-1.0, 1.0)},
        velocity_range_by_joint={"j0": (-2.0, 2.0)},
        acceleration_range_by_joint={"j0": (-5.0, 5.0)},
        velocity_reversals_by_joint={"j0": 3},
        direction_coverage=0.8,
        gravity_pose_diversity=0.6,
        contact_fraction=0.1,
        temperature_range=(20.0, 35.0),
        channel_availability=["joint_position_rad", "joint_velocity_rad_s"],
    )
    assert fp.fingerprint_version == "1.0"
    assert fp.robot_model == "UR3e"
    assert fp.activity_family == "FAST_ACCELERATION_DECELERATION"
    assert fp.position_range_by_joint["j0"] == (-1.0, 1.0)


def test_activity_fingerprint_defaults_optional_fields():
    fp = ActivityFingerprint(
        robot_model="UR3e",
        configuration_digest="sha256:cfg",
        activity_family="HOLD",
        duration_s=1.0,
        sample_rate_hz=125.0,
    )
    assert fp.fingerprint_version == "1.0"
    assert fp.controller_major_version is None
    assert fp.program_digest is None
    assert fp.position_range_by_joint == {}
    assert fp.velocity_range_by_joint == {}
    assert fp.acceleration_range_by_joint == {}
    assert fp.velocity_reversals_by_joint == {}
    assert fp.direction_coverage == 0.0
    assert fp.gravity_pose_diversity == 0.0
    assert fp.contact_fraction == 0.0
    assert fp.temperature_range is None
    assert fp.channel_availability == []


@pytest.mark.parametrize("forbidden_key", sorted(FORBIDDEN_PAYLOAD_KEYS))
def test_calibration_outcome_envelope_rejects_hidden_truth_payload_keys(forbidden_key):
    with pytest.raises(ValidationError) as exc_info:
        CalibrationOutcomeEnvelope(**_complete_envelope_kwargs(payload={forbidden_key: "secret"}))
    assert forbidden_key in str(exc_info.value)


def test_forbidden_payload_keys_set_is_complete():
    expected = {
        "scenario_class",
        "hidden_parameters",
        "expected_outcome",
        "true_candidate_error",
        "future_golden_result",
    }
    assert FORBIDDEN_PAYLOAD_KEYS == expected
