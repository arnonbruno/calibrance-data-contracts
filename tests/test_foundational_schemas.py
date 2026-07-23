"""Tests for foundational foundry schemas previously under-covered."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from calibrance_data_contracts import (
    AugmentationClass,
    AugmentationConfig,
    AugmentationRecord,
    CanonicalSignals,
    CanonicalTrajectory,
    CurrentResidualRecord,
    DatasetRightsPolicy,
    DatasetSource,
    DynamicsSignalWindow,
    EventLabel,
    HydrationLevel,
    IdentifiedParameterVector,
    Intervention,
    JointActuatorParameters,
    JointFrictionParameters,
    LabelSource,
    LabelType,
    LinkInertialParameters,
    MediaStreamRef,
    Modality,
    ModelAdequacyClass,
    ModelAdequacyDecision,
    ModelAdequacyMetrics,
    ObservedEvent,
    Outcome,
    ParameterGroupId,
    ProvenanceRecord,
    QualityFlags,
    RootCause,
    SourceState,
    SourceType,
    TorqueResidualRecord,
    TransformClass,
    TwinDynamicsContext,
    TwinParameterSet,
    __version__,
    default_ur3e_parameter_groups,
)
from calibrance_data_contracts.capture_context import QualityFlag


def test_package_version_matches_pyproject() -> None:
    assert __version__ == "0.2.0"


def test_dataset_source_and_rights() -> None:
    source = DatasetSource(
        source_type=SourceType.UCI_ROBOT_FAILURES,
        name="UCI Robot Execution Failures",
    )
    assert source.state == SourceState.DISCOVERED
    assert source.hydration_level == HydrationLevel.H0_METADATA

    policy = DatasetRightsPolicy(license_id="MIT")
    assert policy.is_auto_approvable() is True
    assert policy.is_commercial_training_allowed() is False

    blocked = DatasetRightsPolicy(license_id="MIT", personal_data_possible=True)
    assert blocked.is_auto_approvable() is False


def test_provenance_and_augmentation() -> None:
    source_id = uuid4()
    prov = ProvenanceRecord(
        source_id=source_id,
        adapter_name="uci_robot_failures",
        adapter_version="1.0.0",
    )
    assert prov.created_at.tzinfo is not None

    cfg = AugmentationConfig(
        augmentation_class=AugmentationClass.LABEL_PRESERVING,
        transform_class=TransformClass.JITTER,
        intensity=0.5,
        seed=7,
    )
    record = AugmentationRecord(
        parent_trajectory_id=uuid4(),
        child_trajectory_id=uuid4(),
        config=cfg,
    )
    assert record.config.seed == 7


def test_ontology_enum_vocabularies() -> None:
    assert ObservedEvent.DRIFT.value == "drift"
    assert RootCause.SENSOR_BIAS.value == "sensor_bias"
    assert Intervention.RECALIBRATE_SENSOR.value == "recalibrate_sensor"
    assert Outcome.SUCCESS.value == "success"


def test_trajectory_and_signals() -> None:
    source_id = uuid4()
    traj = CanonicalTrajectory(
        source_id=source_id,
        num_steps=2,
        signals=CanonicalSignals(
            joint_position_rad=[[0.0, 0.1], [0.1, 0.2]],
            timestamp_ns=[1, 2],
        ),
        quality_flags=[QualityFlags(), QualityFlags(has_nan=True, is_valid=False)],
        media_streams=[MediaStreamRef(modality=Modality.VIDEO, frame_count=10)],
        event_labels=[
            EventLabel(
                label_type=LabelType.OBSERVED_EVENT,
                label_value=ObservedEvent.DRIFT.value,
                label_source=LabelSource.ALGORITHM,
                time_range=(0.0, 1.0),
            )
        ],
    )
    assert traj.num_steps == 2
    assert traj.quality_flags is not None
    assert traj.quality_flags[1].has_nan is True


def test_event_label_rejects_inverted_time_range() -> None:
    with pytest.raises(ValidationError):
        EventLabel(
            label_type=LabelType.OUTCOME,
            label_value="success",
            time_range=(2.0, 1.0),
        )


def test_quality_flag_severity_pattern() -> None:
    flag = QualityFlag(code="gap", severity="error", message="drop")
    assert flag.severity == "error"
    with pytest.raises(ValidationError):
        QualityFlag(code="gap", severity="fatal")


def test_capture_context_timestamp_is_timezone_aware() -> None:
    from calibrance_data_contracts import CaptureContext

    ctx = CaptureContext(capture_id="cap-tz")
    assert ctx.timestamp.tzinfo is not None


def test_calibration_parameter_groups_and_vector() -> None:
    groups = default_ur3e_parameter_groups()
    assert len(groups) == 5
    assert groups[0].group_id == ParameterGroupId.G1_INERTIAL

    vec = IdentifiedParameterVector(
        parameter_set_id="ps-1",
        names=("a", "b"),
        values=(1.0, 2.0),
        covariance_diag=(0.1, 0.2),
        active_groups=(ParameterGroupId.G2_FRICTION,),
    )
    assert vec.values == (1.0, 2.0)

    with pytest.raises(ValidationError):
        IdentifiedParameterVector(
            parameter_set_id="ps-1",
            names=("a",),
            values=(1.0, 2.0),
        )


def test_twin_model_and_adequacy() -> None:
    identity = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    ctx = TwinDynamicsContext(
        robot_model="UR3e",
        gravity_vector_m_s2=(0.0, 0.0, -9.81),
        mounting_transform=identity,
        tool_transform=identity,
        declared_payload_mass_kg=0.5,
        declared_payload_cog_m=(0.0, 0.0, 0.05),
        model_source_digest="digest01",
        feature_contract_digest="digest02",
        derivative_filter_digest="digest03",
        sample_rate_hz=500.0,
    )
    assert ctx.sample_rate_hz == 500.0

    params = TwinParameterSet(
        parameter_set_id="tp-1",
        robot_model="UR3e",
        model_source_digest="digest01",
        joint_order=("shoulder_pan",),
        link_inertials=[
            LinkInertialParameters(
                link_name="base",
                mass_kg=1.0,
                com_m=(0.0, 0.0, 0.0),
                inertia_kg_m2=(1.0, 0.0, 0.0, 1.0, 0.0, 1.0),
            )
        ],
        friction=[
            JointFrictionParameters(
                joint_name="shoulder_pan",
                coulomb_pos_nm=0.1,
                coulomb_neg_nm=0.1,
                viscous_nm_s_rad=0.01,
            )
        ],
        actuators=[
            JointActuatorParameters(
                joint_name="shoulder_pan",
                torque_constant_nm_per_a=0.1,
            )
        ],
    )
    assert params.schema_version == "1.0"

    decision = ModelAdequacyDecision(
        robot_model="UR3e",
        model_class="pinocchio_ur3e",
        accepted=True,
        classification=ModelAdequacyClass.ADEQUATE,
        metrics=ModelAdequacyMetrics(
            torque_rmse_nm=0.2,
            current_rmse_a=0.05,
            torque_max_abs_nm=1.0,
            residual_whiteness_score=0.8,
            n_samples=1000,
        ),
        policy_digest="policy-1",
    )
    assert decision.accepted is True


def test_dynamics_signal_window_shape_validation() -> None:
    window = DynamicsSignalWindow(
        robot_model="UR3e",
        joint_order=("j0", "j1"),
        sample_rate_hz=125.0,
        q_rad=[[0.0, 0.1]],
        qd_rad_s=[[0.0, 0.0]],
        qdd_rad_s2=[[0.0, 0.0]],
        derivative_filter_digest="df",
        feature_contract_digest="fc",
    )
    assert len(window.q_rad) == 1

    with pytest.raises(ValidationError):
        DynamicsSignalWindow(
            robot_model="UR3e",
            joint_order=("j0", "j1"),
            sample_rate_hz=125.0,
            q_rad=[[0.0]],
            qd_rad_s=[[0.0, 0.0]],
            qdd_rad_s2=[[0.0, 0.0]],
            derivative_filter_digest="df",
            feature_contract_digest="fc",
        )

    torque = TorqueResidualRecord(
        residual_nm=[0.1, -0.1],
        predicted_nm=[1.0, 1.1],
        measured_nm=[1.1, 1.0],
        joint_order=("j0", "j1"),
    )
    assert torque.residual_nm[0] == 0.1

    current = CurrentResidualRecord(
        residual_a=[0.01],
        predicted_a=[0.5],
        measured_a=[0.51],
        joint_order=("j0",),
    )
    assert current.measured_a[0] == 0.51


def test_activity_fingerprint_rejects_bad_coverage() -> None:
    from calibrance_data_contracts import ActivityFingerprint

    with pytest.raises(ValidationError):
        ActivityFingerprint(
            robot_model="UR3e",
            configuration_digest="sha256:cfg",
            activity_family="HOLD",
            duration_s=1.0,
            sample_rate_hz=125.0,
            direction_coverage=1.5,
        )


def test_evidence_manifest_timestamp_timezone() -> None:
    from calibrance_data_contracts import EvidenceManifest

    manifest = EvidenceManifest(
        run_id="run-1",
        run_digest="sha256:run",
        bundle_manifest_digest="sha256:bundle",
        split_manifest_digest="sha256:split",
        holdout_manifest_digest="sha256:holdout",
        metric_definitions_digest="sha256:metrics",
    )
    assert manifest.created_at.tzinfo is not None
    assert isinstance(manifest.created_at, datetime)
    assert manifest.created_at.tzinfo == timezone.utc or manifest.created_at.utcoffset() is not None
