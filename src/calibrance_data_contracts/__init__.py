"""
calibrance-data-contracts
=========================

Shared Pydantic v2 schemas, enums, and type definitions for the Calibrance
data foundry.
"""

from __future__ import annotations

from .augmentation import AugmentationConfig, AugmentationRecord
from .dataset import ArtifactRecord, DatasetSource, DatasetVersionManifest
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
from .ontology import Intervention, ObservedEvent, Outcome, RootCause
from .provenance import ProvenanceRecord
from .rights import PERMISSIVE_LICENSE_IDS, DatasetRightsPolicy, TriBool
from .signals import CanonicalSignals, QualityFlags
from .trajectory import CanonicalTrajectory, EventLabel, MediaStreamRef

__version__ = "0.1.0"

__all__ = [
    # augmentation
    "AugmentationConfig",
    "AugmentationRecord",
    # dataset
    "ArtifactRecord",
    "DatasetSource",
    "DatasetVersionManifest",
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
    # meta
    "__version__",
]
