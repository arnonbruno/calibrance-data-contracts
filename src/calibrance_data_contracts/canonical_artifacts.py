"""AUTOCAL-1 A2 — canonical artifact schemas for server-side estimation.

Frozen contracts for dataset manifests, estimator runs, numerical candidates,
server validation runs, calibration workflows, and audit evidence entries.

Evidence provenance fields are first-class on every artifact. Digests are
immutable content hashes of canonical JSON payloads (sha256 hex).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from calibrance_data_contracts.enums import EvidenceTier
from calibrance_data_contracts.honesty import (
    HonestyMarkingError,
    ParameterSource,
    normalize_parameter_source,
    validate_server_estimated_claim,
)


class CanonicalArtifactError(ValueError):
    """Raised when an AUTOCAL artifact violates a hard invariant."""


# ---------------------------------------------------------------------------
# Enumerations / closed vocabularies
# ---------------------------------------------------------------------------


class SplitStrategy(str, Enum):
    CYCLE_BASED = "cycle_based"
    SESSION_BASED = "session_based"
    TIME_BLOCK = "time_block"


SPLIT_STRATEGIES: frozenset[str] = frozenset(s.value for s in SplitStrategy)


class EstimatorRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


ESTIMATOR_RUN_STATUSES: frozenset[str] = frozenset(s.value for s in EstimatorRunStatus)


class Identifiability(str, Enum):
    IDENTIFIABLE = "identifiable"
    PARTIALLY_IDENTIFIABLE = "partially_identifiable"
    NOT_IDENTIFIABLE = "not_identifiable"


IDENTIFIABILITY_VALUES: frozenset[str] = frozenset(s.value for s in Identifiability)


class CandidateStatus(str, Enum):
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    ELIGIBLE_FOR_REVIEW = "eligible_for_review"


CANDIDATE_STATUSES: frozenset[str] = frozenset(s.value for s in CandidateStatus)


class ModelAdequacyStatus(str, Enum):
    SUPPORTED = "supported"
    INADEQUATE = "inadequate"
    UNKNOWN = "unknown"


MODEL_ADEQUACY_STATUSES: frozenset[str] = frozenset(s.value for s in ModelAdequacyStatus)


class ValidationDisposition(str, Enum):
    ELIGIBLE_FOR_HUMAN_REVIEW = "eligible_for_human_review"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED = "unsupported"
    ESTIMATOR_FAILED = "estimator_failed"


VALIDATION_DISPOSITIONS: frozenset[str] = frozenset(s.value for s in ValidationDisposition)


# Distinct from honesty.ValidationSource (caller_supplied / server_computed).
# ServerValidationRun always originates from an independent server reproduction.
SERVER_VALIDATION_SOURCE = "server_reproduced"


class CalibrationWorkflowState(str, Enum):
    """A7 orchestration states — schema frozen in A2; transitions in A7."""

    DRIFT_DETECTED = "drift_detected"
    CREDIBILITY_ASSESSED = "credibility_assessed"
    DATASET_BUILDING = "dataset_building"
    DATASET_READY = "dataset_ready"
    ESTIMATING = "estimating"
    ESTIMATION_COMPLETE = "estimation_complete"
    VALIDATING = "validating"
    PENDING_HUMAN_REVIEW = "pending_human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    EVIDENCE_REQUESTED = "evidence_requested"
    ABORTED = "aborted"
    CLOSED = "closed"


WORKFLOW_STATES: frozenset[str] = frozenset(s.value for s in CalibrationWorkflowState)


class AuditEventType(str, Enum):
    DRIFT_DETECTED = "drift_detected"
    CREDIBILITY_ASSESSED = "credibility_assessed"
    DATASET_BUILT = "dataset_built"
    ESTIMATOR_RUN = "estimator_run"
    CANDIDATE_PRODUCED = "candidate_produced"
    VALIDATION_RUN = "validation_run"
    HUMAN_DECISION = "human_decision"
    EVIDENCE_REQUESTED = "evidence_requested"
    WORKFLOW_TRANSITION = "workflow_transition"
    WORKFLOW_CLOSED = "workflow_closed"


AUDIT_EVENT_TYPES: frozenset[str] = frozenset(s.value for s in AuditEventType)


EVIDENCE_TIER_VALUES: frozenset[str] = frozenset(t.value for t in EvidenceTier)


# ---------------------------------------------------------------------------
# Digest helpers (immutable content addressing)
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize a mapping to canonical UTF-8 JSON (sorted keys, no spaces)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_hex(payload: Mapping[str, Any] | bytes | str) -> str:
    if isinstance(payload, bytes):
        raw = payload
    elif isinstance(payload, str):
        raw = payload.encode("utf-8")
    else:
        raw = canonical_json_bytes(payload)
    return hashlib.sha256(raw).hexdigest()


def _require_nonempty(name: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise CanonicalArtifactError(f"{name} is required")
    return text


def _require_digest(name: str, value: Any) -> str:
    text = _require_nonempty(name, value)
    if len(text) < 16:
        raise CanonicalArtifactError(f"{name} must be a content digest (>=16 hex chars)")
    return text


def _as_str_list(name: str, value: Sequence[str] | None) -> list[str]:
    items = list(value or [])
    for item in items:
        if not str(item).strip():
            raise CanonicalArtifactError(f"{name} must not contain empty strings")
    return [str(item) for item in items]


def _as_dict(name: str, value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise CanonicalArtifactError(f"{name} must be a mapping")
    return dict(value)


def _normalize_window(name: str, value: Mapping[str, Any] | None) -> dict[str, Any]:
    window = _as_dict(name, value)
    start = window.get("start")
    end = window.get("end")
    if start is None or end is None:
        raise CanonicalArtifactError(f"{name} must include 'start' and 'end'")
    return {
        "start": str(start),
        "end": str(end),
        **{k: v for k, v in window.items() if k not in ("start", "end")},
    }


def _normalize_evidence_tier(value: str | EvidenceTier | None) -> str:
    if value is None or value == "":
        return EvidenceTier.SYNTHETIC.value
    raw = value.value if isinstance(value, EvidenceTier) else str(value)
    if raw not in EVIDENCE_TIER_VALUES:
        raise CanonicalArtifactError(
            f"unknown evidence_tier: {raw!r}; allowed={sorted(EVIDENCE_TIER_VALUES)}"
        )
    return raw


def _enum_value(enum_cls: type[Enum], value: Any, *, name: str) -> str:
    if isinstance(value, enum_cls):
        return value.value
    text = str(value)
    allowed = {m.value for m in enum_cls}
    if text not in allowed:
        raise CanonicalArtifactError(f"unknown {name}: {text!r}; allowed={sorted(allowed)}")
    return text


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------


@dataclass
class CalibrationDatasetManifest:
    """Server-controlled calibration dataset identity and split evidence."""

    dataset_id: str
    asset_id: str
    task_id: str
    task_version: str
    robot_model: str
    tool_configuration: dict
    payload_configuration: dict
    operating_envelope: dict
    telemetry_source_ids: list[str]
    process_context_ids: list[str]
    required_signals: list[str]
    available_signals: list[str]
    estimation_window: dict  # {"start": "...", "end": "..."}
    held_out_window: dict  # {"start": "...", "end": "..."}
    split_strategy: str  # cycle_based | session_based | time_block
    quality_filters: dict
    missingness_summary: dict
    evidence_tier: str  # EvidenceTier
    manifest_digest: str = ""  # sha256 of canonical contents (immutable once set)
    created_at: str = field(default_factory=_utc_now_iso)

    def __post_init__(self) -> None:
        self.dataset_id = _require_nonempty("dataset_id", self.dataset_id)
        self.asset_id = _require_nonempty("asset_id", self.asset_id)
        self.task_id = _require_nonempty("task_id", self.task_id)
        self.task_version = _require_nonempty("task_version", self.task_version)
        self.robot_model = _require_nonempty("robot_model", self.robot_model)
        self.tool_configuration = _as_dict("tool_configuration", self.tool_configuration)
        self.payload_configuration = _as_dict("payload_configuration", self.payload_configuration)
        self.operating_envelope = _as_dict("operating_envelope", self.operating_envelope)
        self.telemetry_source_ids = _as_str_list("telemetry_source_ids", self.telemetry_source_ids)
        self.process_context_ids = _as_str_list("process_context_ids", self.process_context_ids)
        self.required_signals = _as_str_list("required_signals", self.required_signals)
        self.available_signals = _as_str_list("available_signals", self.available_signals)
        self.estimation_window = _normalize_window("estimation_window", self.estimation_window)
        self.held_out_window = _normalize_window("held_out_window", self.held_out_window)
        self.split_strategy = _enum_value(SplitStrategy, self.split_strategy, name="split_strategy")
        self.quality_filters = _as_dict("quality_filters", self.quality_filters)
        self.missingness_summary = _as_dict("missingness_summary", self.missingness_summary)
        self.evidence_tier = _normalize_evidence_tier(self.evidence_tier)
        self.created_at = _require_nonempty("created_at", self.created_at)
        expected = self.compute_digest()
        if not self.manifest_digest:
            self.manifest_digest = expected
        else:
            self.manifest_digest = _require_digest("manifest_digest", self.manifest_digest)
            if self.manifest_digest != expected:
                raise CanonicalArtifactError(
                    "manifest_digest does not match canonical contents (immutable digest mismatch)"
                )

    def _digest_payload(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "task_version": self.task_version,
            "robot_model": self.robot_model,
            "tool_configuration": self.tool_configuration,
            "payload_configuration": self.payload_configuration,
            "operating_envelope": self.operating_envelope,
            "telemetry_source_ids": self.telemetry_source_ids,
            "process_context_ids": self.process_context_ids,
            "required_signals": self.required_signals,
            "available_signals": self.available_signals,
            "estimation_window": self.estimation_window,
            "held_out_window": self.held_out_window,
            "split_strategy": self.split_strategy,
            "quality_filters": self.quality_filters,
            "missingness_summary": self.missingness_summary,
            "evidence_tier": self.evidence_tier,
        }

    def compute_digest(self) -> str:
        return sha256_hex(self._digest_payload())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._digest_payload(),
            "manifest_digest": self.manifest_digest,
            "created_at": self.created_at,
        }


@dataclass
class EstimatorRun:
    """One server-side estimation attempt against a dataset manifest."""

    estimator_run_id: str
    dataset_id: str
    estimator_name: str
    estimator_version: str
    configuration_digest: str
    parameter_ids: list[str]  # canonical IDs from A1
    prior_digest: str
    status: str = EstimatorRunStatus.QUEUED.value
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    artifact_digest: Optional[str] = None

    def __post_init__(self) -> None:
        self.estimator_run_id = _require_nonempty("estimator_run_id", self.estimator_run_id)
        self.dataset_id = _require_nonempty("dataset_id", self.dataset_id)
        self.estimator_name = _require_nonempty("estimator_name", self.estimator_name)
        self.estimator_version = _require_nonempty("estimator_version", self.estimator_version)
        self.configuration_digest = _require_digest(
            "configuration_digest", self.configuration_digest
        )
        self.parameter_ids = _as_str_list("parameter_ids", self.parameter_ids)
        if not self.parameter_ids:
            raise CanonicalArtifactError("parameter_ids must be non-empty")
        self.prior_digest = _require_digest("prior_digest", self.prior_digest)
        self.status = _enum_value(EstimatorRunStatus, self.status, name="status")
        if self.artifact_digest is not None:
            self.artifact_digest = _require_digest("artifact_digest", self.artifact_digest)
        if self.status == EstimatorRunStatus.FAILED.value and not self.failure_reason:
            raise CanonicalArtifactError("failed estimator runs require failure_reason")
        if self.status == EstimatorRunStatus.COMPLETED.value and not self.artifact_digest:
            raise CanonicalArtifactError("completed estimator runs require artifact_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "estimator_run_id": self.estimator_run_id,
            "dataset_id": self.dataset_id,
            "estimator_name": self.estimator_name,
            "estimator_version": self.estimator_version,
            "configuration_digest": self.configuration_digest,
            "parameter_ids": list(self.parameter_ids),
            "prior_digest": self.prior_digest,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "failure_reason": self.failure_reason,
            "artifact_digest": self.artifact_digest,
        }


@dataclass
class EstimatedParameter:
    """One proposed parameter value with uncertainty and identifiability."""

    parameter_id: str  # canonical ID from A1
    current_value: float
    proposed_value: float
    delta: float
    unit: str
    lower_bound: float
    upper_bound: float
    standard_error: float
    identifiability: str  # identifiable | partially_identifiable | not_identifiable
    source: str  # server_estimated | caller_supplied

    def __post_init__(self) -> None:
        self.parameter_id = _require_nonempty("parameter_id", self.parameter_id)
        self.unit = _require_nonempty("unit", self.unit)
        self.current_value = float(self.current_value)
        self.proposed_value = float(self.proposed_value)
        self.delta = float(self.delta)
        self.lower_bound = float(self.lower_bound)
        self.upper_bound = float(self.upper_bound)
        self.standard_error = float(self.standard_error)
        if self.lower_bound > self.upper_bound:
            raise CanonicalArtifactError("lower_bound must be <= upper_bound")
        if self.standard_error < 0:
            raise CanonicalArtifactError("standard_error must be >= 0")
        self.identifiability = _enum_value(
            Identifiability, self.identifiability, name="identifiability"
        )
        try:
            self.source = normalize_parameter_source(self.source)
        except HonestyMarkingError as exc:
            raise CanonicalArtifactError(str(exc)) from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "delta": self.delta,
            "unit": self.unit,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "standard_error": self.standard_error,
            "identifiability": self.identifiability,
            "source": self.source,
        }


@dataclass
class NumericalCalibrationCandidate:
    """Server-estimated numerical calibration candidate awaiting validation."""

    candidate_id: str
    estimator_run_id: str  # REQUIRED — links to the estimator run
    dataset_id: str
    asset_id: str
    task_id: str
    parameter_values: list[EstimatedParameter]
    parameter_source: str = ParameterSource.SERVER_ESTIMATED.value
    server_estimated: bool = True
    model_adequacy: dict = field(default_factory=dict)
    uncertainty_status: dict = field(default_factory=dict)
    evidence_tier: str = EvidenceTier.SYNTHETIC.value
    candidate_digest: str = ""
    status: str = CandidateStatus.PENDING_VALIDATION.value

    def __post_init__(self) -> None:
        self.candidate_id = _require_nonempty("candidate_id", self.candidate_id)
        self.estimator_run_id = _require_nonempty("estimator_run_id", self.estimator_run_id)
        self.dataset_id = _require_nonempty("dataset_id", self.dataset_id)
        self.asset_id = _require_nonempty("asset_id", self.asset_id)
        self.task_id = _require_nonempty("task_id", self.task_id)
        if not self.parameter_values:
            raise CanonicalArtifactError("parameter_values must be non-empty")
        normalized: list[EstimatedParameter] = []
        for item in self.parameter_values:
            if isinstance(item, EstimatedParameter):
                normalized.append(item)
            elif isinstance(item, Mapping):
                normalized.append(EstimatedParameter(**dict(item)))
            else:
                raise CanonicalArtifactError("parameter_values entries must be EstimatedParameter")
        self.parameter_values = normalized
        try:
            self.parameter_source = normalize_parameter_source(self.parameter_source)
            validate_server_estimated_claim(
                server_estimated=bool(self.server_estimated),
                estimator_run_id=self.estimator_run_id,
                parameter_source=self.parameter_source,
            )
        except HonestyMarkingError as exc:
            raise CanonicalArtifactError(str(exc)) from exc
        if not self.server_estimated:
            raise CanonicalArtifactError(
                "NumericalCalibrationCandidate requires server_estimated=True"
            )
        if self.parameter_source != ParameterSource.SERVER_ESTIMATED.value:
            raise CanonicalArtifactError(
                "NumericalCalibrationCandidate parameter_source must be server_estimated"
            )
        self.model_adequacy = _as_dict("model_adequacy", self.model_adequacy)
        status = self.model_adequacy.get("status", ModelAdequacyStatus.UNKNOWN.value)
        self.model_adequacy["status"] = _enum_value(
            ModelAdequacyStatus, status, name="model_adequacy.status"
        )
        if "checks" not in self.model_adequacy:
            self.model_adequacy["checks"] = {}
        self.uncertainty_status = _as_dict("uncertainty_status", self.uncertainty_status)
        self.evidence_tier = _normalize_evidence_tier(self.evidence_tier)
        self.status = _enum_value(CandidateStatus, self.status, name="status")
        expected = self.compute_digest()
        if not self.candidate_digest:
            self.candidate_digest = expected
        else:
            self.candidate_digest = _require_digest("candidate_digest", self.candidate_digest)
            if self.candidate_digest != expected:
                raise CanonicalArtifactError(
                    "candidate_digest does not match canonical contents (immutable digest mismatch)"
                )

    def _digest_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "estimator_run_id": self.estimator_run_id,
            "dataset_id": self.dataset_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "parameter_values": [p.to_dict() for p in self.parameter_values],
            "parameter_source": self.parameter_source,
            "server_estimated": bool(self.server_estimated),
            "model_adequacy": self.model_adequacy,
            "uncertainty_status": self.uncertainty_status,
            "evidence_tier": self.evidence_tier,
        }

    def compute_digest(self) -> str:
        return sha256_hex(self._digest_payload())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._digest_payload(),
            "candidate_digest": self.candidate_digest,
            "status": self.status,
        }


@dataclass
class ServerValidationRun:
    """Independent server-side validation of a numerical candidate."""

    validation_run_id: str
    candidate_id: str
    held_out_dataset_digest: str  # MUST match dataset manifest digest
    metrics: dict
    task_tolerance_results: dict
    cross_task_results: dict
    physical_constraint_results: dict
    counterexample_results: dict
    model_adequacy_results: dict
    disposition: str
    artifact_digest: str
    validation_source: str = SERVER_VALIDATION_SOURCE
    independently_reproduced: bool = True

    def __post_init__(self) -> None:
        self.validation_run_id = _require_nonempty("validation_run_id", self.validation_run_id)
        self.candidate_id = _require_nonempty("candidate_id", self.candidate_id)
        self.held_out_dataset_digest = _require_digest(
            "held_out_dataset_digest", self.held_out_dataset_digest
        )
        self.metrics = _as_dict("metrics", self.metrics)
        self.task_tolerance_results = _as_dict(
            "task_tolerance_results", self.task_tolerance_results
        )
        self.cross_task_results = _as_dict("cross_task_results", self.cross_task_results)
        self.physical_constraint_results = _as_dict(
            "physical_constraint_results", self.physical_constraint_results
        )
        self.counterexample_results = _as_dict(
            "counterexample_results", self.counterexample_results
        )
        self.model_adequacy_results = _as_dict(
            "model_adequacy_results", self.model_adequacy_results
        )
        self.disposition = _enum_value(ValidationDisposition, self.disposition, name="disposition")
        self.artifact_digest = _require_digest("artifact_digest", self.artifact_digest)
        if self.validation_source != SERVER_VALIDATION_SOURCE:
            raise CanonicalArtifactError(f"validation_source must be {SERVER_VALIDATION_SOURCE!r}")
        if not self.independently_reproduced:
            raise CanonicalArtifactError(
                "ServerValidationRun requires independently_reproduced=True"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_run_id": self.validation_run_id,
            "candidate_id": self.candidate_id,
            "held_out_dataset_digest": self.held_out_dataset_digest,
            "validation_source": self.validation_source,
            "independently_reproduced": bool(self.independently_reproduced),
            "metrics": dict(self.metrics),
            "task_tolerance_results": dict(self.task_tolerance_results),
            "cross_task_results": dict(self.cross_task_results),
            "physical_constraint_results": dict(self.physical_constraint_results),
            "counterexample_results": dict(self.counterexample_results),
            "model_adequacy_results": dict(self.model_adequacy_results),
            "disposition": self.disposition,
            "artifact_digest": self.artifact_digest,
        }


@dataclass
class CalibrationWorkflow:
    """Persistent self-calibration orchestration state (A7 schema freeze)."""

    workflow_id: str
    asset_id: str
    task_id: str
    organization_id: str
    state: str = CalibrationWorkflowState.DRIFT_DETECTED.value
    drift_event_id: Optional[str] = None
    credibility_assessment_id: Optional[str] = None
    dataset_id: Optional[str] = None
    estimator_run_id: Optional[str] = None
    candidate_id: Optional[str] = None
    validation_run_id: Optional[str] = None
    human_decision_id: Optional[str] = None
    evidence_specification_id: Optional[str] = None
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)
    closed_at: Optional[str] = None

    def __post_init__(self) -> None:
        self.workflow_id = _require_nonempty("workflow_id", self.workflow_id)
        self.asset_id = _require_nonempty("asset_id", self.asset_id)
        self.task_id = _require_nonempty("task_id", self.task_id)
        self.organization_id = _require_nonempty("organization_id", self.organization_id)
        self.state = _enum_value(CalibrationWorkflowState, self.state, name="state")
        self.created_at = _require_nonempty("created_at", self.created_at)
        self.updated_at = _require_nonempty("updated_at", self.updated_at)
        if self.state == CalibrationWorkflowState.CLOSED.value and not self.closed_at:
            raise CanonicalArtifactError("closed workflows require closed_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "organization_id": self.organization_id,
            "state": self.state,
            "drift_event_id": self.drift_event_id,
            "credibility_assessment_id": self.credibility_assessment_id,
            "dataset_id": self.dataset_id,
            "estimator_run_id": self.estimator_run_id,
            "candidate_id": self.candidate_id,
            "validation_run_id": self.validation_run_id,
            "human_decision_id": self.human_decision_id,
            "evidence_specification_id": self.evidence_specification_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
        }


@dataclass
class AuditEvidenceEntry:
    """Append-only evidence provenance record (packaged in A9)."""

    workflow_id: str
    event_type: str
    actor: str  # server-derived
    organization_id: str
    asset_id: str
    task_id: str
    source: str  # system | user:<id> | worker
    request_id: str
    artifact_digests: list[str]
    source_sha: str
    feature_flags: dict
    evidence_tier: str
    timestamp: str = field(default_factory=_utc_now_iso)
    estimator_run_id: Optional[str] = None
    validation_run_id: Optional[str] = None
    container_digest: Optional[str] = None

    def __post_init__(self) -> None:
        self.workflow_id = _require_nonempty("workflow_id", self.workflow_id)
        self.event_type = _enum_value(AuditEventType, self.event_type, name="event_type")
        self.actor = _require_nonempty("actor", self.actor)
        self.organization_id = _require_nonempty("organization_id", self.organization_id)
        self.asset_id = _require_nonempty("asset_id", self.asset_id)
        self.task_id = _require_nonempty("task_id", self.task_id)
        self.source = _require_nonempty("source", self.source)
        self.request_id = _require_nonempty("request_id", self.request_id)
        self.artifact_digests = _as_str_list("artifact_digests", self.artifact_digests)
        self.source_sha = _require_digest("source_sha", self.source_sha)
        self.feature_flags = _as_dict("feature_flags", self.feature_flags)
        self.evidence_tier = _normalize_evidence_tier(self.evidence_tier)
        self.timestamp = _require_nonempty("timestamp", self.timestamp)
        if self.container_digest is not None:
            self.container_digest = _require_digest("container_digest", self.container_digest)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "organization_id": self.organization_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "source": self.source,
            "request_id": self.request_id,
            "estimator_run_id": self.estimator_run_id,
            "validation_run_id": self.validation_run_id,
            "artifact_digests": list(self.artifact_digests),
            "source_sha": self.source_sha,
            "container_digest": self.container_digest,
            "feature_flags": dict(self.feature_flags),
            "timestamp": self.timestamp,
            "evidence_tier": self.evidence_tier,
        }


# ---------------------------------------------------------------------------
# B1 — CalibrationObservationSet (physical signals from canonical telemetry)
# ---------------------------------------------------------------------------


def _as_float_matrix(name: str, value: Any) -> list[list[float]]:
    """Normalize ndarray / nested sequences to list[list[float]]."""
    if value is None:
        raise CanonicalArtifactError(f"{name} is required")
    if hasattr(value, "tolist") and not isinstance(value, (list, tuple)):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        raise CanonicalArtifactError(f"{name} must be a 2d sequence")
    rows: list[list[float]] = []
    for i, row in enumerate(value):
        if hasattr(row, "tolist") and not isinstance(row, (list, tuple)):
            row = row.tolist()
        if not isinstance(row, (list, tuple)):
            raise CanonicalArtifactError(f"{name}[{i}] must be a sequence")
        try:
            rows.append([float(x) for x in row])
        except (TypeError, ValueError) as exc:
            raise CanonicalArtifactError(f"{name}[{i}] must contain floats") from exc
    return rows


def _as_float_vector(name: str, value: Any) -> list[float]:
    if value is None:
        raise CanonicalArtifactError(f"{name} is required")
    if hasattr(value, "tolist") and not isinstance(value, (list, tuple)):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        raise CanonicalArtifactError(f"{name} must be a 1d sequence")
    try:
        return [float(x) for x in value]
    except (TypeError, ValueError) as exc:
        raise CanonicalArtifactError(f"{name} must contain floats") from exc


def _as_bool_vector(name: str, value: Any) -> list[bool]:
    if value is None:
        raise CanonicalArtifactError(f"{name} is required")
    if hasattr(value, "tolist") and not isinstance(value, (list, tuple)):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        raise CanonicalArtifactError(f"{name} must be a 1d sequence")
    return [bool(x) for x in value]


def _as_dict_list(name: str, value: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    items = list(value or [])
    out: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise CanonicalArtifactError(f"{name}[{i}] must be a mapping")
        out.append(dict(item))
    return out


@dataclass
class CalibrationObservationSet:
    """Estimator-ready physical signals derived from canonical telemetry (B1).

    Arrays are stored as nested Python lists so the contracts package stays
    free of a numpy dependency. Callers may pass array-like objects; they are
    normalized in ``__post_init__``. Digests hash the JSON-canonical payload
    (lists), so identical numeric contents yield a deterministic digest.
    """

    observation_set_id: str
    dataset_manifest_id: str
    asset_id: str
    task_id: str
    robot_model: str

    # Physical signals (per sample, per joint) — shapes [N, n_joints] / [N]
    q: list[list[float]]
    q_dot: list[list[float]]
    q_ddot: list[list[float]]
    effort: list[list[float]]
    sample_times: list[float]

    quality_mask: list[bool]
    activity_segments: list[dict]
    process_context: dict

    signal_provenance: dict
    transformation_log: list[dict]
    observation_set_digest: str = ""

    n_samples: int = 0
    n_joints: int = 0
    units: dict[str, str] = field(
        default_factory=lambda: {
            "q": "rad",
            "q_dot": "rad/s",
            "q_ddot": "rad/s^2",
            "effort": "N·m",
            "sample_times": "s",
        }
    )
    evidence_tier: str = EvidenceTier.SYNTHETIC.value
    created_at: str = field(default_factory=_utc_now_iso)

    def __post_init__(self) -> None:
        self.observation_set_id = _require_nonempty("observation_set_id", self.observation_set_id)
        self.dataset_manifest_id = _require_nonempty(
            "dataset_manifest_id", self.dataset_manifest_id
        )
        self.asset_id = _require_nonempty("asset_id", self.asset_id)
        self.task_id = _require_nonempty("task_id", self.task_id)
        self.robot_model = _require_nonempty("robot_model", self.robot_model)

        self.q = _as_float_matrix("q", self.q)
        self.q_dot = _as_float_matrix("q_dot", self.q_dot)
        self.q_ddot = _as_float_matrix("q_ddot", self.q_ddot)
        self.effort = _as_float_matrix("effort", self.effort)
        self.sample_times = _as_float_vector("sample_times", self.sample_times)
        self.quality_mask = _as_bool_vector("quality_mask", self.quality_mask)

        if not self.q:
            raise CanonicalArtifactError("q must be non-empty")
        n = len(self.q)
        n_joints = len(self.q[0])
        if n_joints < 1:
            raise CanonicalArtifactError("q must have at least one joint column")
        for name, matrix in (
            ("q", self.q),
            ("q_dot", self.q_dot),
            ("q_ddot", self.q_ddot),
            ("effort", self.effort),
        ):
            if len(matrix) != n:
                raise CanonicalArtifactError(f"{name} length {len(matrix)} != n_samples {n}")
            for i, row in enumerate(matrix):
                if len(row) != n_joints:
                    raise CanonicalArtifactError(
                        f"{name}[{i}] length {len(row)} != n_joints {n_joints}"
                    )
        if len(self.sample_times) != n:
            raise CanonicalArtifactError(
                f"sample_times length {len(self.sample_times)} != n_samples {n}"
            )
        if len(self.quality_mask) != n:
            raise CanonicalArtifactError(
                f"quality_mask length {len(self.quality_mask)} != n_samples {n}"
            )

        self.n_samples = int(n)
        self.n_joints = int(n_joints)
        self.activity_segments = _as_dict_list("activity_segments", self.activity_segments)
        self.process_context = _as_dict("process_context", self.process_context)
        self.signal_provenance = _as_dict("signal_provenance", self.signal_provenance)
        self.transformation_log = _as_dict_list("transformation_log", self.transformation_log)
        if not self.transformation_log:
            raise CanonicalArtifactError(
                "transformation_log is required (every observation set must record transforms)"
            )
        self.units = {str(k): str(v) for k, v in dict(self.units or {}).items()}
        for required in ("q", "q_dot", "q_ddot", "effort", "sample_times"):
            if required not in self.units:
                raise CanonicalArtifactError(f"units must declare {required!r}")
        self.evidence_tier = _normalize_evidence_tier(self.evidence_tier)
        self.created_at = _require_nonempty("created_at", self.created_at)

        expected = self.compute_digest()
        if not self.observation_set_digest:
            self.observation_set_digest = expected
        else:
            self.observation_set_digest = _require_digest(
                "observation_set_digest", self.observation_set_digest
            )
            if self.observation_set_digest != expected:
                raise CanonicalArtifactError(
                    "observation_set_digest does not match canonical contents "
                    "(immutable digest mismatch)"
                )

    def _digest_payload(self) -> dict[str, Any]:
        return {
            "observation_set_id": self.observation_set_id,
            "dataset_manifest_id": self.dataset_manifest_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "robot_model": self.robot_model,
            "q": self.q,
            "q_dot": self.q_dot,
            "q_ddot": self.q_ddot,
            "effort": self.effort,
            "sample_times": self.sample_times,
            "quality_mask": self.quality_mask,
            "activity_segments": self.activity_segments,
            "process_context": self.process_context,
            "signal_provenance": self.signal_provenance,
            "transformation_log": self.transformation_log,
            "n_samples": self.n_samples,
            "n_joints": self.n_joints,
            "units": self.units,
            "evidence_tier": self.evidence_tier,
        }

    def compute_digest(self) -> str:
        return sha256_hex(self._digest_payload())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._digest_payload(),
            "observation_set_digest": self.observation_set_digest,
            "created_at": self.created_at,
        }


def evidence_field_inventory() -> dict[str, list[str]]:
    """Acceptance helper: evidence provenance fields per artifact schema."""
    return {
        "CalibrationDatasetManifest": [
            "manifest_digest",
            "evidence_tier",
            "telemetry_source_ids",
        ],
        "EstimatorRun": [
            "configuration_digest",
            "prior_digest",
            "artifact_digest",
            "estimator_version",
        ],
        "NumericalCalibrationCandidate": [
            "candidate_digest",
            "parameter_source",
            "server_estimated",
            "evidence_tier",
        ],
        "ServerValidationRun": [
            "held_out_dataset_digest",
            "validation_source",
            "independently_reproduced",
            "artifact_digest",
        ],
        "CalibrationWorkflow": [
            "dataset_id",
            "estimator_run_id",
            "candidate_id",
            "validation_run_id",
            "evidence_specification_id",
        ],
        "AuditEvidenceEntry": [
            "source_sha",
            "container_digest",
            "feature_flags",
            "actor",
            "artifact_digests",
            "evidence_tier",
        ],
        "CalibrationObservationSet": [
            "observation_set_digest",
            "evidence_tier",
            "signal_provenance",
            "transformation_log",
            "quality_mask",
            "dataset_manifest_id",
        ],
    }


def schema_field_names(cls: type) -> list[str]:
    return [f.name for f in fields(cls)]


__all__ = [
    "AUDIT_EVENT_TYPES",
    "AuditEventType",
    "AuditEvidenceEntry",
    "CANDIDATE_STATUSES",
    "CalibrationDatasetManifest",
    "CalibrationObservationSet",
    "CalibrationWorkflow",
    "CalibrationWorkflowState",
    "CandidateStatus",
    "CanonicalArtifactError",
    "ESTIMATOR_RUN_STATUSES",
    "EVIDENCE_TIER_VALUES",
    "EstimatedParameter",
    "EstimatorRun",
    "EstimatorRunStatus",
    "IDENTIFIABILITY_VALUES",
    "Identifiability",
    "MODEL_ADEQUACY_STATUSES",
    "ModelAdequacyStatus",
    "NumericalCalibrationCandidate",
    "SERVER_VALIDATION_SOURCE",
    "SPLIT_STRATEGIES",
    "ServerValidationRun",
    "SplitStrategy",
    "VALIDATION_DISPOSITIONS",
    "ValidationDisposition",
    "WORKFLOW_STATES",
    "canonical_json_bytes",
    "evidence_field_inventory",
    "schema_field_names",
    "sha256_hex",
]
