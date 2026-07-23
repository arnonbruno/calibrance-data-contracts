"""Dynamics signal contracts for twin evaluation and calibration (Gate H1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def _check_aligned_shapes(self) -> DynamicsSignalWindow:
        nq = len(self.joint_order)
        if nq == 0:
            raise ValueError("joint_order must not be empty")
        lengths = {len(self.q_rad), len(self.qd_rad_s), len(self.qdd_rad_s2)}
        if len(lengths) != 1:
            raise ValueError("q_rad, qd_rad_s, and qdd_rad_s2 must share the same length T")
        for name, rows in (
            ("q_rad", self.q_rad),
            ("qd_rad_s", self.qd_rad_s),
            ("qdd_rad_s2", self.qdd_rad_s2),
            ("measured_torque_nm", self.measured_torque_nm),
            ("measured_current_a", self.measured_current_a),
        ):
            if rows is None:
                continue
            for i, row in enumerate(rows):
                if len(row) != nq:
                    raise ValueError(f"{name}[{i}] must have length {nq} (joint_order)")
        return self


class TorqueResidualRecord(BaseModel):
    """Per-sample torque residual between measured and predicted torque."""

    residual_nm: list[float]
    predicted_nm: list[float]
    measured_nm: list[float]
    joint_order: tuple[str, ...]

    @model_validator(mode="after")
    def _check_lengths(self) -> TorqueResidualRecord:
        n = len(self.joint_order)
        for name in ("residual_nm", "predicted_nm", "measured_nm"):
            if len(getattr(self, name)) != n:
                raise ValueError(f"{name} must match joint_order length")
        return self


class CurrentResidualRecord(BaseModel):
    """Per-sample current residual between measured and predicted current."""

    residual_a: list[float]
    predicted_a: list[float]
    measured_a: list[float]
    joint_order: tuple[str, ...]

    @model_validator(mode="after")
    def _check_lengths(self) -> CurrentResidualRecord:
        n = len(self.joint_order)
        for name in ("residual_a", "predicted_a", "measured_a"):
            if len(getattr(self, name)) != n:
                raise ValueError(f"{name} must match joint_order length")
        return self
