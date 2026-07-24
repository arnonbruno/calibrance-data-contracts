"""AUTOCAL-1 A2 — canonical artifact schema validation tests."""

from __future__ import annotations

import pytest

from calibrance_data_contracts.canonical_artifacts import (
    SERVER_VALIDATION_SOURCE,
    AuditEvidenceEntry,
    CalibrationDatasetManifest,
    CalibrationWorkflow,
    CalibrationWorkflowState,
    CanonicalArtifactError,
    EstimatedParameter,
    EstimatorRun,
    EstimatorRunStatus,
    NumericalCalibrationCandidate,
    ServerValidationRun,
    evidence_field_inventory,
    sha256_hex,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def _param(**overrides) -> EstimatedParameter:
    data = dict(
        parameter_id="ur.payload.mass",
        current_value=1.0,
        proposed_value=1.2,
        delta=0.2,
        unit="kg",
        lower_bound=0.5,
        upper_bound=3.0,
        standard_error=0.05,
        identifiability="identifiable",
        source="server_estimated",
    )
    data.update(overrides)
    return EstimatedParameter(**data)


def _manifest(**overrides) -> CalibrationDatasetManifest:
    data = dict(
        dataset_id="ds-1",
        asset_id="asset-1",
        task_id="pick-place",
        task_version="1.0.0",
        robot_model="ur3e",
        tool_configuration={"tool": "gripper"},
        payload_configuration={"mass_kg": 1.0},
        operating_envelope={"speed_max": 1.0},
        telemetry_source_ids=["tel-1"],
        process_context_ids=["pc-1"],
        required_signals=["joint_torque"],
        available_signals=["joint_torque", "joint_position"],
        estimation_window={"start": "2026-07-01T00:00:00Z", "end": "2026-07-02T00:00:00Z"},
        held_out_window={"start": "2026-07-02T00:00:00Z", "end": "2026-07-03T00:00:00Z"},
        split_strategy="cycle_based",
        quality_filters={"min_cycles": 10},
        missingness_summary={"joint_torque": 0.01},
        evidence_tier="synthetic",
    )
    data.update(overrides)
    return CalibrationDatasetManifest(**data)


def test_manifest_computes_immutable_digest() -> None:
    m = _manifest()
    assert len(m.manifest_digest) == 64
    assert m.manifest_digest == m.compute_digest()
    with pytest.raises(CanonicalArtifactError, match="immutable digest"):
        _manifest(manifest_digest=DIGEST_A)


def test_manifest_requires_windows() -> None:
    with pytest.raises(CanonicalArtifactError, match="estimation_window"):
        _manifest(estimation_window={"start": "x"})


def test_estimator_run_completed_requires_artifact() -> None:
    with pytest.raises(CanonicalArtifactError, match="artifact_digest"):
        EstimatorRun(
            estimator_run_id="er-1",
            dataset_id="ds-1",
            estimator_name="constrained_nls",
            estimator_version="0.1.0",
            configuration_digest=DIGEST_A,
            parameter_ids=["ur.payload.mass"],
            prior_digest=DIGEST_B,
            status=EstimatorRunStatus.COMPLETED.value,
        )


def test_estimator_run_ok() -> None:
    run = EstimatorRun(
        estimator_run_id="er-1",
        dataset_id="ds-1",
        estimator_name="constrained_nls",
        estimator_version="0.1.0",
        configuration_digest=DIGEST_A,
        parameter_ids=["ur.payload.mass"],
        prior_digest=DIGEST_B,
        status="completed",
        artifact_digest=DIGEST_C,
    )
    assert run.to_dict()["status"] == "completed"


def test_candidate_requires_server_estimated() -> None:
    with pytest.raises(CanonicalArtifactError, match="server_estimated"):
        NumericalCalibrationCandidate(
            candidate_id="c-1",
            estimator_run_id="er-1",
            dataset_id="ds-1",
            asset_id="a-1",
            task_id="t-1",
            parameter_values=[_param()],
            parameter_source="caller_supplied",
            server_estimated=False,
        )


def test_candidate_digest_roundtrip() -> None:
    cand = NumericalCalibrationCandidate(
        candidate_id="c-1",
        estimator_run_id="er-1",
        dataset_id="ds-1",
        asset_id="a-1",
        task_id="t-1",
        parameter_values=[_param()],
        model_adequacy={"status": "supported", "checks": {"rmse": True}},
        uncertainty_status={"coverage": 0.9, "method": "bootstrap"},
    )
    assert cand.candidate_digest == cand.compute_digest()
    assert cand.server_estimated is True
    assert cand.parameter_source == "server_estimated"


def test_validation_run_requires_server_reproduced() -> None:
    with pytest.raises(CanonicalArtifactError, match="server_reproduced"):
        ServerValidationRun(
            validation_run_id="v-1",
            candidate_id="c-1",
            held_out_dataset_digest=DIGEST_A,
            metrics={"held_out_rmse": 0.1},
            task_tolerance_results={},
            cross_task_results={},
            physical_constraint_results={},
            counterexample_results={},
            model_adequacy_results={},
            disposition="eligible_for_human_review",
            artifact_digest=DIGEST_B,
            validation_source="caller_supplied",
            independently_reproduced=True,
        )


def test_validation_run_ok() -> None:
    v = ServerValidationRun(
        validation_run_id="v-1",
        candidate_id="c-1",
        held_out_dataset_digest=DIGEST_A,
        metrics={"held_out_rmse": 0.1, "estimation_rmse": 0.08, "improvement_pct": 20.0},
        task_tolerance_results={"ok": True},
        cross_task_results={},
        physical_constraint_results={},
        counterexample_results={},
        model_adequacy_results={},
        disposition="eligible_for_human_review",
        artifact_digest=DIGEST_B,
    )
    assert v.validation_source == SERVER_VALIDATION_SOURCE
    assert v.independently_reproduced is True


def test_workflow_closed_requires_timestamp() -> None:
    with pytest.raises(CanonicalArtifactError, match="closed_at"):
        CalibrationWorkflow(
            workflow_id="w-1",
            asset_id="a-1",
            task_id="t-1",
            organization_id="o-1",
            state=CalibrationWorkflowState.CLOSED.value,
        )


def test_audit_evidence_fields() -> None:
    entry = AuditEvidenceEntry(
        workflow_id="w-1",
        event_type="dataset_built",
        actor="system:dataset_builder",
        organization_id="o-1",
        asset_id="a-1",
        task_id="t-1",
        source="system",
        request_id="req-1",
        artifact_digests=[DIGEST_A],
        source_sha=DIGEST_B,
        feature_flags={"autocal_shadow": True},
        evidence_tier="recorded_real_replay",
        container_digest=DIGEST_C,
    )
    assert entry.to_dict()["source_sha"] == DIGEST_B


def test_evidence_inventory_covers_all_schemas() -> None:
    inventory = evidence_field_inventory()
    assert set(inventory) == {
        "CalibrationDatasetManifest",
        "EstimatorRun",
        "NumericalCalibrationCandidate",
        "ServerValidationRun",
        "CalibrationWorkflow",
        "AuditEvidenceEntry",
        "CalibrationObservationSet",
        "RegressorResult",
    }
    for fields in inventory.values():
        assert fields


def test_sha256_hex_stable() -> None:
    assert sha256_hex({"b": 1, "a": 2}) == sha256_hex({"a": 2, "b": 1})


def _observation_set(**overrides):
    from calibrance_data_contracts.canonical_artifacts import CalibrationObservationSet

    data = dict(
        observation_set_id="obs-1",
        dataset_manifest_id="ds-1",
        asset_id="asset-1",
        task_id="pick-place",
        robot_model="ur3e",
        q=[[0.1, 0.2, 0.3, 0.4, 0.5, 0.6], [0.11, 0.21, 0.31, 0.41, 0.51, 0.61]],
        q_dot=[[0.01] * 6, [0.02] * 6],
        q_ddot=[[0.001] * 6, [0.002] * 6],
        effort=[[1.0] * 6, [1.1] * 6],
        sample_times=[0.0, 0.008],
        quality_mask=[True, True],
        activity_segments=[{"segment_id": "seg-0", "start_idx": 0, "end_idx": 1}],
        process_context={"task_id": "pick-place"},
        signal_provenance={"q": "joint_position", "q_ddot": "derived"},
        transformation_log=[{"step": "unit_conversion", "field": "q", "from": "rad", "to": "rad"}],
        evidence_tier="synthetic",
    )
    data.update(overrides)
    return CalibrationObservationSet(**data)


def test_observation_set_digest_deterministic() -> None:
    a = _observation_set()
    b = _observation_set()
    assert a.observation_set_digest == b.observation_set_digest
    assert len(a.observation_set_digest) == 64
    assert a.n_samples == 2
    assert a.n_joints == 6


def test_observation_set_requires_transformation_log() -> None:
    with pytest.raises(CanonicalArtifactError, match="transformation_log"):
        _observation_set(transformation_log=[])


def test_observation_set_rejects_digest_mismatch() -> None:
    with pytest.raises(CanonicalArtifactError, match="immutable digest"):
        _observation_set(observation_set_digest="a" * 64)


def test_observation_set_shape_mismatch() -> None:
    with pytest.raises(CanonicalArtifactError, match="sample_times"):
        _observation_set(sample_times=[0.0])

def _regressor_result(**overrides):
    from calibrance_data_contracts.canonical_artifacts import RegressorResult

    # 2 samples × 6 joints = 12 rows, 2 parameters
    phi = [[float(i + j) for j in range(2)] for i in range(12)]
    y = [float(i) * 0.1 for i in range(12)]
    data = dict(
        regressor_version="1.0.0",
        physics_model_version="1.0.0",
        parameter_ids=["ur.payload.mass", "ur.joint.friction.viscous"],
        phi=phi,
        y=y,
        n_samples=2,
        n_joints=6,
        n_parameters=2,
        observation_set_digest="a" * 64,
        parameter_taxonomy_version="1.0.0",
        signal_transformations=[{"step": "unit_conversion", "field": "q"}],
        derivative_method="savgol_11_3",
        filter_settings={"butterworth_cutoff_hz": 20.0, "butterworth_order": 4},
        condition_number=12.5,
        excitation_rank=2,
        n_effective_samples=2,
    )
    data.update(overrides)
    return RegressorResult(**data)


def test_regressor_result_digest_deterministic() -> None:
    a = _regressor_result()
    b = _regressor_result()
    assert a.regressor_digest == b.regressor_digest
    assert a.target_digest == b.target_digest
    assert len(a.regressor_digest) == 64
    assert len(a.target_digest) == 64


def test_regressor_result_requires_transformations() -> None:
    with pytest.raises(CanonicalArtifactError, match="signal_transformations"):
        _regressor_result(signal_transformations=[])


def test_regressor_result_rejects_singular() -> None:
    with pytest.raises(CanonicalArtifactError, match="condition_number"):
        _regressor_result(condition_number=float("inf"))


def test_regressor_result_requires_observation_link() -> None:
    with pytest.raises(CanonicalArtifactError, match="observation_set_digest"):
        _regressor_result(observation_set_digest="")
