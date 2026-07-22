"""Activity fingerprint schema for the Activity-Identifiability Atlas (PR-C2).

A deterministic fingerprint of a robot activity. No learned embedding —
pure physical/kinematic descriptors only.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ActivityFingerprint(BaseModel):
    """Deterministic physical/kinematic fingerprint of a robot activity."""

    fingerprint_version: str = "1.0"
    robot_model: str
    controller_major_version: str | None = None
    configuration_digest: str
    program_digest: str | None = None
    activity_family: str
    duration_s: float
    sample_rate_hz: float
    position_range_by_joint: dict[str, tuple[float, float]] = Field(default_factory=dict)
    velocity_range_by_joint: dict[str, tuple[float, float]] = Field(default_factory=dict)
    acceleration_range_by_joint: dict[str, tuple[float, float]] = Field(default_factory=dict)
    velocity_reversals_by_joint: dict[str, int] = Field(default_factory=dict)
    direction_coverage: float = 0.0
    gravity_pose_diversity: float = 0.0
    contact_fraction: float = 0.0
    temperature_range: tuple[float, float] | None = None
    channel_availability: list[str] = Field(default_factory=list)
