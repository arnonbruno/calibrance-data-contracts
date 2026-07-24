"""AUTOCAL-1 A4a — versioned calibration estimator Protocol.

Any estimator (constrained NLS, WLS, RLS, future Bayesian) plugs into
``CalibrationEstimator``. Product code must not hard-code estimator-specific
APIs; A4b+ implementations satisfy this Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from calibrance_data_contracts.canonical_artifacts import (
    CalibrationDatasetManifest,
    EstimatedParameter,
    sha256_hex,
)
from calibrance_data_contracts.honesty import ParameterSource, normalize_parameter_source

PRIOR_TYPES: frozenset[str] = frozenset({"uniform", "gaussian", "none"})


class EstimatorProtocolError(ValueError):
    """Raised when estimator Protocol inputs/outputs violate hard invariants."""


@dataclass
class SupportResult:
    """Outcome of ``CalibrationEstimator.supports`` (identifiability pre-check)."""

    supported: bool
    reason: str = ""
    missing_signals: list[str] = field(default_factory=list)
    unsupported_parameters: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.supported = bool(self.supported)
        self.reason = str(self.reason or "")
        self.missing_signals = [str(s) for s in (self.missing_signals or [])]
        self.unsupported_parameters = [str(s) for s in (self.unsupported_parameters or [])]
        if not self.supported and not self.reason.strip():
            raise EstimatorProtocolError("unsupported SupportResult requires a reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported": self.supported,
            "reason": self.reason,
            "missing_signals": list(self.missing_signals),
            "unsupported_parameters": list(self.unsupported_parameters),
        }


@dataclass
class ParameterSpec:
    """Canonical parameter specification supplied to an estimator."""

    parameter_id: str  # canonical ID from A1
    current_value: float
    lower_bound: float
    upper_bound: float
    unit: str
    joint_scope: Optional[str] = None

    def __post_init__(self) -> None:
        self.parameter_id = str(self.parameter_id or "").strip()
        if not self.parameter_id:
            raise EstimatorProtocolError("parameter_id is required")
        self.unit = str(self.unit or "").strip()
        if not self.unit:
            raise EstimatorProtocolError("unit is required")
        self.current_value = float(self.current_value)
        self.lower_bound = float(self.lower_bound)
        self.upper_bound = float(self.upper_bound)
        if self.lower_bound > self.upper_bound:
            raise EstimatorProtocolError("lower_bound must be <= upper_bound")
        if self.joint_scope is not None:
            text = str(self.joint_scope).strip()
            self.joint_scope = text or None

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "current_value": self.current_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "unit": self.unit,
            "joint_scope": self.joint_scope,
        }


@dataclass
class ParameterPrior:
    """Optional prior for a parameter (uniform / gaussian / none)."""

    parameter_id: str
    prior_type: str  # "uniform" | "gaussian" | "none"
    bounds: tuple[float, float]
    mean: Optional[float] = None
    std: Optional[float] = None

    def __post_init__(self) -> None:
        self.parameter_id = str(self.parameter_id or "").strip()
        if not self.parameter_id:
            raise EstimatorProtocolError("parameter_id is required")
        self.prior_type = str(self.prior_type or "").strip().lower()
        if self.prior_type not in PRIOR_TYPES:
            raise EstimatorProtocolError(
                f"unknown prior_type: {self.prior_type!r}; allowed={sorted(PRIOR_TYPES)}"
            )
        if not isinstance(self.bounds, (tuple, list)) or len(self.bounds) != 2:
            raise EstimatorProtocolError("bounds must be a (lower, upper) pair")
        lower, upper = float(self.bounds[0]), float(self.bounds[1])
        if lower > upper:
            raise EstimatorProtocolError("prior bounds lower must be <= upper")
        self.bounds = (lower, upper)
        if self.mean is not None:
            self.mean = float(self.mean)
        if self.std is not None:
            self.std = float(self.std)
            if self.std <= 0:
                raise EstimatorProtocolError("gaussian prior std must be > 0")
        if self.prior_type == "gaussian":
            if self.mean is None or self.std is None:
                raise EstimatorProtocolError("gaussian prior requires mean and std")

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "prior_type": self.prior_type,
            "mean": self.mean,
            "std": self.std,
            "bounds": list(self.bounds),
        }


@dataclass
class EstimationContext:
    """Runtime context for a single estimation attempt (reproducibility + scope)."""

    robot_model: str
    operating_envelope: dict
    task_id: str
    task_version: str
    tool_configuration: dict
    payload_configuration: dict
    evidence_tier: str
    seed: int  # for reproducibility

    def __post_init__(self) -> None:
        self.robot_model = str(self.robot_model or "").strip()
        self.task_id = str(self.task_id or "").strip()
        self.task_version = str(self.task_version or "").strip()
        self.evidence_tier = str(self.evidence_tier or "").strip()
        if not self.robot_model:
            raise EstimatorProtocolError("robot_model is required")
        if not self.task_id:
            raise EstimatorProtocolError("task_id is required")
        if not self.task_version:
            raise EstimatorProtocolError("task_version is required")
        if not self.evidence_tier:
            raise EstimatorProtocolError("evidence_tier is required")
        self.operating_envelope = dict(self.operating_envelope or {})
        self.tool_configuration = dict(self.tool_configuration or {})
        self.payload_configuration = dict(self.payload_configuration or {})
        self.seed = int(self.seed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot_model": self.robot_model,
            "operating_envelope": dict(self.operating_envelope),
            "task_id": self.task_id,
            "task_version": self.task_version,
            "tool_configuration": dict(self.tool_configuration),
            "payload_configuration": dict(self.payload_configuration),
            "evidence_tier": self.evidence_tier,
            "seed": self.seed,
        }


@dataclass
class EstimationResult:
    """Versioned estimator output. Digests are content hashes of the artifact body."""

    estimator_name: str
    estimator_version: str
    parameters: list[EstimatedParameter]
    converged: bool
    objective_history: list[float]
    n_iterations: int
    n_start_points: int
    runtime_seconds: float
    configuration_digest: str
    artifact_digest: str = ""
    convergence_metric: Optional[float] = None
    warnings: list[str] = field(default_factory=list)
    failure_reason: Optional[str] = None

    def __post_init__(self) -> None:
        self.estimator_name = str(self.estimator_name or "").strip()
        self.estimator_version = str(self.estimator_version or "").strip()
        if not self.estimator_name:
            raise EstimatorProtocolError("estimator_name is required")
        if not self.estimator_version:
            raise EstimatorProtocolError("estimator_version is required")
        self.converged = bool(self.converged)
        self.objective_history = [float(v) for v in (self.objective_history or [])]
        self.n_iterations = int(self.n_iterations)
        self.n_start_points = int(self.n_start_points)
        self.runtime_seconds = float(self.runtime_seconds)
        if self.n_iterations < 0 or self.n_start_points < 0:
            raise EstimatorProtocolError("n_iterations and n_start_points must be >= 0")
        if self.runtime_seconds < 0:
            raise EstimatorProtocolError("runtime_seconds must be >= 0")
        if self.convergence_metric is not None:
            self.convergence_metric = float(self.convergence_metric)
        self.warnings = [str(w) for w in (self.warnings or [])]
        if self.failure_reason is not None:
            self.failure_reason = str(self.failure_reason) or None

        # Silent non-convergence is forbidden — failure must be explicit.
        if not self.converged and not (self.failure_reason or "").strip():
            raise EstimatorProtocolError(
                "non-converged EstimationResult requires failure_reason "
                "(silent_nonconvergence gate)"
            )

        config = str(self.configuration_digest or "").strip()
        if len(config) < 16:
            raise EstimatorProtocolError("configuration_digest must be a content digest")
        self.configuration_digest = config

        normalized = _normalize_estimated_parameters(self.parameters)
        self.parameters = normalized

        expected = self.compute_artifact_digest()
        if not self.artifact_digest:
            self.artifact_digest = expected
        else:
            digest = str(self.artifact_digest).strip()
            if len(digest) < 16:
                raise EstimatorProtocolError("artifact_digest must be a content digest")
            if digest != expected:
                raise EstimatorProtocolError(
                    "artifact_digest does not match canonical artifact contents"
                )
            self.artifact_digest = digest

    def _artifact_payload(self) -> dict[str, Any]:
        return {
            "estimator_name": self.estimator_name,
            "estimator_version": self.estimator_version,
            "parameters": [p.to_dict() for p in self.parameters],
            "converged": self.converged,
            "objective_history": list(self.objective_history),
            "convergence_metric": self.convergence_metric,
            "n_iterations": self.n_iterations,
            "n_start_points": self.n_start_points,
            "runtime_seconds": self.runtime_seconds,
            "warnings": list(self.warnings),
            "failure_reason": self.failure_reason,
            "configuration_digest": self.configuration_digest,
        }

    def compute_artifact_digest(self) -> str:
        return sha256_hex(self._artifact_payload())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._artifact_payload(),
            "artifact_digest": self.artifact_digest,
        }


def _normalize_estimated_parameters(
    values: Sequence[EstimatedParameter] | Sequence[Mapping[str, Any]] | None,
) -> list[EstimatedParameter]:
    items = list(values or [])
    out: list[EstimatedParameter] = []
    for item in items:
        if isinstance(item, EstimatedParameter):
            param = item
        elif isinstance(item, Mapping):
            param = EstimatedParameter(**dict(item))
        else:
            raise EstimatorProtocolError("parameters entries must be EstimatedParameter")
        # Caller-supplied values must never be stored as server estimates.
        try:
            source = normalize_parameter_source(param.source)
        except Exception as exc:  # HonestyMarkingError
            raise EstimatorProtocolError(str(exc)) from exc
        if source != ParameterSource.SERVER_ESTIMATED.value:
            raise EstimatorProtocolError(
                "EstimationResult parameters must have source=server_estimated "
                "(caller_parameters_used_as_server_estimates gate)"
            )
        # Physical validity: proposed value must lie within declared bounds.
        if not (param.lower_bound <= param.proposed_value <= param.upper_bound):
            raise EstimatorProtocolError(
                f"proposed_value for {param.parameter_id!r} outside bounds "
                f"[{param.lower_bound}, {param.upper_bound}] "
                "(physically_invalid_estimates gate)"
            )
        out.append(param)
    return out


@runtime_checkable
class CalibrationEstimator(Protocol):
    """Versioned estimator plug-in interface."""

    @property
    def estimator_name(self) -> str: ...

    @property
    def estimator_version(self) -> str: ...

    def supports(
        self,
        robot_model: str,
        parameter_ids: list[str],
        available_signals: set[str],
    ) -> SupportResult: ...

    def estimate(
        self,
        dataset_manifest: CalibrationDatasetManifest,
        parameter_specs: list[ParameterSpec],
        priors: list[ParameterPrior],
        context: EstimationContext,
    ) -> EstimationResult: ...


__all__ = [
    "PRIOR_TYPES",
    "CalibrationEstimator",
    "EstimationContext",
    "EstimationResult",
    "EstimatorProtocolError",
    "ParameterPrior",
    "ParameterSpec",
    "SupportResult",
]
