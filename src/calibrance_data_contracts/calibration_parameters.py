"""Calibration parameter identification contracts (Gate H1).

AUTOCAL-1 A1: ParameterGroupId G1–G5 labels are historical grouping only.
Persistent cross-repository identifiers live in
``calibrance_data_contracts.canonical_taxonomy`` (semantic ``ur.*`` IDs).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from calibrance_data_contracts.honesty import (
    HonestyMarkingError,
    default_parameter_source,
    normalize_parameter_source,
    validate_server_estimated_claim,
)


class ParameterGroupId(str, Enum):
    """Identifiable dynamics parameter groups for twin calibration.

    Deprecated as persistent cross-repo IDs — use semantic ``ur.*`` taxonomy IDs.
    """

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
    # Honesty markings — defaults never claim server estimation.
    parameter_source: str = Field(default_factory=default_parameter_source)
    server_estimated: bool = False
    estimator_run_id: Optional[str] = None

    @model_validator(mode="after")
    def _check_vector_lengths(self) -> IdentifiedParameterVector:
        if len(self.names) != len(self.values):
            raise ValueError("names and values must have the same length")
        if self.covariance_diag is not None and len(self.covariance_diag) != len(self.values):
            raise ValueError("covariance_diag must match values length")
        if any(v < 0 for v in (self.covariance_diag or ())):
            raise ValueError("covariance_diag entries must be non-negative")
        try:
            source = normalize_parameter_source(self.parameter_source)
            validate_server_estimated_claim(
                server_estimated=bool(self.server_estimated),
                estimator_run_id=self.estimator_run_id,
                parameter_source=source,
            )
        except HonestyMarkingError as exc:
            raise ValueError(str(exc)) from exc
        self.parameter_source = source
        if not self.server_estimated:
            self.estimator_run_id = None
        return self


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
