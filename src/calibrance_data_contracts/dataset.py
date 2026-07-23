"""
Dataset source and version manifest models.

This module defines the catalog-level objects: the :class:`DatasetSource`
(row in the source registry), the :class:`DatasetVersionManifest`
(per-version manifest produced after hydration), and the
:class:`ArtifactRecord` (individual downloadable artifact).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import HydrationLevel, SourceState, SourceType


class ArtifactRecord(BaseModel):
    """
    A single physical artifact (file) belonging to a dataset source.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique artifact ID.")
    source_id: UUID = Field(..., description="Parent dataset source ID.")
    sha256: str = Field(..., description="SHA-256 of the file content.")
    size_bytes: int = Field(..., ge=0, description="File size in bytes.")
    mime_type: str = Field(..., description="MIME type of the artifact.")
    storage_path: Optional[str] = Field(
        default=None, description="Local storage path (if downloaded)."
    )
    download_url: Optional[str] = Field(default=None, description="Original download URL.")
    etag: Optional[str] = Field(default=None, description="HTTP ETag / content hash from source.")
    last_modified: Optional[datetime] = Field(
        default=None, description="Last-modified timestamp from the upstream source."
    )


class DatasetSource(BaseModel):
    """
    A dataset source as tracked in the Calibrance source registry.

    Corresponds to §5.2 of the data foundry plan.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique source identifier.")
    source_type: SourceType = Field(..., description="Adapter / origin family.")
    name: str = Field(..., min_length=1, description="Human-readable source name.")
    description: str = Field(default="", description="Short description of the dataset.")
    url: Optional[str] = Field(default=None, description="Upstream URL for the dataset.")
    doi: Optional[str] = Field(default=None, description="DOI if available.")

    license_id: Optional[str] = Field(
        default=None, description="SPDX-style or custom licence identifier."
    )
    rights_policy_id: Optional[UUID] = Field(default=None, description="FK to DatasetRightsPolicy.")

    state: SourceState = Field(
        default=SourceState.DISCOVERED, description="Current lifecycle state."
    )
    hydration_level: HydrationLevel = Field(
        default=HydrationLevel.H0_METADATA,
        description="How much of the source has been materialised.",
    )
    relevance_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Relevance / priority score (0-100)."
    )

    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the source was first discovered.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible key-value bag for source-specific metadata.",
    )

    @field_validator("relevance_score")
    @classmethod
    def _validate_relevance(cls, v: float) -> float:
        if not 0.0 <= v <= 100.0:
            raise ValueError("relevance_score must be between 0 and 100")
        return v


class DatasetVersionManifest(BaseModel):
    """
    Version manifest for a dataset source (§5.5).

    A manifest is produced each time a source is hydrated to a new version.
    It records the counts, checksums, rights, and artifact inventory.
    """

    manifest_id: UUID = Field(default_factory=uuid4, description="Unique manifest ID.")
    source_id: UUID = Field(..., description="Parent dataset source.")
    version: str = Field(..., description="Semantic version string (e.g. '1.0.0').")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Manifest creation timestamp.",
    )

    # Counts
    num_trajectories: int = Field(default=0, ge=0, description="Number of trajectories.")
    num_steps: int = Field(default=0, ge=0, description="Total steps across all trajectories.")
    num_episodes: int = Field(default=0, ge=0, description="Number of episodes.")
    num_artifacts: int = Field(default=0, ge=0, description="Number of physical artifacts.")

    # Checksums / integrity
    sha256: Optional[str] = Field(
        default=None, description="Aggregate SHA-256 of all artifact hashes."
    )
    size_bytes: int = Field(default=0, ge=0, description="Total uncompressed size in bytes.")

    # Links
    rights_policy_id: Optional[UUID] = Field(
        default=None, description="FK to the rights policy active for this version."
    )
    provenance_record_id: Optional[UUID] = Field(
        default=None, description="FK to the provenance record for this version."
    )

    # Artifact inventory
    artifacts: list[ArtifactRecord] = Field(
        default_factory=list, description="Artifacts included in this version."
    )

    # Signal inventory: which canonical signal channels are present
    signal_channels: list[str] = Field(
        default_factory=list,
        description="Canonical signal channel names present in this version.",
    )

    # Free-form metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Version-specific metadata.")


__all__ = [
    "ArtifactRecord",
    "DatasetSource",
    "DatasetVersionManifest",
]
