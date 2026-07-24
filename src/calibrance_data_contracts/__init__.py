"""
calibrance-data-contracts
=========================

Shared schemas (Pydantic v2 and dataclasses), enums, and type definitions
for the Calibrance data foundry.
"""

from __future__ import annotations

from .activity_fingerprint import ActivityFingerprint
from .augmentation import AugmentationConfig, AugmentationRecord
from .calibration_outcome import CalibrationOutcomeEnvelope
from .calibration_parameters import (
    CalibrationParameterBounds,
    CalibrationParameterGroup,
    CalibrationParameterPrior,
    CalibrationParameterSpec,
    IdentifiedParameterVector,
    ParameterGroupId,
    default_ur3e_parameter_groups,
)
from .canonical_taxonomy import (
    CANONICAL_BY_ID,
    CANONICAL_PARAMETER_IDS,
    CANONICAL_PARAMETERS,
    TAXONOMY_VERSION,
    CanonicalParameter,
    get_canonical_parameter,
    is_canonical_parameter_id,
    parameters_by_group,
    taxonomy_catalogue_dict,
)
from .taxonomy_migration import (
    KNOWN_SOURCES,
    NON_CALIBRATION_IDS,
    AliasRecord,
    AmbiguousAliasError,
    TaxonomyError,
    UnknownParameterError,
    assert_acceptance_gates,
    build_alias_table,
    build_taxonomy_manifest,
    canonical_to_old_id,
    classify_parameter_id,
    deserialize_historical_profile,
    load_taxonomy_manifest,
    migration_rows,
    normalize_parameter_id,
    normalize_parameter_mapping,
    old_id_to_canonical,
    validate_alias_table,
    write_taxonomy_manifest,
)
from .candidate_validation import (
    DISPOSITION_VALUES,
    KNOWN_REJECTION_REASONS,
    REJECTION_COUNTEREXAMPLE,
    REJECTION_CROSS_TASK,
    REJECTION_MODEL_INADEQUACY,
    REJECTION_OVERFITTING,
    REJECTION_PHYSICAL,
    REJECTION_UNCERTAINTY,
    REJECTION_UNDER_CALIBRATED,
    CandidateDisposition,
    CandidateValidation,
    CandidateValidationError,
)
from .capture_context import (
    CaptureContext,
    CaptureEpoch,
    ClockQuality,
    ConfigurationFingerprint,
    GapAnnotation,
    QualityFlag,
    TimingAnnotation,
)
from .dataset import ArtifactRecord, DatasetSource, DatasetVersionManifest
from .dynamics_signals import (
    CurrentResidualRecord,
    DynamicsSignalWindow,
    TorqueResidualRecord,
)
from .economic_context import (
    CONFIDENCE_LEVELS,
    COST_FIELDS,
    EXTREME_COST_THRESHOLD,
    KNOWN_CURRENCIES,
    VALUE_STATUSES,
    AssumptionSource,
    EconomicAssumptions,
    EconomicEstimate,
    EconomicValidationError,
    assert_currency_match,
)
from .enums import (
    AugmentationClass,
    ContributionMode,
    EvidenceTier,
    GroundTruthMethod,
    HydrationLevel,
    LabelSource,
    LabelType,
    Modality,
    SignalChannel,
    SourceState,
    SourceType,
    TransformClass,
)
from .evidence import (
    CapabilityClaim,
    CapabilityDeclaration,
    CapabilityID,
    CapabilityPolicy,
    DiagnosticStatus,
    EvidenceLevel,
    EvidenceManifest,
    ModelBundleManifest,
    ReasonCode,
    SupportedEnvelope,
    TriState,
    UncertaintyDecomposition,
)
from .evidence_recommendation import (
    ACTIVE_IDENTIFICATION_AUTHORITY,
    AUTHORITY_VALUES,
    REQUIRED_CONSTRAINT_KEYS,
    EvidenceRecommendation,
    EvidenceRecommendationValidationError,
    default_constraints,
)
from .honesty import (
    ALL_PARAMETER_SOURCES,
    ALL_VALIDATION_SOURCES,
    DISPLAY_LABELS,
    FIT_ALLOWED_PARAMETER_SOURCES,
    HIGH_AUTHORITY_CREDIBILITY_LABELS,
    MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL,
    HonestyMarkingError,
    ParameterSource,
    ValidationSource,
    assert_fit_allowed_source,
    assert_fleet_prior_input_allowed,
    assert_no_high_authority_label,
    can_promote_to_fleet_prior_input,
    default_parameter_source,
    default_validation_source,
    display_label_for_parameter_source,
    estimated_by_for_response,
    max_credibility_label,
    normalize_parameter_source,
    normalize_validation_source,
    parameter_source_audit_event,
    validate_server_estimated_claim,
)
from .intervention_outcome import (
    HUMAN_DECISION_STATES,
    CalibrationRecommendation,
    CausalAttribution,
    HumanDecision,
    InterventionOutcomeChain,
    InterventionState,
    NodeProvenance,
    ObservedOutcome,
    OutcomeType,
    PhysicalIntervention,
)
from .model_adequacy import (
    ModelAdequacyClass,
    ModelAdequacyDecision,
    ModelAdequacyMetrics,
)
from .ontology import Intervention, ObservedEvent, Outcome, RootCause
from .process_context import OperatingMode, ProcessEvent
from .provenance import ProvenanceRecord
from .quality_observation import QualityObservation
from .rights import PERMISSIVE_LICENSE_IDS, DatasetRightsPolicy, TriBool
from .signals import CanonicalSignals, QualityFlags
from .task import ActivityFamily, TaskBinding, TaskDefinition, TaskTolerance
from .timestamp_alignment import TimestampAlignment
from .trajectory import CanonicalTrajectory, EventLabel, MediaStreamRef
from .twin_model import (
    JointActuatorParameters,
    JointFrictionParameters,
    LinkInertialParameters,
    TwinDynamicsContext,
    TwinParameterSet,
)

