"""AUTOCAL-1 A4a — versioned estimator Protocol compliance tests."""

from __future__ import annotations

import pytest

from calibrance_data_contracts.canonical_artifacts import (
    CalibrationDatasetManifest,
    EstimatedParameter,
)
from calibrance_data_contracts.estimator_protocol import (
    PRIOR_TYPES,
    CalibrationEstimator,
    EstimationContext,
    EstimationResult,
    EstimatorProtocolError,
    ParameterPrior,
    ParameterSpec,
    SupportResult,
)

DIGEST_A = "a" * 64


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
        robot_model="UR5e",
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


def _context(**overrides) -> EstimationContext:
    data = dict(
        robot_model="UR5e",
        operating_envelope={"speed_max": 1.0},
        task_id="pick-place",
        task_version="1.0.0",
        tool_configuration={"tool": "gripper"},
        payload_configuration={"mass_kg": 1.0},
        evidence_tier="synthetic",
        seed=42,
    )
    data.update(overrides)
    return EstimationContext(**data)


class _MockEstimator:
    """Minimal CalibrationEstimator implementation for Protocol compliance."""

    @property
    def estimator_name(self) -> str:
        return "mock_nls"

    @property
    def estimator_version(self) -> str:
        return "0.0.1"

    def supports(
        self,
        robot_model: str,
        parameter_ids: list[str],
        available_signals: set[str],
    ) -> SupportResult:
        del robot_model
        missing = sorted({"joint_torque"} - set(available_signals))
        unsupported = [p for p in parameter_ids if not p.startswith("ur.")]
        if missing or unsupported:
            return SupportResult(
                supported=False,
                reason="missing signals or unsupported parameters",
                missing_signals=missing,
                unsupported_parameters=unsupported,
            )
        return SupportResult(supported=True, reason="ok")

    def estimate(
        self,
        dataset_manifest: CalibrationDatasetManifest,
        parameter_specs: list[ParameterSpec],
        priors: list[ParameterPrior],
        context: EstimationContext,
    ) -> EstimationResult:
        del priors
        params = [
            _param(
                parameter_id=spec.parameter_id,
                current_value=spec.current_value,
                proposed_value=spec.current_value,
                delta=0.0,
                unit=spec.unit,
                lower_bound=spec.lower_bound,
                upper_bound=spec.upper_bound,
            )
            for spec in parameter_specs
        ]
        return EstimationResult(
            estimator_name=self.estimator_name,
            estimator_version=self.estimator_version,
            parameters=params,
            converged=True,
            objective_history=[1.0, 0.5, 0.1],
            n_iterations=3,
            n_start_points=1,
            runtime_seconds=0.01,
            configuration_digest=DIGEST_A,
            warnings=[],
            failure_reason=None,
        )


def test_mock_estimator_satisfies_protocol() -> None:
    estimator = _MockEstimator()
    assert isinstance(estimator, CalibrationEstimator)
    support = estimator.supports("UR5e", ["ur.payload.mass"], {"joint_torque", "joint_position"})
    assert support.supported is True
    result = estimator.estimate(
        dataset_manifest=_manifest(),
        parameter_specs=[
            ParameterSpec(
                parameter_id="ur.payload.mass",
                current_value=1.0,
                lower_bound=0.5,
                upper_bound=3.0,
                unit="kg",
            )
        ],
        priors=[],
        context=_context(),
    )
    assert result.converged is True
    assert result.artifact_digest
    assert len(result.artifact_digest) == 64
    assert result.estimator_name == "mock_nls"
    assert result.estimator_version == "0.0.1"


def test_support_result_requires_reason_when_unsupported() -> None:
    with pytest.raises(EstimatorProtocolError, match="reason"):
        SupportResult(supported=False, reason="")


def test_estimation_result_rejects_silent_nonconvergence() -> None:
    with pytest.raises(EstimatorProtocolError, match="silent_nonconvergence"):
        EstimationResult(
            estimator_name="mock",
            estimator_version="0.1.0",
            parameters=[],
            converged=False,
            objective_history=[],
            n_iterations=1,
            n_start_points=1,
            runtime_seconds=0.1,
            configuration_digest=DIGEST_A,
            failure_reason=None,
        )


def test_estimation_result_rejects_caller_supplied_source() -> None:
    with pytest.raises(EstimatorProtocolError, match="server_estimated"):
        EstimationResult(
            estimator_name="mock",
            estimator_version="0.1.0",
            parameters=[_param(source="caller_supplied")],
            converged=True,
            objective_history=[0.1],
            n_iterations=1,
            n_start_points=1,
            runtime_seconds=0.1,
            configuration_digest=DIGEST_A,
        )


def test_estimation_result_rejects_out_of_bounds() -> None:
    with pytest.raises(EstimatorProtocolError, match="physically_invalid"):
        EstimationResult(
            estimator_name="mock",
            estimator_version="0.1.0",
            parameters=[_param(proposed_value=9.0, lower_bound=0.5, upper_bound=3.0)],
            converged=True,
            objective_history=[0.1],
            n_iterations=1,
            n_start_points=1,
            runtime_seconds=0.1,
            configuration_digest=DIGEST_A,
        )


def test_estimation_result_computes_artifact_digest() -> None:
    result = EstimationResult(
        estimator_name="mock",
        estimator_version="0.1.0",
        parameters=[_param()],
        converged=True,
        objective_history=[0.2, 0.1],
        n_iterations=2,
        n_start_points=1,
        runtime_seconds=0.05,
        configuration_digest=DIGEST_A,
    )
    assert result.artifact_digest == result.compute_artifact_digest()
    payload = result.to_dict()
    assert set(payload) >= {
        "estimator_name",
        "estimator_version",
        "parameters",
        "converged",
        "objective_history",
        "configuration_digest",
        "artifact_digest",
        "n_iterations",
        "n_start_points",
        "runtime_seconds",
    }


def test_parameter_prior_types() -> None:
    assert "gaussian" in PRIOR_TYPES
    prior = ParameterPrior(
        parameter_id="ur.payload.mass",
        prior_type="gaussian",
        mean=1.0,
        std=0.1,
        bounds=(0.5, 3.0),
    )
    assert prior.to_dict()["prior_type"] == "gaussian"
    with pytest.raises(EstimatorProtocolError, match="prior_type"):
        ParameterPrior(
            parameter_id="ur.payload.mass",
            prior_type="beta",
            bounds=(0.0, 1.0),
        )


def test_unversioned_estimator_rejected() -> None:
    with pytest.raises(EstimatorProtocolError, match="estimator_version"):
        EstimationResult(
            estimator_name="mock",
            estimator_version="",
            parameters=[],
            converged=True,
            objective_history=[],
            n_iterations=0,
            n_start_points=0,
            runtime_seconds=0.0,
            configuration_digest=DIGEST_A,
        )
