"""Activity fingerprint schema for the Activity-Identifiability Atlas (PR-C2).

A deterministic fingerprint of a robot activity. No learned embedding —
pure physical/kinematic descriptors only.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def _check_physical_ranges(self) -> ActivityFingerprint:
        if self.duration_s < 0:
            raise ValueError("duration_s must be non-negative")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        for name in (
            "direction_coverage",
            "gravity_pose_diversity",
            "contact_fraction",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.temperature_range is not None:
            t_lo, t_hi = self.temperature_range
            if t_lo > t_hi:
                raise ValueError("temperature_range min must be <= max")
        return self
