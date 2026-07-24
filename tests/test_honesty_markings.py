"""Honesty marking schemas — parameter_source / validation_source gates."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from calibrance_data_contracts import (
    CandidateDisposition,
    CandidateValidation,
    CandidateValidationError,
    HonestyMarkingError,
    IdentifiedParameterVector,
    ParameterSource,
    TwinParameterSet,
    ValidationSource,
    assert_fit_allowed_source,
    assert_fleet_prior_input_allowed,
    assert_no_high_authority_label,
    can_promote_to_fleet_prior_input,
    estimated_by_for_response,
    max_credibility_label,
    parameter_source_audit_event,
    validate_server_estimated_claim,
)


def test_fit_rejects_server_estimated() -> None:
    with pytest.raises(HonestyMarkingError, match="no server estimator"):
        assert_fit_allowed_source(
            parameter_source="caller_supplied",
            server_estimated=True,
        )


def test_fit_rejects_server_estimated_source() -> None:
    with pytest.raises(HonestyMarkingError, match="not allowed on /fit"):
        assert_fit_allowed_source(parameter_source="server_estimated")


def test_fit_accepts_caller_supplied_default() -> None:
    assert assert_fit_allowed_source(parameter_source=None) == "caller_supplied"
    assert (
        assert_fit_allowed_source(parameter_source="synthetic_demo") == "synthetic_demo"
    )


def test_server_estimated_requires_estimator_run_id() -> None:
    with pytest.raises(HonestyMarkingError, match="estimator_run_id"):
        validate_server_estimated_claim(
            server_estimated=True,
            estimator_run_id=None,
            parameter_source="server_estimated",
        )


def test_identified_vector_defaults_caller_supplied() -> None:
    vec = IdentifiedParameterVector(
        parameter_set_id="p1",
        names=("payload_mass_kg",),
        values=(1.5,),
    )
    assert vec.parameter_source == ParameterSource.CALLER_SUPPLIED.value
    assert vec.server_estimated is False
    assert vec.estimator_run_id is None


def test_identified_vector_rejects_server_estimated_without_run_id() -> None:
    with pytest.raises(ValidationError):
        IdentifiedParameterVector(
            parameter_set_id="p1",
            names=("payload_mass_kg",),
            values=(1.5,),
            server_estimated=True,
            parameter_source="server_estimated",
        )


def test_candidate_validation_defaults_caller_supplied() -> None:
    v = CandidateValidation(
        validation_id="val-1",
        candidate_id="cand-1",
        tenant_id="t1",
        asset_id="a1",
        task_id="task-1",
        disposition=CandidateDisposition.ELIGIBLE_FOR_HUMAN_REVIEW,
        identification_fit={},
        held_out_performance={},
        task_tolerance_compliance={},
        cross_task_impact={},
        robustness_score=0.5,
        physical_validity={"valid": True},
        uncertainty_quality={},
    )
    assert v.validation_source == ValidationSource.CALLER_SUPPLIED.value
    assert v.independently_reproduced is False
    d = v.to_dict()
    assert d["validation_source"] == "caller_supplied"
    assert d["independently_reproduced"] is False


def test_candidate_validation_rejects_high_authority_label() -> None:
    with pytest.raises(CandidateValidationError, match="calibrance_verified"):
        CandidateValidation(
            validation_id="val-1",
            candidate_id="cand-1",
            tenant_id="t1",
            asset_id="a1",
            task_id="task-1",
            disposition=CandidateDisposition.ELIGIBLE_FOR_HUMAN_REVIEW,
            identification_fit={},
            held_out_performance={},
            task_tolerance_compliance={},
            cross_task_impact={},
            robustness_score=0.5,
            physical_validity={"valid": True},
            uncertainty_quality={},
            credibility_status="calibrance_verified",
        )


def test_high_authority_gate_and_fleet_prior() -> None:
    assert_no_high_authority_label(
        server_estimated=False,
        independently_reproduced=False,
        label="provisional_callersupplied",
    )
    with pytest.raises(HonestyMarkingError):
        assert_no_high_authority_label(
            server_estimated=False,
            independently_reproduced=False,
            label="production_validated",
        )
    assert can_promote_to_fleet_prior_input(
        server_estimated=False, independently_reproduced=False
    ) is False
    with pytest.raises(HonestyMarkingError, match="fleet-prior"):
        assert_fleet_prior_input_allowed(
            server_estimated=False, independently_reproduced=True
        )


def test_max_credibility_and_estimated_by() -> None:
    assert (
        max_credibility_label(
            server_estimated=False,
            independently_reproduced=False,
            requested="calibrance_verified",
        )
        == "provisional_callersupplied"
    )
    assert estimated_by_for_response(server_estimated=False) is None
    assert estimated_by_for_response(server_estimated=True) == "calibrance"


def test_audit_event_shape() -> None:
    event = parameter_source_audit_event(
        parameter_source="caller_supplied",
        server_estimated=False,
        supplied_by="user-1",
        timestamp="2026-07-23T00:00:00Z",
    )
    assert event["event_type"] == "profile_parameter_source"
    assert event["server_estimated"] is False


def test_twin_parameter_set_defaults() -> None:
    twin = TwinParameterSet(
        parameter_set_id="tps-1",
        robot_model="UR3e",
        model_source_digest="sha256:deadbeef",
        joint_order=("shoulder_pan",),
        link_inertials=[],
        friction=[],
        actuators=[],
    )
    assert twin.parameter_source == "caller_supplied"
    assert twin.server_estimated is False
    assert twin.estimator_run_id is None
