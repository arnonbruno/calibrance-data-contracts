"""P7 candidate validation schema — disposition and invariant checks."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from calibrance_data_contracts import (
    CandidateDisposition,
    CandidateValidation,
    CandidateValidationError,
)

TS = datetime(2026, 7, 23, 17, 0, tzinfo=timezone.utc)


def _valid(**overrides) -> CandidateValidation:
    data = dict(
        validation_id="val-001",
        candidate_id="cand-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="pick-place-1",
        disposition=CandidateDisposition.ELIGIBLE_FOR_HUMAN_REVIEW,
        identification_fit={"rmse": 0.05, "improved": True},
        held_out_performance={"rmse": 0.06, "degraded": False},
        task_tolerance_compliance={"within_tolerance": True},
        cross_task_impact={"material_degradation": False, "tasks": {}},
        robustness_score=0.85,
        physical_validity={"valid": True, "violations": []},
        uncertainty_quality={"calibrated": True, "ece": 0.04},
        simulator_agreement={"agree": True, "max_delta": 0.02},
        counterexample_similarity={"max_similarity": 0.1, "critical_match": False},
        model_inadequacy={"discrepancy": 0.08, "excessive": False},
        created_at=TS,
        evidence_tier="synthetic",
    )
    data.update(overrides)
    return CandidateValidation(**data)


def test_eligible_roundtrip() -> None:
    v = _valid()
    assert v.disposition == CandidateDisposition.ELIGIBLE_FOR_HUMAN_REVIEW
    assert v.is_promotable_to_human is True
    d = v.to_dict()
    assert d["disposition"] == "eligible_for_human_review"
    assert d["rejection_reasons"] == []


def test_reject_requires_reasons() -> None:
    with pytest.raises(CandidateValidationError, match="rejection_reason"):
        _valid(
            disposition=CandidateDisposition.REJECT,
            rejection_reasons=[],
        )


def test_eligible_forbids_reasons() -> None:
    with pytest.raises(CandidateValidationError, match="must not carry"):
        _valid(rejection_reasons=["overfitting_held_out_degradation"])


def test_reject_with_reasons_ok() -> None:
    v = _valid(
        disposition=CandidateDisposition.REJECT,
        rejection_reasons=["physically_invalid_parameters"],
    )
    assert v.is_promotable_to_human is False
    assert v.rejection_reasons == ["physically_invalid_parameters"]


def test_disposition_from_string() -> None:
    v = _valid(disposition="insufficient_evidence", rejection_reasons=[])
    assert v.disposition == CandidateDisposition.INSUFFICIENT_EVIDENCE


def test_unknown_disposition() -> None:
    with pytest.raises(CandidateValidationError, match="unknown disposition"):
        _valid(disposition="promote_now")


def test_robustness_bounds() -> None:
    with pytest.raises(CandidateValidationError, match="robustness_score"):
        _valid(robustness_score=1.5)


def test_required_ids() -> None:
    with pytest.raises(CandidateValidationError, match="validation_id"):
        _valid(validation_id="")


def test_unsupported_disposition() -> None:
    v = _valid(
        disposition=CandidateDisposition.UNSUPPORTED,
        rejection_reasons=[],
        warnings=["mechanism_not_supported:plastic_deformation"],
    )
    assert v.disposition.value == "unsupported"


def test_unknown_rejection_reason_warns() -> None:
    v = _valid(
        disposition=CandidateDisposition.REJECT,
        rejection_reasons=["custom_plant_policy"],
    )
    assert any("unknown rejection_reason" in w for w in v.warnings)
