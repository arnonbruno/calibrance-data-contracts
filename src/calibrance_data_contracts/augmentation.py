"""
Augmentation configuration and lineage records.

:class:`AugmentationConfig` describes *how* a transform should be applied.
:class:`AugmentationRecord` captures the lineage of an augmented trajectory
(parent → child) together with the config that produced it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import AugmentationClass, TransformClass


class AugmentationConfig(BaseModel):
    """
    Parameters for a single augmentation transform.

    Used both as a recipe (what to apply) and as a snapshot stored inside an
    :class:`AugmentationRecord` (what *was* applied).
    """

    augmentation_class: AugmentationClass = Field(
        ..., description="High-level augmentation taxonomy class."
    )
    transform_class: TransformClass = Field(..., description="Concrete transform identifier.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Transform-specific parameters (e.g. sigma, warp strength).",
    )
    intensity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Normalised intensity / strength of the transform [0, 1].",
    )
    seed: Optional[int] = Field(
        default=None, description="RNG seed for reproducibility (None = non-deterministic)."
    )
    apply_to_channels: list[str] = Field(
        default_factory=list,
        description="Canonical signal channel names this transform targets "
        "(empty = all available channels).",
    )
    label_preserving: bool = Field(
        default=True,
        description="Whether the transform is expected to preserve existing labels.",
    )


class AugmentationRecord(BaseModel):
    """
    Lineage record linking a parent trajectory to an augmented child.

    Produced by the augmentation pipeline each time a transform is applied.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique augmentation record ID.")
    parent_trajectory_id: UUID = Field(..., description="Source (pre-augmentation) trajectory ID.")
    child_trajectory_id: UUID = Field(
        ..., description="Resulting (post-augmentation) trajectory ID."
    )
    config: AugmentationConfig = Field(
        ..., description="Snapshot of the config used to produce the child."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the augmentation was applied.",
    )
    created_by: Optional[str] = Field(
        default=None, description="User or system identifier that ran the augmentation."
    )
    provenance_record_id: Optional[UUID] = Field(
        default=None, description="FK to a ProvenanceRecord for this augmentation."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional free-form metadata."
    )


__all__ = [
    "AugmentationConfig",
    "AugmentationRecord",
]
