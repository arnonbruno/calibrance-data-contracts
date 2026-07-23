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
    position_tolerance_mm: float
    orientation_tolerance_deg: float
    torque_tolerance_pct: float
    cycle_time_tolerance_pct: float
    process_tolerance: Optional[dict] = None  # task-specific quality tolerances


@dataclass
class TaskDefinition:
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


@dataclass
class TaskBinding:
    organization_id: str
    site_id: str
    asset_id: str
    configuration_id: str  # robot config snapshot
    task_id: str
    task_version: str
    bound_at: datetime
    bound_by: str
