"""
Provenance tracking for dataset versions and individual trajectories.

A :class:`ProvenanceRecord` captures the lineage of a data artefact — which
source it came from, which adapter / pipeline produced it, and any parent
records it was derived from.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    """
    Lineage record for a dataset version or trajectory.

    Linked from :class:`~calibrance_data_contracts.dataset.DatasetVersionManifest`
    and :class:`~calibrance_data_contracts.trajectory.CanonicalTrajectory` via
    ``provenance_record_id``.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique provenance record ID.")
    source_id: UUID = Field(..., description="Parent dataset source ID.")

    # Upstream origin
    source_uri: Optional[str] = Field(
        default=None, description="URI / path of the original upstream artefact."
    )
    source_checksum: Optional[str] = Field(
        default=None, description="SHA-256 of the original upstream artefact."
    )
    source_type: Optional[str] = Field(
        default=None,
        description="SourceType value (or free-form string) of the upstream origin.",
    )

    # Adapter / pipeline that produced this artefact
    adapter_name: str = Field(
        ..., description="Name of the ingestion adapter (e.g. 'uci_robot_failures')."
    )
    adapter_version: str = Field(
        ..., description="Semantic version of the adapter that produced this record."
    )
    pipeline_steps: list[str] = Field(
        default_factory=list,
        description="Ordered list of normalisation / transform step identifiers.",
    )

    # Lineage chain
    parent_provenance_ids: list[UUID] = Field(
        default_factory=list,
        description="IDs of parent ProvenanceRecords this record was derived from.",
    )

    # Timestamps / actor
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this provenance record was created.",
    )
    created_by: Optional[str] = Field(
        default=None, description="User or system identifier that created this record."
    )

    # Free-form
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional provenance metadata."
    )


__all__ = [
    "ProvenanceRecord",
]
