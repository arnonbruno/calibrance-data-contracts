"""Honesty markings for parameter and validation provenance.

Until a server-side estimator exists, every caller-supplied artifact must be
marked as such. These helpers prevent misrepresentation of estimation authority.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class ParameterSource(str, Enum):
    """Where numerical parameters originated."""

    CALLER_SUPPLIED = "caller_supplied"
    SYNTHETIC_DEMO = "synthetic_demo"
    FILE_IMPORT = "file_import"
    MANUAL_OVERRIDE = "manual_override"
    SERVER_ESTIMATED = "server_estimated"


class ValidationSource(str, Enum):
    """Where validation metrics originated."""

    SERVER_COMPUTED = "server_computed"
    CALLER_SUPPLIED = "caller_supplied"
    SYNTHETIC = "synthetic"


# Sources accepted by /fit (no server estimator exists yet).
FIT_ALLOWED_PARAMETER_SOURCES: frozenset[str] = frozenset(
    {
        ParameterSource.CALLER_SUPPLIED.value,
        ParameterSource.SYNTHETIC_DEMO.value,
        ParameterSource.FILE_IMPORT.value,
        ParameterSource.MANUAL_OVERRIDE.value,
    }
)

ALL_PARAMETER_SOURCES: frozenset[str] = FIT_ALLOWED_PARAMETER_SOURCES | {
    ParameterSource.SERVER_ESTIMATED.value
}

ALL_VALIDATION_SOURCES: frozenset[str] = frozenset(s.value for s in ValidationSource)

# Labels that imply Calibrance independently verified the values.
HIGH_AUTHORITY_CREDIBILITY_LABELS: frozenset[str] = frozenset(
    {
        "calibrance_verified",
        "production_validated",
        "server_estimated",
        "automatically_calibrated",
        "auto_estimated",
    }
)

# Maximum credibility label when evidence is caller-supplied / not reproduced.
MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL = "provisional_callersupplied"

# Human-readable display strings (never claim Calibrance estimation by default).
DISPLAY_LABELS: dict[str, str] = {
    ParameterSource.CALLER_SUPPLIED.value: "Parameters supplied by user",
    ParameterSource.SYNTHETIC_DEMO.value: "Synthetic demo values",
    ParameterSource.FILE_IMPORT.value: "Manual profile import",
    ParameterSource.MANUAL_OVERRIDE.value: "Parameters supplied by user",
    ParameterSource.SERVER_ESTIMATED.value: "Server-estimated parameters",
}


class HonestyMarkingError(ValueError):
    """Raised when a request claims estimation authority it does not have."""


def default_parameter_source() -> str:
    return ParameterSource.CALLER_SUPPLIED.value


def default_validation_source() -> str:
    return ValidationSource.CALLER_SUPPLIED.value


def display_label_for_parameter_source(parameter_source: str) -> str:
    return DISPLAY_LABELS.get(parameter_source, "Parameters supplied by user")


def normalize_parameter_source(value: str | ParameterSource | None) -> str:
    if value is None or value == "":
        return default_parameter_source()
    raw = value.value if isinstance(value, ParameterSource) else str(value)
    if raw not in ALL_PARAMETER_SOURCES:
        raise HonestyMarkingError(
            f"unknown parameter_source: {raw!r}; "
            f"allowed={sorted(ALL_PARAMETER_SOURCES)}"
        )
    return raw


def normalize_validation_source(value: str | ValidationSource | None) -> str:
    if value is None or value == "":
        return default_validation_source()
    raw = value.value if isinstance(value, ValidationSource) else str(value)
    if raw not in ALL_VALIDATION_SOURCES:
        raise HonestyMarkingError(
            f"unknown validation_source: {raw!r}; "
            f"allowed={sorted(ALL_VALIDATION_SOURCES)}"
        )
    return raw


def validate_server_estimated_claim(
    *,
    server_estimated: bool,
    estimator_run_id: Optional[str],
    parameter_source: str | ParameterSource | None = None,
) -> None:
    """Reject server-estimated claims without a real estimator_run_id."""
    source = normalize_parameter_source(parameter_source)
    run_id = (estimator_run_id or "").strip() or None

    if server_estimated and not run_id:
        raise HonestyMarkingError(
            "server_estimated=true requires a non-empty estimator_run_id"
        )
    if source == ParameterSource.SERVER_ESTIMATED.value and not run_id:
        raise HonestyMarkingError(
            "parameter_source=server_estimated requires a non-empty estimator_run_id"
        )
    if run_id and not server_estimated and source != ParameterSource.SERVER_ESTIMATED.value:
        # Allow storing a run id only when claiming server estimation.
        raise HonestyMarkingError(
            "estimator_run_id may only be set when server_estimated=true "
            "or parameter_source=server_estimated"
        )
    if server_estimated and source != ParameterSource.SERVER_ESTIMATED.value:
        raise HonestyMarkingError(
            "server_estimated=true requires parameter_source=server_estimated"
        )
    if source == ParameterSource.SERVER_ESTIMATED.value and not server_estimated:
        raise HonestyMarkingError(
            "parameter_source=server_estimated requires server_estimated=true"
        )


def assert_fit_allowed_source(
    *,
    parameter_source: str | ParameterSource | None,
    server_estimated: bool = False,
    estimator_run_id: Optional[str] = None,
    credibility_label: Optional[str] = None,
) -> str:
    """Gate /fit to non-estimation workflows only. Returns normalized source."""
    source = normalize_parameter_source(parameter_source)
    if server_estimated:
        raise HonestyMarkingError(
            "server_estimated=true is rejected: no server estimator exists yet"
        )
    if source not in FIT_ALLOWED_PARAMETER_SOURCES:
        raise HonestyMarkingError(
            f"parameter_source={source!r} is not allowed on /fit; "
            f"allowed={sorted(FIT_ALLOWED_PARAMETER_SOURCES)}"
        )
    if estimator_run_id:
        raise HonestyMarkingError(
            "estimator_run_id is not accepted on /fit until a server estimator exists"
        )
    if credibility_label and credibility_label in HIGH_AUTHORITY_CREDIBILITY_LABELS:
        raise HonestyMarkingError(
            f"credibility label {credibility_label!r} implies automated calibration "
            "and is not allowed on /fit"
        )
    return source


def max_credibility_label(
    *,
    server_estimated: bool,
    independently_reproduced: bool,
    requested: Optional[str] = None,
) -> str:
    """Clamp credibility when evidence is not independently server-produced."""
    if server_estimated and independently_reproduced:
        return requested or "calibrance_verified"
    if requested and requested in HIGH_AUTHORITY_CREDIBILITY_LABELS:
        return MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL
    if requested and requested != MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL:
        # Allow weaker labels but never elevate above provisional_callersupplied.
        if requested in {
            "insufficient_evidence",
            "provisional",
            "unsupported",
            "needs_more_evidence",
            MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL,
        }:
            return requested
        return MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL
    return MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL


def assert_no_high_authority_label(
    *,
    server_estimated: bool,
    independently_reproduced: bool,
    label: Optional[str],
) -> None:
    if server_estimated and independently_reproduced:
        return
    if label and label in HIGH_AUTHORITY_CREDIBILITY_LABELS:
        raise HonestyMarkingError(
            f"label {label!r} is forbidden when server_estimated=false "
            "or independently_reproduced=false; "
            f"maximum allowed is {MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL!r}"
        )


def can_promote_to_fleet_prior_input(
    *,
    server_estimated: bool,
    independently_reproduced: bool,
) -> bool:
    """Fleet priors remain shadow_only; caller-supplied evidence is never input."""
    return bool(server_estimated and independently_reproduced)


def assert_fleet_prior_input_allowed(
    *,
    server_estimated: bool,
    independently_reproduced: bool,
) -> None:
    if not can_promote_to_fleet_prior_input(
        server_estimated=server_estimated,
        independently_reproduced=independently_reproduced,
    ):
        raise HonestyMarkingError(
            "caller-supplied or non-reproduced evidence cannot be promoted "
            "to fleet-prior input (fleet_priors remain shadow_only)"
        )


def estimated_by_for_response(*, server_estimated: bool) -> Optional[str]:
    """API responses must never claim estimated_by=calibrance when not server-estimated."""
    if server_estimated:
        return "calibrance"
    return None


def parameter_source_audit_event(
    *,
    parameter_source: str,
    server_estimated: bool,
    supplied_by: str,
    estimator_run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "event_type": "profile_parameter_source",
        "parameter_source": parameter_source,
        "server_estimated": bool(server_estimated),
        "supplied_by": supplied_by,
    }
    if timestamp is not None:
        event["timestamp"] = timestamp
    if estimator_run_id is not None:
        event["estimator_run_id"] = estimator_run_id
    return event


__all__ = [
    "ALL_PARAMETER_SOURCES",
    "ALL_VALIDATION_SOURCES",
    "DISPLAY_LABELS",
    "FIT_ALLOWED_PARAMETER_SOURCES",
    "HIGH_AUTHORITY_CREDIBILITY_LABELS",
    "MAX_CALLER_SUPPLIED_CREDIBILITY_LABEL",
    "HonestyMarkingError",
    "ParameterSource",
    "ValidationSource",
    "assert_fit_allowed_source",
    "assert_fleet_prior_input_allowed",
    "assert_no_high_authority_label",
    "can_promote_to_fleet_prior_input",
    "default_parameter_source",
    "default_validation_source",
    "display_label_for_parameter_source",
    "estimated_by_for_response",
    "max_credibility_label",
    "normalize_parameter_source",
    "normalize_validation_source",
    "parameter_source_audit_event",
    "validate_server_estimated_claim",
]
