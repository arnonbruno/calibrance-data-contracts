"""Calibration parameter identification contracts (Gate H1)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ParameterGroupId(str, Enum):
    """Identifiable dynamics parameter groups for twin calibration."""

    G1_INERTIAL = "G1_inertial"
    G2_FRICTION = "G2_friction"
    G3_ACTUATOR = "G3_actuator"
    G4_PAYLOAD = "G4_payload"
    G5_KINEMATIC_OFFSET = "G5_kinematic_offset"


class CalibrationParameterBounds(BaseModel):
    """Box bounds for a named calibration parameter."""

    name: str
    lower: float
    upper: float
    units: str
    group: ParameterGroupId


class CalibrationParameterPrior(BaseModel):
    """Optional Gaussian prior for a calibration parameter."""

    name: str
    mean: float
    std: float = Field(gt=0.0)
    units: str
    group: ParameterGroupId


class CalibrationParameterGroup(BaseModel):
    """Named group of calibration parameters (G1–G5)."""

    group_id: ParameterGroupId
    description: str
    parameter_names: tuple[str, ...]
    identifiable: bool = True


class CalibrationParameterSpec(BaseModel):
    """Specification of the identifiable parameter vector for a twin class."""

    robot_model: Literal["UR3e"]
    parameter_names: tuple[str, ...]
    groups: list[CalibrationParameterGroup]
    bounds: list[CalibrationParameterBounds]
    priors: list[CalibrationParameterPrior] = Field(default_factory=list)
    regressor_layout: str = Field(
        default="standard_inertial_friction_actuator",
        description="Named layout for the dynamic regressor columns.",
    )


class IdentifiedParameterVector(BaseModel):
    """Point estimate plus optional covariance for identified parameters."""

    parameter_set_id: str
    names: tuple[str, ...]
    values: tuple[float, ...]
    covariance_diag: tuple[float, ...] | None = None
    method: str = "least_squares"
    active_groups: tuple[ParameterGroupId, ...] = ()


def default_ur3e_parameter_groups() -> list[CalibrationParameterGroup]:
    """Canonical G1–G5 groups for the UR3e Pinocchio twin."""
    return [
        CalibrationParameterGroup(
            group_id=ParameterGroupId.G1_INERTIAL,
            description="Link inertial parameters (mass, CoM, inertia / base params).",
            parameter_names=("link_inertials",),
        ),
        CalibrationParameterGroup(
            group_id=ParameterGroupId.G2_FRICTION,
            description="Directional Coulomb + viscous friction per joint.",
            parameter_names=("coulomb_pos_nm", "coulomb_neg_nm", "viscous_nm_s_rad"),
        ),
        CalibrationParameterGroup(
            group_id=ParameterGroupId.G3_ACTUATOR,
            description="Current-to-torque map: tau = K_tau * i + b_i.",
            parameter_names=("torque_constant_nm_per_a", "torque_bias_nm"),
        ),
        CalibrationParameterGroup(
            group_id=ParameterGroupId.G4_PAYLOAD,
            description="Declared tool payload mass and center of gravity.",
            parameter_names=("payload_mass_kg", "payload_cog_m"),
        ),
        CalibrationParameterGroup(
            group_id=ParameterGroupId.G5_KINEMATIC_OFFSET,
            description="Mounting and tool frame transforms / joint zero offsets.",
            parameter_names=("mounting_transform", "tool_transform", "joint_zero_offsets"),
            identifiable=False,
        ),
    ]
