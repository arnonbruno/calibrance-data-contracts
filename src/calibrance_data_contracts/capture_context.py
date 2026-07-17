"""Typed capture context schemas — timing semantics, config fingerprint, and pipeline configuration."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ClockQuality(str, Enum):
    """Clock synchronization quality assessment."""

    SYNCHRONIZED = "synchronized"
    APPROXIMATE = "approximate"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class CaptureEpoch(str, Enum):
    """Record what already happened to each timestamp in the input pipeline."""

    RAW_DEVICE = "raw_device_nanoseconds"
    DEVICE_TO_ROBOT_OFFSET_APPLIED = "device_to_robot_offset_applied"
    CLOUD_DRIFT_CORRECTED = "cloud_drift_corrected"


class TimingAnnotation(BaseModel):
    """Timing metadata — all timestamps inherit these annotations."""

    epoch: CaptureEpoch = CaptureEpoch.RAW_DEVICE
    clock_quality: ClockQuality = ClockQuality.UNKNOWN
    monotonic_assumption_valid: bool = True
    gap_representation: str = Field(
        default="none",
        description=(
            "How missing samples are represented in this window: "
            "'none', 'mask', 'interpolated'"
        ),
    )


class ConfigurationFingerprint(BaseModel):
    """Captures exactly what software/firmware was running, bounded strings, can change on restart."""

    controller_version: str = Field(
        default="unknown",
        max_length=64,
        description="e.g., polyscope 5.12.3",
    )
    firmware_digest: str = Field(
        default="unknown",
        max_length=128,
        description="Hash of firmware build",
    )
    safety_config_hash: str = Field(
        default="unknown",
        max_length=128,
        description="Hash of safety configuration",
    )
    robot_program_hash: str = Field(
        default="unknown",
        max_length=128,
        description="Hash of currently loaded robot program",
    )
    capture_script_version: str = Field(
        default="unknown",
        max_length=64,
        description="Version of rpi_capture.py",
    )
    schema_version: str = Field(
        default="unknown",
        max_length=64,
        description="Version of data contract schema used",
    )
    controller_status: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Controller status at capture time: NORMAL, PROTECTIVE_STOP, etc.",
    )
    protective_stop_active: Optional[bool] = None
    violation_status: Optional[str] = Field(default=None, max_length=64)


class CaptureContext(BaseModel):
    """Full capture context — should be attached to every captured trajectory or replay artifact."""

    capture_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Robot
    robot_model: str = Field(default="unknown", max_length=64)
    robot_serial: str = Field(default="unknown", max_length=64)
    symlink_name: Optional[str] = Field(default=None, max_length=64)
    tcp_fixture_id: Optional[str] = Field(default=None, max_length=64)

    # Timing
    timing: TimingAnnotation = Field(default_factory=TimingAnnotation)
    nominal_sample_rate_hz: float = 500
    measured_sample_rate_hz: Optional[float] = None

    # Configuration
    configuration: ConfigurationFingerprint = Field(default_factory=ConfigurationFingerprint)

    # Pipeline
    detection_threshold: float = 0.5
    abstention_threshold: float = 0.5
    label_map_digest: Optional[str] = None
    feature_config_digest: Optional[str] = None
    intended_use_id: Optional[str] = None

    # Hardware
    ram_mb: int = 3700
    cpu_model: str = "Cortex-A72"
    cpu_count: int = 4
    os_version: str = "debian_bookworm_aarch64"

    # Transmission
    transport_mode: str = Field(
        default="file",
        description="HTTP inside campus, SFTP from Nygaard, file for local",
    )


class GapAnnotation(BaseModel):
    """Describes a gap in the telemetry sequence."""

    gap_start_index: int
    gap_end_index: int
    gap_samples: int
    start_timestamp_ns: Optional[int] = None
    end_timestamp_ns: Optional[int] = None
    gap_time_ms: Optional[float] = None
    reason: Optional[str] = None  # "thermal_throttle", "sample_rate_drop", etc.


class QualityFlag(BaseModel):
    """Quality flag for a telemetry window."""

    code: str
    severity: str = Field(default="warning", pattern="^(info|warning|error|critical)$")
    message: str = ""
    window_start: Optional[int] = None
    window_end: Optional[int] = None
