"""
calibrance-data-contracts
=========================

Shared Pydantic v2 schemas, enums, and type definitions for the Calibrance
data foundry.
"""

from __future__ import annotations

from .augmentation import AugmentationConfig, AugmentationRecord
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
    EvidenceLevel,
    DiagnosticStatus,
    ReasonCode,
    CapabilityID,
    TriState,
    CapabilityDeclaration,
    CapabilityPolicy,
    SupportedEnvelope,
    CapabilityClaim,
    UncertaintyDecomposition,
    ModelBundleManifest,
    EvidenceManifest,
)
from .model_adequacy import (
    ModelAdequacyClass,
    ModelAdequacyDecision,
    ModelAdequacyMetrics,
)
from .ontology import Intervention, ObservedEvent, Outcome, RootCause
from .provenance import ProvenanceRecord
from .rights import PERMISSIVE_LICENSE_IDS, DatasetRightsPolicy, TriBool
from .signals import CanonicalSignals, QualityFlags
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
    # augmentation
    "AugmentationConfig",
    "AugmentationRecord",
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
    # provenance
    "ProvenanceRecord",
    # rights
    "PERMISSIVE_LICENSE_IDS",
    "DatasetRightsPolicy",
    "TriBool",
    # signals
    "CanonicalSignals",
    "QualityFlags",
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
