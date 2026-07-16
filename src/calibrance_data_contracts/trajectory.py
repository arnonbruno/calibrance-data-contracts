"""
Canonical trajectory, media stream, and event label models.

These are the core data objects produced by the normalisation layer and
consumed by augmentation, training, and evaluation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import GroundTruthMethod, LabelSource, LabelType, Modality
from .signals import CanonicalSignals, QualityFlags


class MediaStreamRef(BaseModel):
    """
    Reference to a media stream (video, depth, audio) associated with a
    trajectory.
    """

    stream_id: UUID = Field(default_factory=uuid4, description="Unique stream ID.")
    modality: Modality = Field(..., description="Modality of the stream.")
    frame_count: int = Field(default=0, ge=0, description="Number of frames.")
    fps: Optional[float] = Field(
        default=None, ge=0.0, description="Frames per second (0 = unknown)."
    )
    resolution: Optional[tuple[int, int]] = Field(
        default=None, description="(width, height) in pixels."
    )
    encoding: Optional[str] = Field(
        default=None, description="Codec / encoding (e.g. 'h264', 'vp9')."
    )
    artifact_id: Optional[UUID] = Field(
        default=None, description="FK to the ArtifactRecord storing this stream."
    )


class EventLabel(BaseModel):
    """
    A semantic label attached to (a time range within) a trajectory.

    Label types form a diagnostic chain:
        observed_event → root_cause → intervention → outcome
    """

    label_id: UUID = Field(default_factory=uuid4, description="Unique label ID.")
    label_type: LabelType = Field(..., description="Role of this label in the diagnostic chain.")
    label_value: str = Field(
        ..., description="Ontology value (e.g. 'DRIFT', 'SENSOR_BIAS', 'RECALIBRATE_SENSOR')."
    )
    label_source: LabelSource = Field(
        default=LabelSource.ALGORITHM, description="Origin of the label."
    )
    human_reviewer: Optional[str] = Field(
        default=None, description="Reviewer identifier if human-reviewed."
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score [0, 1]."
    )
    ground_truth_method: GroundTruthMethod = Field(
        default=GroundTruthMethod.UNKNOWN,
        description="Method used to establish ground truth.",
    )
    time_range: tuple[float, float] = Field(
        ...,
        description="(start, end) in seconds relative to trajectory start.",
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Free-text evidence pointers (file refs, log lines, etc.).",
    )
    ontology_version: str = Field(
        default="0.1.0", description="Version of the event/outcome ontology used."
    )


class CanonicalTrajectory(BaseModel):
    """
    A single normalised trajectory (§6.2).

    This is the canonical unit of robotic interaction data in Calibrance.
    A trajectory contains:
    - Per-step signals (positions, velocities, efforts, etc.)
    - Per-step quality flags
    - Optional media stream references
    - Optional event labels
    - Provenance metadata
    """

    trajectory_id: UUID = Field(default_factory=uuid4, description="Unique trajectory ID.")
    source_id: UUID = Field(..., description="Parent dataset source.")
    version_manifest_id: Optional[UUID] = Field(
        default=None, description="FK to the version manifest this trajectory belongs to."
    )

    # Temporal scope
    num_steps: int = Field(..., ge=1, description="Number of timesteps in this trajectory.")
    duration_s: Optional[float] = Field(
        default=None, ge=0.0, description="Total duration in seconds."
    )

    # Robot / environment description
    robot_name: Optional[str] = Field(default=None, description="Robot identifier.")
    task_description: Optional[str] = Field(default=None, description="Task description.")
    num_dofs: Optional[int] = Field(
        default=None, ge=1, description="Number of degrees of freedom."
    )

    # Per-step data (all arrays must be length == num_steps)
    signals: Optional[CanonicalSignals] = Field(
        default=None, description="Per-step canonical signals."
    )
    quality_flags: Optional[list[QualityFlags]] = Field(
        default=None, description="Per-step quality flags (length == num_steps)."
    )

    # Media
    media_streams: list[MediaStreamRef] = Field(
        default_factory=list, description="Associated media streams."
    )

    # Labels
    event_labels: list[EventLabel] = Field(
        default_factory=list, description="Event / cause / intervention / outcome labels."
    )

    # Provenance
    provenance_record_id: Optional[UUID] = Field(
        default=None, description="FK to the ProvenanceRecord for this trajectory."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this trajectory was normalised.",
    )

    # Free-form metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Trajectory-specific metadata."
    )


__all__ = [
    "CanonicalTrajectory",
    "MediaStreamRef",
    "EventLabel",
]
