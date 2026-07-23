"""Process context schemas for manufacturing cycle ingestion (P3).

Process events capture job/batch/tool/mode context alongside robot telemetry.
They do not authorize robot commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

_ALIGNMENT_STATUSES: frozenset[str] = frozenset({"aligned", "alignment_uncertain"})
_CLOCK_SOURCES: frozenset[str] = frozenset({"device", "ntp", "manual"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OperatingMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    MAINTENANCE = "maintenance"
    SETUP = "setup"
    ERROR = "error"


@dataclass
class ProcessEvent:
    """Manufacturing process/cycle context linked to robot telemetry."""

    event_id: str
    tenant_id: str
    asset_id: str
    job_id: Optional[str] = None
    batch_id: Optional[str] = None
    product_variant: Optional[str] = None
    tool_id: Optional[str] = None
    payload_configuration: Optional[dict] = None
    cycle_start: Optional[datetime] = None
    cycle_end: Optional[datetime] = None
    cycle_time_s: Optional[float] = None
    operating_mode: Optional[OperatingMode] = None
    alarm_events: list[dict] = field(default_factory=list)
    stop_events: list[dict] = field(default_factory=list)
    maintenance_events: list[dict] = field(default_factory=list)
    operator_annotations: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_utc_now)
    clock_source: str = "device"  # device, ntp, manual
    estimated_offset_ms: Optional[float] = None
    alignment_uncertainty_ms: Optional[float] = None
    alignment_status: str = "aligned"  # aligned, alignment_uncertain
    source: str = "csv"  # csv, parquet, rest, mqtt
    evidence_tier: str = "synthetic"

    def __post_init__(self) -> None:
        if not (self.event_id or "").strip():
            raise ValueError("event_id is required")
        if not (self.tenant_id or "").strip():
            raise ValueError("tenant_id is required")
        if not (self.asset_id or "").strip():
            raise ValueError("asset_id is required")
        if isinstance(self.operating_mode, str):
            self.operating_mode = OperatingMode(self.operating_mode)
        if self.cycle_time_s is not None and float(self.cycle_time_s) < 0:
            raise ValueError("cycle_time_s must be non-negative")
        if (
            self.cycle_start is not None
            and self.cycle_end is not None
            and self.cycle_end < self.cycle_start
        ):
            raise ValueError("cycle_end must be >= cycle_start")
        if self.alignment_status not in _ALIGNMENT_STATUSES:
            raise ValueError(
                f"alignment_status must be one of {sorted(_ALIGNMENT_STATUSES)}, "
                f"got {self.alignment_status!r}"
            )
        if self.clock_source not in _CLOCK_SOURCES:
            raise ValueError(
                f"clock_source must be one of {sorted(_CLOCK_SOURCES)}, "
                f"got {self.clock_source!r}"
            )
        if self.alignment_uncertainty_ms is not None and float(self.alignment_uncertainty_ms) < 0:
            raise ValueError("alignment_uncertainty_ms must be non-negative")
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)
        self.alarm_events = [dict(e) for e in (self.alarm_events or [])]
        self.stop_events = [dict(e) for e in (self.stop_events or [])]
        self.maintenance_events = [dict(e) for e in (self.maintenance_events or [])]
        self.operator_annotations = list(self.operator_annotations or [])
