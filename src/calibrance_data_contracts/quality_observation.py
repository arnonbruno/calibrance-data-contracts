"""Quality observation schemas for manufacturing quality ingestion (P3).

Quality observations may link to a process cycle via process_event_id.
Uncertain timestamp alignment must never silently force a quality result
onto a robot cycle — mark alignment_uncertain instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

_ALIGNMENT_STATUSES: frozenset[str] = frozenset({"aligned", "alignment_uncertain"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class QualityObservation:
    """A single quality measurement optionally linked to a process cycle."""

    observation_id: str
    tenant_id: str
    asset_id: str
    process_event_id: Optional[str] = None  # link to process cycle
    measurement_name: str = ""
    value: float = 0.0
    unit: str = ""
    lower_tolerance: Optional[float] = None
    upper_tolerance: Optional[float] = None
    pass_fail: Optional[bool] = None
    scrap: bool = False
    rework: bool = False
    measurement_source: str = ""  # CMM, vision, manual, etc.
    timestamp: datetime = field(default_factory=_utc_now)
    original_timestamp: Optional[datetime] = None
    clock_source: str = "device"
    estimated_offset_ms: Optional[float] = None
    alignment_uncertainty_ms: Optional[float] = None
    alignment_status: str = "aligned"  # aligned, alignment_uncertain
    evidence_tier: str = "synthetic"

    def __post_init__(self) -> None:
        if not (self.observation_id or "").strip():
            raise ValueError("observation_id is required")
        if not (self.tenant_id or "").strip():
            raise ValueError("tenant_id is required")
        if not (self.asset_id or "").strip():
            raise ValueError("asset_id is required")
        if self.alignment_status not in _ALIGNMENT_STATUSES:
            raise ValueError(
                f"alignment_status must be one of {sorted(_ALIGNMENT_STATUSES)}, "
                f"got {self.alignment_status!r}"
            )
        if (
            self.lower_tolerance is not None
            and self.upper_tolerance is not None
            and float(self.lower_tolerance) > float(self.upper_tolerance)
        ):
            raise ValueError("lower_tolerance must be <= upper_tolerance")
        if self.alignment_uncertainty_ms is not None and float(self.alignment_uncertainty_ms) < 0:
            raise ValueError("alignment_uncertainty_ms must be non-negative")
        # Never silently attach an uncertain observation to a process cycle.
        if (
            self.alignment_status == "alignment_uncertain"
            and self.process_event_id
            and self.alignment_uncertainty_ms is None
        ):
            raise ValueError(
                "alignment_uncertain observations linked to a process_event_id "
                "must record alignment_uncertainty_ms"
            )
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
