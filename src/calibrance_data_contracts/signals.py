"""
Canonical signal arrays and per-step quality flags.

:class:`CanonicalSignals` holds the normalised per-timestep signal tensors
produced by the data foundry.  Each channel is optional; companion
availability masks indicate which timesteps have valid data for that channel.

:class:`QualityFlags` is a per-timestep quality descriptor attached to a
trajectory (see :class:`~calibrance_data_contracts.trajectory.CanonicalTrajectory`).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CanonicalSignals(BaseModel):
    """
    Per-step canonical signal arrays for a trajectory.

    Array conventions:
    - Joint-level channels: ``list[list[float]]`` with shape ``(T, n_dof)``.
    - Scalar / TCP / action channels: ``list[list[float]]`` with shape
      ``(T, D)`` where ``D`` is the channel dimensionality (e.g. 7 for a
      pose quaternion+xyz, 6 for a wrench).
    - Timestamp: ``list[int]`` with shape ``(T,)`` (nanoseconds).
    - Availability masks: ``list[bool]`` with shape ``(T,)`` — ``True``
      means the corresponding timestep has valid data for that channel.
    """

    # ------------------------------------------------------------------
    # Joint-level signals
    # ------------------------------------------------------------------
    joint_position_rad: Optional[list[list[float]]] = Field(
        default=None, description="Joint positions in radians, shape (T, n_dof)."
    )
    joint_velocity_rad_s: Optional[list[list[float]]] = Field(
        default=None, description="Joint velocities in rad/s, shape (T, n_dof)."
    )
    joint_effort_nm: Optional[list[list[float]]] = Field(
        default=None, description="Joint efforts / torques in N·m, shape (T, n_dof)."
    )
    joint_current_a: Optional[list[list[float]]] = Field(
        default=None, description="Joint motor currents in amperes, shape (T, n_dof)."
    )
    joint_temperature_c: Optional[list[list[float]]] = Field(
        default=None, description="Joint temperatures in °C, shape (T, n_dof)."
    )
    joint_torque_nm: Optional[list[list[float]]] = Field(
        default=None, description="Measured joint torques in N·m, shape (T, n_dof)."
    )

    # ------------------------------------------------------------------
    # TCP / end-effector
    # ------------------------------------------------------------------
    tcp_pose: Optional[list[list[float]]] = Field(
        default=None, description="TCP pose [x,y,z,qx,qy,qz,qw], shape (T, 7)."
    )
    tcp_wrench: Optional[list[list[float]]] = Field(
        default=None, description="TCP wrench [fx,fy,fz,tx,ty,tz], shape (T, 6)."
    )
    tcp_velocity: Optional[list[list[float]]] = Field(
        default=None, description="TCP linear+angular velocity, shape (T, 6)."
    )

    # ------------------------------------------------------------------
    # Gripper
    # ------------------------------------------------------------------
    gripper_position: Optional[list[list[float]]] = Field(
        default=None, description="Gripper position, shape (T, D)."
    )
    gripper_force: Optional[list[list[float]]] = Field(
        default=None, description="Gripper force, shape (T, D)."
    )

    # ------------------------------------------------------------------
    # Cartesian
    # ------------------------------------------------------------------
    cartesian_position: Optional[list[list[float]]] = Field(
        default=None, description="Cartesian XYZ position, shape (T, 3)."
    )
    cartesian_orientation: Optional[list[list[float]]] = Field(
        default=None, description="Cartesian orientation quaternion, shape (T, 4)."
    )

    # ------------------------------------------------------------------
    # Robot state / controller
    # ------------------------------------------------------------------
    robot_mode: Optional[list[list[float]]] = Field(
        default=None, description="Encoded robot mode per step, shape (T, 1)."
    )
    safety_stop: Optional[list[list[float]]] = Field(
        default=None, description="Safety-stop flag (0/1) per step, shape (T, 1)."
    )
    controller_state: Optional[list[list[float]]] = Field(
        default=None, description="Encoded controller state, shape (T, D)."
    )

    # ------------------------------------------------------------------
    # Time
    # ------------------------------------------------------------------
    timestamp_ns: Optional[list[int]] = Field(
        default=None, description="Absolute timestamps in nanoseconds, shape (T,)."
    )

    # ------------------------------------------------------------------
    # Action / command
    # ------------------------------------------------------------------
    action_position: Optional[list[list[float]]] = Field(
        default=None, description="Commanded joint/TCP positions, shape (T, D)."
    )
    action_velocity: Optional[list[list[float]]] = Field(
        default=None, description="Commanded velocities, shape (T, D)."
    )
    action_torque: Optional[list[list[float]]] = Field(
        default=None, description="Commanded torques, shape (T, D)."
    )

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------
    env_temperature_c: Optional[list[list[float]]] = Field(
        default=None, description="Ambient temperature in °C, shape (T, 1)."
    )
    env_humidity: Optional[list[list[float]]] = Field(
        default=None, description="Ambient relative humidity [0,1], shape (T, 1)."
    )

    # ------------------------------------------------------------------
    # Availability masks (True = valid data present at that timestep)
    # ------------------------------------------------------------------
    joint_position_rad_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for joint_position_rad."
    )
    joint_velocity_rad_s_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for joint_velocity_rad_s."
    )
    joint_effort_nm_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for joint_effort_nm."
    )
    joint_current_a_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for joint_current_a."
    )
    joint_temperature_c_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for joint_temperature_c."
    )
    joint_torque_nm_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for joint_torque_nm."
    )
    tcp_pose_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for tcp_pose."
    )
    tcp_wrench_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for tcp_wrench."
    )
    tcp_velocity_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for tcp_velocity."
    )
    gripper_position_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for gripper_position."
    )
    gripper_force_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for gripper_force."
    )
    cartesian_position_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for cartesian_position."
    )
    cartesian_orientation_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for cartesian_orientation."
    )
    robot_mode_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for robot_mode."
    )
    safety_stop_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for safety_stop."
    )
    controller_state_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for controller_state."
    )
    timestamp_ns_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for timestamp_ns."
    )
    action_position_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for action_position."
    )
    action_velocity_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for action_velocity."
    )
    action_torque_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for action_torque."
    )
    env_temperature_c_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for env_temperature_c."
    )
    env_humidity_available: Optional[list[bool]] = Field(
        default=None, description="Availability mask for env_humidity."
    )


class QualityFlags(BaseModel):
    """
    Per-timestep quality descriptor.

    Attached as a list of length ``num_steps`` on a
    :class:`~calibrance_data_contracts.trajectory.CanonicalTrajectory`.
    """

    is_valid: bool = Field(
        default=True, description="Overall validity — False means discard this step."
    )
    has_nan: bool = Field(
        default=False, description="One or more signal values are NaN at this step."
    )
    has_inf: bool = Field(
        default=False, description="One or more signal values are Inf at this step."
    )
    has_outlier: bool = Field(
        default=False, description="Statistical outlier detected in one or more channels."
    )
    is_interpolated: bool = Field(
        default=False, description="Values at this step were filled by interpolation."
    )
    is_clipped: bool = Field(
        default=False, description="Values were clipped to a valid range."
    )
    sensor_fault: bool = Field(
        default=False, description="Upstream sensor reported a fault at this step."
    )
    timestamp_gap: bool = Field(
        default=False, description="Abnormal gap detected relative to previous timestamp."
    )
    sync_error: bool = Field(
        default=False, description="Multi-sensor synchronisation error at this step."
    )


__all__ = [
    "CanonicalSignals",
    "QualityFlags",
]
