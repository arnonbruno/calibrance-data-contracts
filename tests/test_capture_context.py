"""Tests for capture context, timing, and quality schemas."""

import pytest
from pydantic import ValidationError

from calibrance_data_contracts.capture_context import (
    CaptureContext,
    CaptureEpoch,
    ClockQuality,
    ConfigurationFingerprint,
    GapAnnotation,
    TimingAnnotation,
)
from calibrance_data_contracts.evidence import ReasonCode


def test_creating_capture_context_with_defaults():
    ctx = CaptureContext(capture_id="cap-001")
    assert ctx.capture_id == "cap-001"
    assert ctx.robot_model == "unknown"
    assert ctx.robot_serial == "unknown"
    assert ctx.nominal_sample_rate_hz == 500
    assert ctx.measured_sample_rate_hz is None
    assert ctx.detection_threshold == 0.5
    assert ctx.abstention_threshold == 0.5
    assert ctx.ram_mb == 3700
    assert ctx.cpu_model == "Cortex-A72"
    assert ctx.cpu_count == 4
    assert ctx.os_version == "debian_bookworm_aarch64"
    assert ctx.transport_mode == "file"
    assert isinstance(ctx.timing, TimingAnnotation)
    assert isinstance(ctx.configuration, ConfigurationFingerprint)


def test_configuration_fingerprint_bounded_strings():
    ok = ConfigurationFingerprint(
        controller_version="polyscope 5.12.3",
        firmware_digest="a" * 128,
        safety_config_hash="b" * 128,
        robot_program_hash="c" * 128,
        capture_script_version="0.2.0",
        schema_version="0.1.0",
    )
    assert ok.controller_version == "polyscope 5.12.3"
    assert len(ok.firmware_digest) == 128

    with pytest.raises(ValidationError):
        ConfigurationFingerprint(controller_version="x" * 65)

    with pytest.raises(ValidationError):
        ConfigurationFingerprint(firmware_digest="y" * 129)


def test_required_channel_missing_in_reason_code():
    assert ReasonCode.REQUIRED_CHANNEL_MISSING.value == "required_channel_missing"
    assert "required_channel_missing" in {rc.value for rc in ReasonCode}


def test_timing_annotation_defaults():
    timing = TimingAnnotation()
    assert timing.epoch == CaptureEpoch.RAW_DEVICE
    assert timing.clock_quality == ClockQuality.UNKNOWN
    assert timing.monotonic_assumption_valid is True
    assert timing.gap_representation == "none"


def test_gap_annotation():
    gap = GapAnnotation(
        gap_start_index=100,
        gap_end_index=150,
        gap_samples=50,
        start_timestamp_ns=1_000_000,
        end_timestamp_ns=1_100_000,
        gap_time_ms=0.1,
        reason="sample_rate_drop",
    )
    assert gap.gap_samples == 50
    assert gap.reason == "sample_rate_drop"
    assert gap.start_timestamp_ns == 1_000_000
