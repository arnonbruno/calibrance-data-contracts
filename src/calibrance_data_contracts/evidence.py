"""Evidence and capability schemas for the Technical Evidence Program."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EvidenceLevel(str, Enum):
    """Evidence maturity levels for capability claims."""
    E0_CODE_VERIFIED = "E0"  # Unit/property/contract/numerical/security verified
    E1_SYNTHETIC = "E1"      # Controlled simulated interventions with known parameters
    E2_REAL_DATA = "E2"      # Independently collected real data
    E3_LIVE_SHADOW = "E3"    # Connected to physical robot without affecting operation
    E4_VERIFIED = "E4"       # Diagnostic followed by controlled intervention
    E5_VALIDATED = "E5"      # Repeated across robots, sites, regimes


class DiagnosticStatus(str, Enum):
    """Possible diagnostic response states."""
    UNSUPPORTED_CONFIGURATION = "unsupported_configuration"
    INVALID_TELEMETRY = "invalid_telemetry"
    INSUFFICIENT_DATA = "insufficient_data"
    DATA_QUALITY_FAILURE = "data_quality_failure"
    MODEL_UNAVAILABLE = "model_unavailable"
    OUT_OF_DISTRIBUTION = "out_of_distribution"
    NO_CHANGE_DETECTED = "no_change_detected"
    CHANGE_NOT_IDENTIFIABLE = "change_detected_not_identifiable"
    CHANGE_CANDIDATE_CAUSES = "change_detected_candidate_causes"
    PARAMETER_ESTIMATE_AVAILABLE = "parameter_estimate_available"


class ReasonCode(str, Enum):
    """Versioned reason codes for diagnostic decisions."""
    REQUIRED_CHANNEL_MISSING = "required_channel_missing"
    INSUFFICIENT_WINDOW_LENGTH = "insufficient_window_length"
    INSUFFICIENT_ACCELERATION_DIVERSITY = "insufficient_acceleration_diversity"
    INSUFFICIENT_CONFIGURATION_DIVERSITY = "insufficient_configuration_diversity"
    UNKNOWN_CONTROLLER_VERSION = "unknown_controller_version"
    UNSUPPORTED_ROBOT_MODEL = "unsupported_robot_model"
    CONFIGURATION_FINGERPRINT_CHANGED = "configuration_fingerprint_changed"
    CLOCK_QUALITY_DEGRADED = "clock_quality_degraded"
    SAMPLE_GAP_RATE_EXCEEDED = "sample_gap_rate_exceeded"
    SEQUENCE_DISCONTINUITY = "sequence_discontinuity"
    OUTSIDE_TRAINING_ENVELOPE = "outside_training_envelope"
    HIGH_MODEL_UNCERTAINTY = "high_model_uncertainty"
    HIGH_IDENTIFIABILITY_RISK = "high_identifiability_risk"
    FAULT_CANDIDATES_CONFOUNDED = "fault_candidates_confounded"
    POSTERIOR_INTERVAL_TOO_WIDE = "posterior_interval_too_wide"
    FLEET_PRIOR_INCOMPATIBLE = "fleet_prior_incompatible"
    FLEET_PRIOR_REJECTED = "fleet_prior_rejected"
    EXTERNAL_REFERENCE_REQUIRED = "external_reference_required"
    # RC2.1 Phase 1A — disabled / experimental product heads
    HEAD_DISABLED = "head_disabled"
    HEAD_EXPERIMENTAL = "head_experimental"
    USING_DETERMINISTIC_RULES = "using_deterministic_rules"
    USING_RLS_ONLY = "using_rls_only"
    TELEMETRY_INTEGRITY_RESIDUAL = "telemetry_integrity_residual"
    # Milestone B — qualified summary_tree anomaly path
    USING_SUMMARY_TREE = "using_summary_tree"
    NEURAL_ANOMALY_DISABLED = "neural_anomaly_disabled"


class CapabilityID(str, Enum):
    """Supported capability identifiers."""
    PACKET_LOSS = "packet_loss"
    TIMING_FAULT = "timing_fault"
    SENSOR_BIAS = "sensor_bias"
    SENSOR_SCALE = "sensor_scale"
    PAYLOAD_CHANGE = "payload_change"
    COG_CHANGE = "center_of_gravity_change"
    FRICTION_CHANGE = "friction_change"
    CONTROLLER_CHANGE = "controller_change"
    TCP_OFFSET = "tcp_offset"
    BASE_FRAME_ERROR = "base_frame_error"
    ABSOLUTE_POSITION = "absolute_position_accuracy"
    GENERIC_ANOMALY = "generic_anomaly_detection"
    PARAMETER_ESTIMATION = "parameter_estimation"
    FLEET_PRIOR = "fleet_prior_application"


class TriState(str, Enum):
    """Tri-state for capability declarations."""
    TRUE = "true"
    CONDITIONAL = "conditional"
    FALSE = "false"


class CapabilityDeclaration(BaseModel):
    """A single capability declaration for a model bundle."""
    capability_id: CapabilityID
    name: str
    detectable: TriState = TriState.FALSE
    diagnosable: TriState = TriState.FALSE
    estimable: TriState = TriState.FALSE
    external_reference_required: bool = False
    required_signals: list[str] = Field(default_factory=list)
    required_excitation: list[str] = Field(default_factory=list)
    confounders: list[str] = Field(default_factory=list)
    minimum_evidence_level: EvidenceLevel = EvidenceLevel.E0_CODE_VERIFIED
    limitations: list[str] = Field(default_factory=list)


class CapabilityPolicy(BaseModel):
    """The product-wide capability policy (one per product)."""
    policy_version: str
    intended_use_id: str
    intended_use_digest: str
    capabilities: list[CapabilityDeclaration]
    prohibited_claims: list[str] = Field(default_factory=list)


class SupportedEnvelope(BaseModel):
    """Operating envelope for a model bundle."""
    robot_models: list[str]
    controller_versions: list[str] = Field(default_factory=lambda: ["*"])
    firmware_versions: list[str] = Field(default_factory=lambda: ["*"])
    dof: int = 6
    sampling_rate_hz_min: float = 0
    sampling_rate_hz_max: float = float("inf")
    signal_channels: list[str] = Field(default_factory=list)
    task_profiles: list[str] = Field(default_factory=lambda: ["*"])


class CapabilityClaim(BaseModel):
    """A runtime claim for a specific diagnostic request."""
    capability_id: CapabilityID
    allowed_action: str  # "detect", "diagnose", "estimate", "candidate_only", "refuse"
    evidence_level: EvidenceLevel
    evidence_refs: list[str] = Field(default_factory=list)


class UncertaintyDecomposition(BaseModel):
    """Uncertainty components for a diagnostic."""
    data_quality: float = Field(ge=0.0, le=1.0)
    model: float = Field(ge=0.0, le=1.0)
    parameter: float = Field(ge=0.0, le=1.0)
    identifiability: float = Field(ge=0.0, le=1.0)
    configuration: float = Field(ge=0.0, le=1.0)
    temporal: float = Field(ge=0.0, le=1.0)


class ModelBundleManifest(BaseModel):
    """Manifest for a complete model bundle."""
    bundle_schema_version: str = "1.0"
    model_id: str
    bundle_digest: str
    source_commit: str
    contracts_version: str
    feature_schema_digest: str
    label_vocab_digest: str
    training_dataset_digest: str
    split_manifest_digest: str
    holdout_manifest_digest: str
    rights_digest: str
    components: dict[str, dict]  # {name: {path, digest, status}}
    robot_dof: int
    supported_envelope_digest: str
    capability_declaration_digest: str
    threshold_digest: str
    intended_use_id: str
    intended_use_digest: str
    evidence_refs: list[str] = Field(default_factory=list)
    signature_algorithm: str = "sha256"
    signing_key_id: str = ""


class EvidenceManifest(BaseModel):
    """Manifest for an evidence run."""
    run_id: str
    run_digest: str
    bundle_manifest_digest: str
    split_manifest_digest: str
    holdout_manifest_digest: str
    scenario_manifests: list[str] = Field(default_factory=list)
    metric_definitions_digest: str
    results_summary: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
