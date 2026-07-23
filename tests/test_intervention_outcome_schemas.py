"""P4 intervention/outcome schema — separation and provenance tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from calibrance_data_contracts import (
    CalibrationRecommendation,
    CausalAttribution,
    HumanDecision,
    InterventionOutcomeChain,
    InterventionState,
    ObservedOutcome,
    OutcomeType,
    PhysicalIntervention,
)

TS = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def _recommendation(**overrides) -> CalibrationRecommendation:
    data = dict(
        recommendation_id="rec-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="task-1",
        candidate_id="cand-1",
        recommended_parameters={"joint_1_friction": 0.12},
        expected_improvement={"residual_rms_pct": -15.0},
        confidence=0.82,
        evidence_tier="synthetic",
        created_at=TS,
        audit_event_id="aud-rec-001",
    )
    data.update(overrides)
    return CalibrationRecommendation(**data)


def _decision(**overrides) -> HumanDecision:
    data = dict(
        decision_id="dec-001",
        recommendation_id="rec-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="task-1",
        state=InterventionState.ACCEPTED,
        decided_by="operator-1",
        decided_at=TS,
        evidence_tier="synthetic",
        is_synthetic=True,
        labeled_as_real=False,
        audit_event_id="aud-dec-001",
    )
    data.update(overrides)
    return HumanDecision(**data)


def _intervention(**overrides) -> PhysicalIntervention:
    data = dict(
        intervention_id="int-001",
        decision_id="dec-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="task-1",
        actual_parameters_applied={"joint_1_friction": 0.12},
        applied_by="tech-7",
        applied_at=TS,
        evidence_tier="synthetic",
        audit_event_id="aud-int-001",
    )
    data.update(overrides)
    return PhysicalIntervention(**data)


def _outcome(**overrides) -> ObservedOutcome:
    data = dict(
        outcome_id="out-001",
        intervention_id="int-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="task-1",
        outcome_type=OutcomeType.RESIDUAL_IMPROVED,
        measured_improvement={"residual_rms_pct": -14.2},
        observation_window_hours=24.0,
        evidence_tier="synthetic",
        audit_event_id="aud-out-001",
        intervention_asset_id="asset-1",
        causal_attribution=CausalAttribution.NOT_CLAIMED,
    )
    data.update(overrides)
    return ObservedOutcome(**data)


def test_recommendation_never_executed() -> None:
    with pytest.raises(ValueError, match="executed"):
        _recommendation(is_executed=True)
    with pytest.raises(ValueError, match="EXECUTED"):
        _recommendation(state=InterventionState.EXECUTED)


def test_synthetic_decision_not_labeled_real() -> None:
    with pytest.raises(ValueError, match="labeled as real"):
        _decision(is_synthetic=True, labeled_as_real=True)


def test_human_decision_state_restricted() -> None:
    with pytest.raises(ValueError, match="human decision state"):
        _decision(state=InterventionState.EXECUTED)


def test_modified_requires_parameters() -> None:
    with pytest.raises(ValueError, match="modified_parameters"):
        _decision(state=InterventionState.MODIFIED, modified_parameters=None)


def test_causal_claim_requires_evidence() -> None:
    with pytest.raises(ValueError, match="causal claim without evidence"):
        _outcome(
            causal_attribution=CausalAttribution.SUPPORTED,
            causal_evidence_ids=[],
        )


def test_cross_asset_outcome_forbidden() -> None:
    with pytest.raises(ValueError, match="cross-asset"):
        _outcome(asset_id="asset-1", intervention_asset_id="asset-2")


def test_rejected_chain_has_no_intervention_or_outcome() -> None:
    chain = InterventionOutcomeChain(
        recommendation=_recommendation(),
        human_decision=_decision(state=InterventionState.REJECTED, reason="risk too high"),
    )
    assert chain.physical_intervention is None
    assert chain.observed_outcome is None

    with pytest.raises(ValueError, match="rejected"):
        InterventionOutcomeChain(
            recommendation=_recommendation(),
            human_decision=_decision(state=InterventionState.REJECTED),
            physical_intervention=_intervention(),
        )


def test_successful_chain_round_trip() -> None:
    chain = InterventionOutcomeChain(
        recommendation=_recommendation(),
        human_decision=_decision(),
        physical_intervention=_intervention(),
        observed_outcome=_outcome(),
    )
    assert chain.recommendation.recommendation_id == "rec-001"
    assert chain.human_decision.state is InterventionState.ACCEPTED
    assert chain.physical_intervention is not None
    assert chain.observed_outcome is not None
    assert chain.observed_outcome.outcome_type is OutcomeType.RESIDUAL_IMPROVED
    assert chain.recommendation.is_executed is False
    assert chain.human_decision.labeled_as_real is False


def test_outcome_types_cover_acceptance_scenarios() -> None:
    required = {
        "residual_improved",
        "residual_worsened",
        "no_measurable_effect",
        "problem_recurred",
        "evidence_insufficient",
    }
    assert required.issubset({o.value for o in OutcomeType})
