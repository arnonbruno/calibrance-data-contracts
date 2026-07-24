"""Canonical calibration parameter taxonomy (AUTOCAL-1 Stage A1).

Stable semantic parameter IDs are the cross-repository source of truth.
Do NOT use group labels such as "G1"–"G5" as persistent identifiers —
those remain historical aliases only (see taxonomy_migration).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

TAXONOMY_VERSION = "1.0.0"

# Semantic group labels for organization only — never used as canonical IDs.
GROUP_PAYLOAD = "payload"
GROUP_FRICTION = "friction"
GROUP_ACTUATOR = "actuator"
GROUP_SENSOR = "sensor"
GROUP_INERTIAL = "inertial"

ROBOT_SCOPE_ALL_UR_ESERIES = "all_ur_eseries"
JOINT_SCOPE_ALL = "all_joints"

DEFAULT_ESTIMATORS: tuple[str, ...] = ("constrained_nls", "wls", "rls")


@dataclass(frozen=True)
class CanonicalParameter:
    """One identifiable dynamics / calibration parameter."""

    parameter_id: str
    display_name: str
    group_id: str
    unit: str
    shape: str  # "scalar" | "vector3" | "matrix"
    robot_model_scope: str
    joint_scope: Optional[str]
    default_bounds: dict[str, float]
    physical_constraints: dict[str, Any]
    identifiability_requirements: dict[str, Any]
    supported_estimators: list[str]
    profile_type: str  # "scalar" | "vector" | "matrix"
    deprecated_aliases: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _param(
    parameter_id: str,
    *,
    display_name: str,
    group_id: str,
    unit: str,
    shape: str = "scalar",
    profile_type: str | None = None,
    joint_scope: Optional[str] = None,
    lower: float,
    upper: float,
    physical_constraints: dict[str, Any] | None = None,
    required_signals: tuple[str, ...] = ("joint_torque", "joint_position"),
    min_excitation: float = 0.5,
    deprecated_aliases: dict[str, str] | None = None,
    notes: str = "",
) -> CanonicalParameter:
    pt = profile_type or (
        "vector" if shape == "vector3" else "matrix" if shape == "matrix" else "scalar"
    )
    return CanonicalParameter(
        parameter_id=parameter_id,
        display_name=display_name,
        group_id=group_id,
        unit=unit,
        shape=shape,
        robot_model_scope=ROBOT_SCOPE_ALL_UR_ESERIES,
        joint_scope=joint_scope,
        default_bounds={"lower": lower, "upper": upper},
        physical_constraints=dict(physical_constraints or {}),
        identifiability_requirements={
            "required_signals": list(required_signals),
            "min_excitation": min_excitation,
        },
        supported_estimators=list(DEFAULT_ESTIMATORS),
        profile_type=pt,
        deprecated_aliases=dict(deprecated_aliases or {}),
        notes=notes,
    )


def _build_canonical_parameters() -> tuple[CanonicalParameter, ...]:
    """Frozen catalogue of A1 canonical parameters."""
    return (
        # --- Payload -----------------------------------------------------------
        _param(
            "ur.payload.mass",
            display_name="Payload mass",
            group_id=GROUP_PAYLOAD,
            unit="kg",
            joint_scope=None,
            lower=0.0,
            upper=50.0,
            physical_constraints={"min": 0.0, "must_be_positive": False},
            required_signals=("joint_torque", "joint_position"),
            deprecated_aliases={
                "h1": "G4_payload.payload_mass_kg",
                "h5": "G3_payload.payload_mass_kg",
                "foundry": "link_6_mass_kg",
                "p7": "payload_mass_kg",
            },
            notes=(
                "Foundry alias link_6_mass_kg is approximate: wrist-link mass is "
                "often used as a day-one payload proxy, not a true tool mass."
            ),
        ),
        _param(
            "ur.payload.center_of_mass",
            display_name="Payload center of mass",
            group_id=GROUP_PAYLOAD,
            unit="m",
            shape="vector3",
            joint_scope=None,
            lower=-0.5,
            upper=0.5,
            physical_constraints={"component_abs_max_m": 0.5},
            required_signals=("joint_torque", "joint_position"),
            deprecated_aliases={
                "h1": "G4_payload.payload_cog_m",
                "h5": "G3_payload.payload_cog_m",
            },
        ),
        _param(
            "ur.payload.center_of_mass.x",
            display_name="Payload CoM X",
            group_id=GROUP_PAYLOAD,
            unit="m",
            joint_scope=None,
            lower=-0.5,
            upper=0.5,
            physical_constraints={"abs_max_m": 0.5},
        ),
        _param(
            "ur.payload.center_of_mass.y",
            display_name="Payload CoM Y",
            group_id=GROUP_PAYLOAD,
            unit="m",
            joint_scope=None,
            lower=-0.5,
            upper=0.5,
            physical_constraints={"abs_max_m": 0.5},
        ),
        _param(
            "ur.payload.center_of_mass.z",
            display_name="Payload CoM Z",
            group_id=GROUP_PAYLOAD,
            unit="m",
            joint_scope=None,
            lower=-0.5,
            upper=0.5,
            physical_constraints={"abs_max_m": 0.5},
        ),
        # --- Joint friction ----------------------------------------------------
        _param(
            "ur.joint.friction.viscous",
            display_name="Viscous friction",
            group_id=GROUP_FRICTION,
            unit="N·m·s/rad",
            joint_scope=JOINT_SCOPE_ALL,
            lower=0.0,
            upper=50.0,
            physical_constraints={"min": 0.0, "must_be_positive": False},
            required_signals=("joint_torque", "joint_velocity"),
            deprecated_aliases={
                "h1": "G2_friction.viscous_nm_s_rad",
                "h5": "G1_friction.viscous",
                "foundry": "viscous_friction_Nms_rad",
                "p7": "friction_viscous",
            },
        ),
        _param(
            "ur.joint.friction.coulomb_positive",
            display_name="Coulomb friction (positive)",
            group_id=GROUP_FRICTION,
            unit="N·m",
            joint_scope=JOINT_SCOPE_ALL,
            lower=0.0,
            upper=50.0,
            physical_constraints={"min": 0.0},
            required_signals=("joint_torque", "joint_velocity"),
            deprecated_aliases={
                "h1": "G2_friction.coulomb_pos_nm",
                "h5": "G1_friction.coulomb_pos_nm",
                "p7": "friction_coulomb",
            },
        ),
        _param(
            "ur.joint.friction.coulomb_negative",
            display_name="Coulomb friction (negative)",
            group_id=GROUP_FRICTION,
            unit="N·m",
            joint_scope=JOINT_SCOPE_ALL,
            lower=0.0,
            upper=50.0,
            physical_constraints={"min": 0.0},
            required_signals=("joint_torque", "joint_velocity"),
            deprecated_aliases={
                "h1": "G2_friction.coulomb_neg_nm",
                "h5": "G1_friction.coulomb_neg_nm",
            },
        ),
        # --- Actuator ----------------------------------------------------------
        _param(
            "ur.actuator.torque_bias",
            display_name="Actuator torque bias",
            group_id=GROUP_ACTUATOR,
            unit="N·m",
            joint_scope=JOINT_SCOPE_ALL,
            lower=-20.0,
            upper=20.0,
            physical_constraints={},
            required_signals=("joint_torque", "joint_current"),
            deprecated_aliases={
                "h1": "G3_actuator.torque_bias_nm",
                "h5": "G2_current_bias.torque_bias_nm",
            },
        ),
        _param(
            "ur.actuator.torque_constant",
            display_name="Actuator torque constant",
            group_id=GROUP_ACTUATOR,
            unit="N·m/A",
            joint_scope=JOINT_SCOPE_ALL,
            lower=0.1,
            upper=50.0,
            physical_constraints={"min": 0.0, "must_be_positive": True},
            required_signals=("joint_torque", "joint_current"),
            deprecated_aliases={
                "h1": "G3_actuator.torque_constant_nm_per_a",
                "h5": "G4_current_scale.current_to_torque_scale",
            },
            notes=(
                "H5 current_to_torque_scale is related but not identical to Kt; "
                "mapped here as the current-to-torque scale parameter."
            ),
        ),
        _param(
            "ur.actuator.delay",
            display_name="Actuator delay",
            group_id=GROUP_ACTUATOR,
            unit="s",
            joint_scope=JOINT_SCOPE_ALL,
            lower=0.0,
            upper=0.1,
            physical_constraints={"min": 0.0},
            required_signals=("joint_torque", "joint_current", "joint_velocity"),
            min_excitation=0.3,
            deprecated_aliases={
                "h5": "G5_actuator_lag.actuator_lag_s",
            },
        ),
        # --- Sensors -----------------------------------------------------------
        _param(
            "ur.sensor.position_bias",
            display_name="Position sensor bias",
            group_id=GROUP_SENSOR,
            unit="rad",
            joint_scope=JOINT_SCOPE_ALL,
            lower=-0.1,
            upper=0.1,
            physical_constraints={},
            required_signals=("joint_position",),
            min_excitation=0.2,
        ),
        _param(
            "ur.sensor.velocity_bias",
            display_name="Velocity sensor bias",
            group_id=GROUP_SENSOR,
            unit="rad/s",
            joint_scope=JOINT_SCOPE_ALL,
            lower=-0.5,
            upper=0.5,
            physical_constraints={},
            required_signals=("joint_velocity",),
            min_excitation=0.2,
        ),
        _param(
            "ur.sensor.torque_bias",
            display_name="Torque sensor bias",
            group_id=GROUP_SENSOR,
            unit="N·m",
            joint_scope=JOINT_SCOPE_ALL,
            lower=-10.0,
            upper=10.0,
            physical_constraints={},
            required_signals=("joint_torque",),
            min_excitation=0.2,
        ),
        # --- Link inertia (per-link / joint-scoped) ----------------------------
        _param(
            "ur.link.inertia",
            display_name="Link inertia",
            group_id=GROUP_INERTIAL,
            unit="kg·m²",
            shape="matrix",
            joint_scope=JOINT_SCOPE_ALL,
            lower=1e-6,
            upper=100.0,
            physical_constraints={"min": 1e-6, "must_be_positive": True},
            required_signals=("joint_torque", "joint_position", "joint_acceleration"),
            deprecated_aliases={
                "h1": "G1_inertial.link_inertials",
                "p7": "inertia_kg_m2",
            },
        ),
    )


CANONICAL_PARAMETERS: tuple[CanonicalParameter, ...] = _build_canonical_parameters()

CANONICAL_BY_ID: Mapping[str, CanonicalParameter] = {
    p.parameter_id: p for p in CANONICAL_PARAMETERS
}

CANONICAL_PARAMETER_IDS: frozenset[str] = frozenset(CANONICAL_BY_ID)


def get_canonical_parameter(parameter_id: str) -> CanonicalParameter:
    """Return a canonical parameter or raise KeyError."""
    try:
        return CANONICAL_BY_ID[parameter_id]
    except KeyError as exc:
        raise KeyError(f"unknown canonical parameter_id: {parameter_id!r}") from exc


def is_canonical_parameter_id(parameter_id: str) -> bool:
    return parameter_id in CANONICAL_BY_ID


def parameters_by_group(group_id: str) -> tuple[CanonicalParameter, ...]:
    return tuple(p for p in CANONICAL_PARAMETERS if p.group_id == group_id)


def taxonomy_catalogue_dict() -> dict[str, Any]:
    """Serializable catalogue for manifests and evidence."""
    return {
        "version": TAXONOMY_VERSION,
        "parameters": [p.to_dict() for p in CANONICAL_PARAMETERS],
    }


__all__ = [
    "TAXONOMY_VERSION",
    "GROUP_PAYLOAD",
    "GROUP_FRICTION",
    "GROUP_ACTUATOR",
    "GROUP_SENSOR",
    "GROUP_INERTIAL",
    "ROBOT_SCOPE_ALL_UR_ESERIES",
    "JOINT_SCOPE_ALL",
    "DEFAULT_ESTIMATORS",
    "CanonicalParameter",
    "CANONICAL_PARAMETERS",
    "CANONICAL_BY_ID",
    "CANONICAL_PARAMETER_IDS",
    "get_canonical_parameter",
    "is_canonical_parameter_id",
    "parameters_by_group",
    "taxonomy_catalogue_dict",
]
