"""P6 evidence recommendation schema — authority and constraint invariants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from calibrance_data_contracts import (
    ACTIVE_IDENTIFICATION_AUTHORITY,
    EvidenceRecommendation,
    EvidenceRecommendationValidationError,
    default_constraints,
)

TS = datetime(2026, 7, 23, 16, 0, tzinfo=timezone.utc)


def _rec(**overrides) -> EvidenceRecommendation:
    data = dict(
        recommendation_id="erec-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="task-1",
        recommended_activity="bidirectional_velocity_sweep",
        expected_information_gain=0.62,
        expected_duration_minutes=2.5,
        target_parameter_groups=["joint_dynamics", "payload"],
        competing_hypotheses=["payload_drift", "friction_increase"],
        required_signals=["joint_position", "joint_velocity", "joint_torque", "timestamp"],
        constraints=default_constraints(),
        estimated_interruption_cost_usd=75.0,
        alternatives=[
            {
                "activity": "free_motion",
                "expected_information_gain": 0.55,
                "score": 0.40,
            }
        ],
        ranking_strategy="cost_aware_calibrance",
        score=0.48,
        explanation=(
            "Bidirectional velocity sweep best separates payload vs friction "
            "under the duration budget."
        ),
        created_at=TS,
        evidence_tier="synthetic",
        labels={"DEMO": True},
    )
    data.update(overrides)
    return EvidenceRecommendation(**data)


def test_valid_recommendation_forces_authority() -> None:
    r = _rec()
    assert r.commands_robot is False
    assert r.human_approval_required is True
    assert r.active_identification_authority == ACTIVE_IDENTIFICATION_AUTHORITY
    assert r.affects_active_profile is False
    assert "workspace" in r.constraints


def test_commands_robot_rejected() -> None:
    with pytest.raises(EvidenceRecommendationValidationError, match="commands_robot"):
        _rec(commands_robot=True)


def test_human_approval_required() -> None:
    with pytest.raises(EvidenceRecommendationValidationError, match="human_approval"):
        _rec(human_approval_required=False)


def test_authority_must_be_recommend_only() -> None:
    with pytest.raises(EvidenceRecommendationValidationError, match="recommend_only"):
        _rec(active_identification_authority="execute")


def test_affects_active_profile_rejected() -> None:
    with pytest.raises(EvidenceRecommendationValidationError, match="active profile"):
        _rec(affects_active_profile=True)


def test_recommendation_without_explanation_rejected() -> None:
    with pytest.raises(EvidenceRecommendationValidationError, match="explanation"):
        _rec(explanation="")


def test_missing_constraint_keys_rejected() -> None:
    with pytest.raises(EvidenceRecommendationValidationError, match="constraints missing"):
        _rec(constraints={"workspace": "ok"})


def test_blocked_recommendation_allows_empty_activity() -> None:
    r = _rec(
        recommended_activity="",
        explanation="",
        blocked_reason="required_signal_missing:joint_torque",
        competing_hypotheses=[],
        target_parameter_groups=[],
        constraints={},
    )
    assert r.blocked_reason.startswith("required_signal_missing")
    assert r.commands_robot is False


def test_to_dict_locks_authority() -> None:
    d = _rec().to_dict()
    assert d["commands_robot"] is False
    assert d["active_identification_authority"] == "recommend_only"
    assert d["affects_active_profile"] is False


def test_default_constraints_has_safety_boundary() -> None:
    c = default_constraints()
    assert c["safety_declaration"]["commands_robot"] is False
    assert c["human_approval"] is True
