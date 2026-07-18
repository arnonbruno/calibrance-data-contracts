"""Twin dynamics context and parameter-set contracts (Gate H1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TwinDynamicsContext(BaseModel):
    """Runtime context required to evaluate a robot dynamics twin."""

    robot_model: Literal["UR3e"]
    gravity_vector_m_s2: tuple[float, float, float] = Field(
        description="Gravity expressed in the world/base frame, m/s^2."
    )
    mounting_transform: tuple[float, ...] = Field(
        description="Row-major 4x4 base mounting transform (16 floats).",
        min_length=16,
        max_length=16,
    )
    tool_transform: tuple[float, ...] = Field(
        description="Row-major 4x4 tool/TCP transform (16 floats).",
        min_length=16,
        max_length=16,
    )
    declared_payload_mass_kg: float = Field(ge=0.0)
    declared_payload_cog_m: tuple[float, float, float]
    controller_version: str | None = None
    model_source_digest: str = Field(min_length=8, max_length=128)
    feature_contract_digest: str = Field(min_length=8, max_length=128)
    derivative_filter_digest: str = Field(min_length=8, max_length=128)
    sample_rate_hz: float = Field(gt=0.0)


class LinkInertialParameters(BaseModel):
    """Inertial parameters for a single rigid link."""

    link_name: str
    mass_kg: float = Field(gt=0.0)
    com_m: tuple[float, float, float]
    inertia_kg_m2: tuple[float, float, float, float, float, float] = Field(
        description="Inertia tensor as (ixx, ixy, ixz, iyy, iyz, izz)."
    )


class JointFrictionParameters(BaseModel):
    """Directional Coulomb + viscous friction for one joint."""

    joint_name: str
    coulomb_pos_nm: float = Field(ge=0.0)
    coulomb_neg_nm: float = Field(ge=0.0)
    viscous_nm_s_rad: float = Field(ge=0.0)


class JointActuatorParameters(BaseModel):
    """Current-to-torque mapping for one joint.

    ``tau_motor = K_tau * i + b_i`` where ``K_tau`` is
    ``torque_constant_nm_per_a * efficiency`` and ``b_i`` is ``torque_bias_nm``.
    """

    joint_name: str
    torque_constant_nm_per_a: float = Field(gt=0.0)
    torque_bias_nm: float = 0.0
    efficiency: float = Field(default=1.0, gt=0.0, le=1.0)


class TwinParameterSet(BaseModel):
    """Identified / nominal parameter set for a dynamics twin."""

    parameter_set_id: str
    robot_model: Literal["UR3e"]
    model_source_digest: str
    joint_order: tuple[str, ...]
    link_inertials: list[LinkInertialParameters]
    friction: list[JointFrictionParameters]
    actuators: list[JointActuatorParameters]
    payload_mass_kg: float = Field(default=0.0, ge=0.0)
    payload_cog_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    schema_version: str = "1.0"
