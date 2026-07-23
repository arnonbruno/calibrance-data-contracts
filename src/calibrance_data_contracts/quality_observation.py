"""Quality observation schemas for manufacturing quality ingestion (P3).

Quality observations may link to a process cycle via process_event_id.
Uncertain timestamp alignment must never silently force a quality result
onto a robot cycle — mark alignment_uncertain instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class QualityObservation:
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
