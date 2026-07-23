"""
calibrance-data-contracts
=========================

Shared Pydantic v2 schemas, enums, and type definitions for the Calibrance
data foundry.
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

__version__ = "0.1.0"

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
