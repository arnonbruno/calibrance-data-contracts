"""Process context schemas for manufacturing cycle ingestion (P3).

Process events capture job/batch/tool/mode context alongside robot telemetry.
They do not authorize robot commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


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
