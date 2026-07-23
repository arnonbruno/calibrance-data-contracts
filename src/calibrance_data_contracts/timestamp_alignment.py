"""Timestamp alignment metadata for process/quality ingestion (P3).

Critical rule: do NOT silently force an uncertain quality result onto a
robot cycle. Record offset + uncertainty; mark alignment_uncertain when
uncertainty exceeds threshold; preserve missingness (no interpolation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

_ALIGNMENT_STATUSES: frozenset[str] = frozenset({"aligned", "alignment_uncertain"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TimestampAlignment:
    """Recorded clock offset/uncertainty between a source and target clock."""

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
        if not (self.source_clock or "").strip():
            raise ValueError("source_clock is required")
        if not (self.target_clock or "").strip():
            raise ValueError("target_clock is required")
        if not (self.method or "").strip():
            raise ValueError("method is required")
        if float(self.uncertainty_ms) < 0:
            raise ValueError("uncertainty_ms must be non-negative")
        if float(self.uncertainty_threshold_ms) < 0:
            raise ValueError("uncertainty_threshold_ms must be non-negative")
        if not 0.0 <= float(self.missing_fraction) <= 1.0:
            raise ValueError("missing_fraction must be in [0, 1]")
        if self.alignment_status not in _ALIGNMENT_STATUSES:
            raise ValueError(
                f"alignment_status must be one of {sorted(_ALIGNMENT_STATUSES)}, "
                f"got {self.alignment_status!r}"
            )
        if self.uncertainty_ms > self.uncertainty_threshold_ms:
            self.alignment_status = "alignment_uncertain"
        if self.recorded_at.tzinfo is None:
            self.recorded_at = self.recorded_at.replace(tzinfo=timezone.utc)
        self.audit_trail = [dict(e) for e in (self.audit_trail or [])]
