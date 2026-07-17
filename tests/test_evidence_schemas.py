"""Tests for evidence and capability schemas."""
import pytest
from calibrance_data_contracts.evidence import (
    EvidenceLevel, DiagnosticStatus, ReasonCode, CapabilityID,
    TriState, CapabilityDeclaration, CapabilityPolicy, SupportedEnvelope,
    CapabilityClaim, UncertaintyDecomposition, ModelBundleManifest,
    EvidenceManifest,
)


def test_evidence_levels():
    assert EvidenceLevel.E0_CODE_VERIFIED.value == "E0"
    assert len(EvidenceLevel) == 6


def test_diagnostic_status():
    assert DiagnosticStatus.CHANGE_NOT_IDENTIFIABLE.value == "change_detected_not_identifiable"
    assert len(DiagnosticStatus) == 10


def test_reason_codes():
    assert ReasonCode.REQUIRED_CHANNEL_MISSING.value == "required_channel_missing"
    assert ReasonCode.HEAD_DISABLED.value == "head_disabled"
    assert ReasonCode.USING_RLS_ONLY.value == "using_rls_only"
    assert len(ReasonCode) == 23


def test_capability_declaration():
    cap = CapabilityDeclaration(
        capability_id=CapabilityID.PAYLOAD_CHANGE,
        name="Payload change",
        detectable=TriState.TRUE,
        diagnosable=TriState.CONDITIONAL,
        estimable=TriState.CONDITIONAL,
        required_signals=["joint_position_rad", "joint_velocity_rad_s", "joint_current_a"],
        required_excitation=["nonzero_acceleration", "multiple_joint_configurations"],
        confounders=["friction_change", "current_scale_error"],
        minimum_evidence_level=EvidenceLevel.E1_SYNTHETIC,
        limitations=["Estimate is relative to configured baseline"],
    )
    assert cap.capability_id == CapabilityID.PAYLOAD_CHANGE
    assert cap.detectable == TriState.TRUE
    assert len(cap.required_signals) == 3


def test_capability_policy():
    policy = CapabilityPolicy(
        policy_version="1.0",
        intended_use_id="ur3e-v1",
        intended_use_digest="sha256:abc123",
        capabilities=[
            CapabilityDeclaration(
                capability_id=CapabilityID.GENERIC_ANOMALY,
                name="Generic anomaly detection",
                detectable=TriState.TRUE,
            )
        ],
    )
    assert len(policy.capabilities) == 1


def test_supported_envelope():
    env = SupportedEnvelope(
        robot_models=["UR3e", "UR5e"],
        dof=6,
        sampling_rate_hz_min=100,
        sampling_rate_hz_max=500,
    )
    assert env.dof == 6
    assert "UR3e" in env.robot_models


def test_uncertainty_decomposition():
    unc = UncertaintyDecomposition(
        data_quality=0.15,
        model=0.42,
        parameter=0.71,
        identifiability=0.91,
        configuration=0.05,
        temporal=0.10,
    )
    assert unc.identifiability == 0.91


def test_model_bundle_manifest():
    manifest = ModelBundleManifest(
        model_id="calibrance-encoder-aursad",
        bundle_digest="sha256:def456",
        source_commit="abc123",
        contracts_version="0.1.0",
        feature_schema_digest="sha256:feat",
        label_vocab_digest="sha256:label",
        training_dataset_digest="sha256:data",
        split_manifest_digest="sha256:split",
        holdout_manifest_digest="sha256:holdout",
        rights_digest="sha256:rights",
        components={"encoder": {"path": "encoder.npz", "digest": "sha256:enc", "status": "present"}},
        robot_dof=6,
        supported_envelope_digest="sha256:env",
        capability_declaration_digest="sha256:cap",
        threshold_digest="sha256:thresh",
        intended_use_id="ur3e-v1",
        intended_use_digest="sha256:iu",
    )
    assert manifest.robot_dof == 6


def test_evidence_manifest():
    manifest = EvidenceManifest(
        run_id="test-run-001",
        run_digest="sha256:run",
        bundle_manifest_digest="sha256:bundle",
        split_manifest_digest="sha256:split",
        holdout_manifest_digest="sha256:holdout",
        metric_definitions_digest="sha256:metrics",
    )
    assert manifest.run_id == "test-run-001"


def test_invalid_uncertainty():
    with pytest.raises(Exception):
        UncertaintyDecomposition(data_quality=1.5, model=0, parameter=0, identifiability=0, configuration=0, temporal=0)


def test_capability_claim():
    claim = CapabilityClaim(
        capability_id=CapabilityID.PAYLOAD_CHANGE,
        allowed_action="candidate_only",
        evidence_level=EvidenceLevel.E1_SYNTHETIC,
        evidence_refs=["sha256:abc"],
    )
    assert claim.allowed_action == "candidate_only"
