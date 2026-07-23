"""Timestamp alignment metadata for process/quality ingestion (P3).

Critical rule: do NOT silently force an uncertain quality result onto a
robot cycle. Record offset + uncertainty; mark alignment_uncertain when
uncertainty exceeds threshold; preserve missingness (no interpolation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TimestampAlignment:
    source_clock: str
    target_clock: str
    offset_ms: float
    uncertainty_ms: float
    method: str  # ntp, manual, cross_correlation
    missing_fraction: float
    resampling_method: Optional[str] = None
    manual_correction_applied: bool = False
    alignment_id: Optional[str] = None
    tenant_id: Optional[str] = None
    asset_id: Optional[str] = None
    alignment_status: str = "aligned"  # aligned, alignment_uncertain
    uncertainty_threshold_ms: float = 50.0
    audit_trail: list[dict] = field(default_factory=list)
    recorded_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.uncertainty_ms > self.uncertainty_threshold_ms:
            self.alignment_status = "alignment_uncertain"
