"""P3 process context and quality observation schema tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from calibrance_data_contracts import (
    OperatingMode,
    ProcessEvent,
    QualityObservation,
    TimestampAlignment,
)


def test_operating_mode_members() -> None:
    assert OperatingMode.AUTO.value == "auto"
    assert OperatingMode.MAINTENANCE.value == "maintenance"
    assert len(OperatingMode) == 5


def test_process_event_round_trip() -> None:
    event = ProcessEvent(
        event_id="pe-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        job_id="job-42",
        batch_id="batch-7",
        product_variant="variant-x",
        tool_id="gripper-1",
        payload_configuration={"mass_kg": 1.2},
        cycle_start=datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
        cycle_end=datetime(2026, 7, 23, 12, 0, 45, tzinfo=timezone.utc),
        cycle_time_s=45.0,
        operating_mode=OperatingMode.AUTO,
        alarm_events=[{"code": "A1", "severity": "warn"}],
        source="csv",
        evidence_tier="synthetic",
    )
    assert event.event_id == "pe-001"
    assert event.operating_mode is OperatingMode.AUTO
    assert event.cycle_time_s == 45.0
    assert event.alarm_events[0]["code"] == "A1"
    assert event.evidence_tier == "synthetic"


def test_process_event_rejects_inverted_cycle() -> None:
    with pytest.raises(ValueError, match="cycle_end"):
        ProcessEvent(
            event_id="pe-001",
            tenant_id="tenant-a",
            asset_id="asset-1",
            cycle_start=datetime(2026, 7, 23, 12, 1, tzinfo=timezone.utc),
            cycle_end=datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
        )


def test_process_event_rejects_negative_cycle_time() -> None:
    with pytest.raises(ValueError, match="cycle_time_s"):
        ProcessEvent(
            event_id="pe-001",
            tenant_id="tenant-a",
            asset_id="asset-1",
            cycle_time_s=-1.0,
        )


def test_quality_observation_fields() -> None:
    obs = QualityObservation(
        observation_id="qo-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        process_event_id="pe-001",
        measurement_name="insert_depth",
        value=12.4,
        unit="mm",
        lower_tolerance=12.0,
        upper_tolerance=13.0,
        pass_fail=True,
        measurement_source="CMM",
        evidence_tier="synthetic",
    )
    assert obs.process_event_id == "pe-001"
    assert obs.pass_fail is True
    assert obs.scrap is False


def test_quality_observation_rejects_inverted_tolerances() -> None:
    with pytest.raises(ValueError, match="lower_tolerance"):
        QualityObservation(
            observation_id="qo-001",
            tenant_id="tenant-a",
            asset_id="asset-1",
            lower_tolerance=13.0,
            upper_tolerance=12.0,
        )


def test_quality_uncertain_link_requires_uncertainty() -> None:
    with pytest.raises(ValueError, match="alignment_uncertainty_ms"):
        QualityObservation(
            observation_id="qo-001",
            tenant_id="tenant-a",
            asset_id="asset-1",
            process_event_id="pe-001",
            alignment_status="alignment_uncertain",
        )


def test_timestamp_alignment_marks_uncertain() -> None:
    aligned = TimestampAlignment(
        source_clock="device",
        target_clock="ntp",
        offset_ms=5.0,
        uncertainty_ms=10.0,
        method="ntp",
        missing_fraction=0.0,
        uncertainty_threshold_ms=50.0,
    )
    assert aligned.alignment_status == "aligned"

    uncertain = TimestampAlignment(
        source_clock="device",
        target_clock="robot",
        offset_ms=120.0,
        uncertainty_ms=80.0,
        method="cross_correlation",
        missing_fraction=0.05,
        uncertainty_threshold_ms=50.0,
    )
    assert uncertain.alignment_status == "alignment_uncertain"


def test_timestamp_alignment_rejects_bad_missing_fraction() -> None:
    with pytest.raises(ValueError, match="missing_fraction"):
        TimestampAlignment(
            source_clock="device",
            target_clock="ntp",
            offset_ms=0.0,
            uncertainty_ms=1.0,
            method="ntp",
            missing_fraction=1.5,
        )
