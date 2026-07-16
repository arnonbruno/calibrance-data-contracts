"""
Diagnostic ontology enums for event labels.

These enums form the controlled vocabulary for
:class:`~calibrance_data_contracts.trajectory.EventLabel` ``label_value``
fields.  The diagnostic chain is:

    ObservedEvent → RootCause → Intervention → Outcome
"""

from __future__ import annotations

from enum import Enum


class ObservedEvent(str, Enum):
    """Observable anomalous or notable events in a trajectory."""

    DRIFT = "drift"
    COLLISION = "collision"
    STALL = "stall"
    OSCILLATION = "oscillation"
    OVERSHOOT = "overshoot"
    UNDERSHOOT = "undershoot"
    SPIKE = "spike"
    DROP = "drop"
    TIMEOUT = "timeout"
    GRASP_FAILURE = "grasp_failure"
    SLIP = "slip"
    UNEXPECTED_CONTACT = "unexpected_contact"
    PATH_DEVIATION = "path_deviation"
    FORCE_LIMIT_EXCEEDED = "force_limit_exceeded"
    VELOCITY_LIMIT_EXCEEDED = "velocity_limit_exceeded"
    TEMPERATURE_ANOMALY = "temperature_anomaly"
    COMMUNICATION_LOSS = "communication_loss"
    EMERGENCY_STOP = "emergency_stop"
    NORMAL_OPERATION = "normal_operation"
    UNKNOWN = "unknown"


class RootCause(str, Enum):
    """Underlying causes attributed to an observed event."""

    SENSOR_BIAS = "sensor_bias"
    SENSOR_NOISE = "sensor_noise"
    SENSOR_FAILURE = "sensor_failure"
    ACTUATOR_WEAR = "actuator_wear"
    ACTUATOR_FAILURE = "actuator_failure"
    CALIBRATION_ERROR = "calibration_error"
    CONTROLLER_TUNING = "controller_tuning"
    SOFTWARE_BUG = "software_bug"
    MECHANICAL_PLAY = "mechanical_play"
    MECHANICAL_FAILURE = "mechanical_failure"
    PAYLOAD_CHANGE = "payload_change"
    ENVIRONMENTAL_DISTURBANCE = "environmental_disturbance"
    THERMAL_DRIFT = "thermal_drift"
    POWER_SUPPLY_ISSUE = "power_supply_issue"
    NETWORK_LATENCY = "network_latency"
    OPERATOR_ERROR = "operator_error"
    WORKPIECE_VARIATION = "workpiece_variation"
    FRICTION_CHANGE = "friction_change"
    UNKNOWN = "unknown"


class Intervention(str, Enum):
    """Corrective or investigative actions taken in response to an event."""

    RECALIBRATE_SENSOR = "recalibrate_sensor"
    REPLACE_SENSOR = "replace_sensor"
    REPLACE_ACTUATOR = "replace_actuator"
    RETUNE_CONTROLLER = "retune_controller"
    UPDATE_FIRMWARE = "update_firmware"
    RESTART_CONTROLLER = "restart_controller"
    LUBRICATE = "lubricate"
    TIGHTEN_FASTENERS = "tighten_fasteners"
    ADJUST_PAYLOAD = "adjust_payload"
    CHANGE_TOOLPATH = "change_toolpath"
    REDUCE_SPEED = "reduce_speed"
    INCREASE_FORCE_LIMIT = "increase_force_limit"
    CLEAN_SENSOR = "clean_sensor"
    INSPECT_MECHANICAL = "inspect_mechanical"
    NO_ACTION = "no_action"
    UNKNOWN = "unknown"


class Outcome(str, Enum):
    """Result of an intervention or of the trajectory as a whole."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    DEGRADED = "degraded"
    UNCHANGED = "unchanged"
    WORSENED = "worsened"
    REQUIRES_FURTHER_ACTION = "requires_further_action"
    ABORTED = "aborted"
    UNKNOWN = "unknown"


__all__ = [
    "ObservedEvent",
    "RootCause",
    "Intervention",
    "Outcome",
]
