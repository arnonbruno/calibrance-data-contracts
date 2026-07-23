"""Task definition and binding schemas for task-conditioned credibility (P2).

Task credibility is scoped to a concrete production task. There is no
universal robot-health score — assessments require a TaskDefinition.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ActivityFamily(str, Enum):
    MACHINE_TENDING = "machine_tending"
    PRECISION_ASSEMBLY = "precision_assembly"
    PICK_AND_PLACE = "pick_and_place"
    WELDING = "welding"
    INSPECTION = "inspection"
    PACKAGING = "packaging"
    PALLETIZING = "palletizing"
    DISPENSING = "dispensing"
    POLISHING = "polishing"
    OTHER = "other"


@dataclass
class TaskTolerance:
    """Task-specific pass/fail tolerances for monitoring and promotion gates."""

    position_tolerance_mm: float
    orientation_tolerance_deg: float
    torque_tolerance_pct: float
    cycle_time_tolerance_pct: float
    process_tolerance: Optional[dict] = None  # task-specific quality tolerances

    def __post_init__(self) -> None:
        for name in (
            "position_tolerance_mm",
            "orientation_tolerance_deg",
            "torque_tolerance_pct",
            "cycle_time_tolerance_pct",
        ):
            value = float(getattr(self, name))
            if value < 0:
                raise ValueError(f"{name} must be non-negative")


def _validate_range(name: str, bounds: tuple[float, float]) -> None:
    if len(bounds) != 2:
        raise ValueError(f"{name} must be a (min, max) pair")
    lo, hi = float(bounds[0]), float(bounds[1])
    if lo > hi:
        raise ValueError(f"{name} min must be <= max (got {bounds!r})")


@dataclass
class TaskDefinition:
    """Immutable-capable definition of a concrete production monitoring task."""

    task_id: str
    name: str
    activity_family: ActivityFamily
    robot_model: str  # e.g., "UR3e"
    tool_configuration: dict  # tool type, TCP offset, etc.
    payload_range_kg: tuple[float, float]  # min, max
    workspace_region: dict  # bounding box or description
    speed_range_m_s: tuple[float, float]
    acceleration_range_m_s2: tuple[float, float]
    required_signals: list[str]  # RTDE signals needed
    relevant_parameter_groups: list[str]  # which calibration parameters matter
    tolerances: TaskTolerance
    intended_monitoring_use: str  # description of how monitoring is used
    version: str = "1.0.0"
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    immutable: bool = False  # becomes true when used in signed evidence

    def __post_init__(self) -> None:
        if not (self.task_id or "").strip():
            raise ValueError("task_id is required")
        if not (self.name or "").strip():
            raise ValueError("name is required")
        if not (self.robot_model or "").strip():
            raise ValueError("robot_model is required")
        if isinstance(self.activity_family, str):
            self.activity_family = ActivityFamily(self.activity_family)
        _validate_range("payload_range_kg", self.payload_range_kg)
        _validate_range("speed_range_m_s", self.speed_range_m_s)
        _validate_range("acceleration_range_m_s2", self.acceleration_range_m_s2)
        if float(self.payload_range_kg[0]) < 0:
            raise ValueError("payload_range_kg min must be non-negative")
        self.required_signals = list(self.required_signals or [])
        self.relevant_parameter_groups = list(self.relevant_parameter_groups or [])
        self.tool_configuration = dict(self.tool_configuration or {})
        self.workspace_region = dict(self.workspace_region or {})


@dataclass
class TaskBinding:
    """Binding of a TaskDefinition version to a concrete asset configuration."""

    organization_id: str
    site_id: str
    asset_id: str
    configuration_id: str  # robot config snapshot
    task_id: str
    task_version: str
    bound_at: datetime
    bound_by: str

    def __post_init__(self) -> None:
        for name in (
            "organization_id",
            "site_id",
            "asset_id",
            "configuration_id",
            "task_id",
            "task_version",
            "bound_by",
        ):
            if not (getattr(self, name) or "").strip():
                raise ValueError(f"{name} is required")
        if self.bound_at.tzinfo is None:
            raise ValueError("bound_at must be timezone-aware")
