"""Dynamics signal contracts for twin evaluation and calibration (Gate H1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DynamicsSignalWindow(BaseModel):
    """Aligned joint-state window used by the dynamics twin."""

    robot_model: Literal["UR3e"]
    joint_order: tuple[str, ...]
    sample_rate_hz: float = Field(gt=0.0)
    q_rad: list[list[float]] = Field(description="Positions [T x nq].")
    qd_rad_s: list[list[float]] = Field(description="Velocities [T x nq].")
    qdd_rad_s2: list[list[float]] = Field(description="Accelerations [T x nq].")
    measured_torque_nm: list[list[float]] | None = None
    measured_current_a: list[list[float]] | None = None
    derivative_filter_digest: str
    feature_contract_digest: str


class TorqueResidualRecord(BaseModel):
    """Per-sample torque residual between measured and predicted torque."""

    residual_nm: list[float]
    predicted_nm: list[float]
    measured_nm: list[float]
    joint_order: tuple[str, ...]


class CurrentResidualRecord(BaseModel):
    """Per-sample current residual between measured and predicted current."""

    residual_a: list[float]
    predicted_a: list[float]
    measured_a: list[float]
    joint_order: tuple[str, ...]