__version__ = "0.2.0"

__all__ = [
    # activity_fingerprint
    "ActivityFingerprint",
    # augmentation
    "AugmentationConfig",
    "AugmentationRecord",
    # calibration_outcome
    "CalibrationOutcomeEnvelope",
    # calibration_parameters
    "CalibrationParameterBounds",
    "CalibrationParameterGroup",
    "CalibrationParameterPrior",
    "CalibrationParameterSpec",
    "IdentifiedParameterVector",
    "ParameterGroupId",
    "default_ur3e_parameter_groups",
    # canonical_taxonomy (AUTOCAL-1 A1)
    "CANONICAL_BY_ID",
    "CANONICAL_PARAMETER_IDS",
    "CANONICAL_PARAMETERS",
    "TAXONOMY_VERSION",
    "CanonicalParameter",
    "get_canonical_parameter",
    "is_canonical_parameter_id",
    "parameters_by_group",
    "taxonomy_catalogue_dict",
    # taxonomy_migration
    "KNOWN_SOURCES",
    "NON_CALIBRATION_IDS",
    "AliasRecord",
    "AmbiguousAliasError",
    "TaxonomyError",
    "UnknownParameterError",
    "assert_acceptance_gates",
    "build_alias_table",
    "build_taxonomy_manifest",
    "canonical_to_old_id",
    "classify_parameter_id",
    "deserialize_historical_profile",
    "load_taxonomy_manifest",
    "migration_rows",
    "normalize_parameter_id",
    "normalize_parameter_mapping",
    "old_id_to_canonical",
    "validate_alias_table",
    "write_taxonomy_manifest",
    # candidate_validation
    "DISPOSITION_VALUES",
    "KNOWN_REJECTION_REASONS",
    "REJECTION_COUNTEREXAMPLE",
    "REJECTION_CROSS_TASK",
    "REJECTION_MODEL_INADEQUACY",
    "REJECTION_OVERFITTING",
    "REJECTION_PHYSICAL",
    "REJECTION_UNCERTAINTY",
    "REJECTION_UNDER_CALIBRATED",
    "CandidateDisposition",
    "CandidateValidation",
    "CandidateValidationError",
    # capture_context
    "CaptureContext",
    "CaptureEpoch",
    "ClockQuality",
    "ConfigurationFingerprint",
    "GapAnnotation",
    "QualityFlag",
    "TimingAnnotation",
    # dataset
    "ArtifactRecord",
    "DatasetSource",
    "DatasetVersionManifest",
    # dynamics_signals
    "CurrentResidualRecord",
    "DynamicsSignalWindow",
    "TorqueResidualRecord",
    # economic_context
    "COST_FIELDS",
    "CONFIDENCE_LEVELS",
    "EXTREME_COST_THRESHOLD",
    "KNOWN_CURRENCIES",
    "VALUE_STATUSES",
    "AssumptionSource",
    "EconomicAssumptions",
    "EconomicEstimate",
    "EconomicValidationError",
    "assert_currency_match",
    # enums
    "AugmentationClass",
    "ContributionMode",
    "EvidenceTier",
    "GroundTruthMethod",
    "HydrationLevel",
    "LabelSource",
    "LabelType",
    "Modality",
    "SignalChannel",
    "SourceState",
    "SourceType",
    "TransformClass",
    # evidence
    "EvidenceLevel",
    "DiagnosticStatus",
    "ReasonCode",
    "CapabilityID",
    "TriState",
    "CapabilityDeclaration",
    "CapabilityPolicy",
    "SupportedEnvelope",
    "CapabilityClaim",
    "UncertaintyDecomposition",
    "ModelBundleManifest",
    "EvidenceManifest",
    # evidence_recommendation
    "ACTIVE_IDENTIFICATION_AUTHORITY",
    "AUTHORITY_VALUES",
    "REQUIRED_CONSTRAINT_KEYS",
    "EvidenceRecommendation",
    "EvidenceRecommendationValidationError",
    "default_constraints",
    # honesty
    "ALL_PARAMETER_SOURCES",
    "ALL_VALIDATION_SOURCES",
    "DISPLAY_LABELS",
    "FIT_ALLOWED_PARAMETER_SOURCES",
    "HIGH_AUTHORITY_CREDIBILITY_LABELS",
    "MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL",
    "HonestyMarkingError",
    "ParameterSource",
    "ValidationSource",
    "assert_fit_allowed_source",
    "assert_fleet_prior_input_allowed",
    "assert_no_high_authority_label",
    "can_promote_to_fleet_prior_input",
    "default_parameter_source",
    "default_validation_source",
    "display_label_for_parameter_source",
    "estimated_by_for_response",
    "max_credibility_label",
    "normalize_parameter_source",
    "normalize_validation_source",
    "parameter_source_audit_event",
    "validate_server_estimated_claim",
    # intervention_outcome
    "HUMAN_DECISION_STATES",
    "CalibrationRecommendation",
    "CausalAttribution",
    "HumanDecision",
    "InterventionOutcomeChain",
    "InterventionState",
    "NodeProvenance",
    "ObservedOutcome",
    "OutcomeType",
    "PhysicalIntervention",
    # model_adequacy
    "ModelAdequacyClass",
    "ModelAdequacyDecision",
    "ModelAdequacyMetrics",
    # ontology
    "Intervention",
    "ObservedEvent",
    "Outcome",
    "RootCause",
    # process_context
    "OperatingMode",
    "ProcessEvent",
    # provenance
    "ProvenanceRecord",
    # quality_observation
    "QualityObservation",
    # rights
    "PERMISSIVE_LICENSE_IDS",
    "DatasetRightsPolicy",
    "TriBool",
    # signals
    "CanonicalSignals",
    "QualityFlags",
    # task
    "ActivityFamily",
    "TaskBinding",
    "TaskDefinition",
    "TaskTolerance",
    # timestamp_alignment
    "TimestampAlignment",
    # trajectory
    "CanonicalTrajectory",
    "EventLabel",
    "MediaStreamRef",
    # twin_model
    "JointActuatorParameters",
    "JointFrictionParameters",
    "LinkInertialParameters",
    "TwinDynamicsContext",
    "TwinParameterSet",
    # meta
    "__version__",
]
