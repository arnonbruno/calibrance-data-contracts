"""P2 task definition schema tests."""

from __future__ import annotations

from datetime import datetime, timezone

from calibrance_data_contracts import (
    ActivityFamily,
    TaskBinding,
    TaskDefinition,
    TaskTolerance,
)


def test_activity_family_members() -> None:
    assert ActivityFamily.MACHINE_TENDING.value == "machine_tending"
    assert ActivityFamily.PRECISION_ASSEMBLY.value == "precision_assembly"
    assert len(ActivityFamily) == 10


def test_task_definition_round_trip() -> None:
    task = TaskDefinition(
        task_id="task-mt-001",
        name="Machine tending cell A",
        activity_family=ActivityFamily.MACHINE_TENDING,
        robot_model="UR3e",
        tool_configuration={"tool_type": "gripper", "tcp_offset_mm": [0, 0, 120]},
        payload_range_kg=(0.1, 2.0),
        workspace_region={"region_id": "cell_a", "bbox_m": [0, 0, 0, 0.8, 0.6, 0.5]},
        speed_range_m_s=(0.05, 0.5),
        acceleration_range_m_s2=(0.1, 2.0),
        required_signals=["actual_q", "actual_TCP_pose", "actual_current"],
        relevant_parameter_groups=["friction", "payload"],
        tolerances=TaskTolerance(
            position_tolerance_mm=2.0,
            orientation_tolerance_deg=1.0,
            torque_tolerance_pct=10.0,
            cycle_time_tolerance_pct=15.0,
        ),
        intended_monitoring_use="Detect twin drift during CNC load/unload cycles",
        version="1.0.0",
        created_at=datetime(2026, 7, 23, tzinfo=timezone.utc),
        created_by="engineer@example.com",
        immutable=False,
    )
    assert task.task_id == "task-mt-001"
    assert task.activity_family is ActivityFamily.MACHINE_TENDING
    assert task.tolerances.position_tolerance_mm == 2.0
    assert task.immutable is False


def test_task_binding_fields() -> None:
    binding = TaskBinding(
        organization_id="org-1",
        site_id="site-1",
        asset_id="asset-1",
        configuration_id="cfg-digest-abc",
        task_id="task-mt-001",
        task_version="1.0.0",
        bound_at=datetime(2026, 7, 23, tzinfo=timezone.utc),
        bound_by="engineer@example.com",
    )
    assert binding.task_id == "task-mt-001"
    assert binding.configuration_id == "cfg-digest-abc"
