"""Counterfactual candidate validation schema (P7).

Every calibration candidate must be validated against held-out evidence before
reaching a human. Training-only improvement is never enough for promotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class CandidateDisposition(str, Enum):
    """Disposition after counterfactual validation (pre-human gate)."""

    ELIGIBLE_FOR_HUMAN_REVIEW = "eligible_for_human_review"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED = "unsupported"


DISPOSITION_VALUES: frozenset[str] = frozenset(d.value for d in CandidateDisposition)

# Canonical rejection reason codes (P7.3).
REJECTION_OVERFITTING = "overfitting_held_out_degradation"
REJECTION_CROSS_TASK = "cross_task_conflict"
REJECTION_PHYSICAL = "physically_invalid_parameters"
REJECTION_COUNTEREXAMPLE = "critical_counterexample_match"
REJECTION_UNCERTAINTY = "result_disappears_under_observation_uncertainty"
REJECTION_MODEL_INADEQUACY = "excessive_model_discrepancy"
REJECTION_UNDER_CALIBRATED = "confidence_under_calibrated"

KNOWN_REJECTION_REASONS: frozenset[str] = frozenset(
    {
        REJECTION_OVERFITTING,
        REJECTION_CROSS_TASK,
        REJECTION_PHYSICAL,
        REJECTION_COUNTEREXAMPLE,
        REJECTION_UNCERTAINTY,
        REJECTION_MODEL_INADEQUACY,
        REJECTION_UNDER_CALIBRATED,
    }
)


class CandidateValidationError(ValueError):
    """Raised when a CandidateValidation record violates hard invariants."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CandidateValidation:
    """Result of 10-dimension counterfactual validation for one candidate."""

    validation_id: str
    candidate_id: str
    tenant_id: str
    asset_id: str
    task_id: str

    disposition: CandidateDisposition

    # Validation dimensions
    identification_fit: dict  # fit quality on training data
    held_out_performance: dict  # generalization
    task_tolerance_compliance: dict  # per-task tolerance check
    cross_task_impact: dict  # impact on other tasks
    robustness_score: float  # observation profile robustness
    physical_validity: dict  # parameter validity
    uncertainty_quality: dict  # calibration check

    simulator_agreement: Optional[dict] = None  # cross-sim check
    counterexample_similarity: Optional[dict] = None  # CEX distance
    model_inadequacy: Optional[dict] = None  # discrepancy check

    # Rejection reasons (if rejected)
    rejection_reasons: list[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=_utc_now)
    evidence_tier: str = "synthetic"
    labels: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    # Integration hooks (P2/P3/P4/P6)
    credibility_status: Optional[str] = None
    quality_observation_ids: list[str] = field(default_factory=list)
    outcome_chain_id: Optional[str] = None
    evidence_recommendation_triggered: bool = False

    def __post_init__(self) -> None:
        if not self.validation_id:
            raise CandidateValidationError("validation_id is required")
        if not self.candidate_id:
            raise CandidateValidationError("candidate_id is required")
        if not self.tenant_id:
            raise CandidateValidationError("tenant_id is required")
        if not self.asset_id:
            raise CandidateValidationError("asset_id is required")
        if not self.task_id:
            raise CandidateValidationError("task_id is required")

        if isinstance(self.disposition, str):
            try:
                self.disposition = CandidateDisposition(self.disposition)
            except ValueError as exc:
                raise CandidateValidationError(
                    f"unknown disposition: {self.disposition!r}"
                ) from exc

        if not isinstance(self.disposition, CandidateDisposition):
            raise CandidateValidationError("disposition must be CandidateDisposition")

        if self.disposition == CandidateDisposition.REJECT and not self.rejection_reasons:
            raise CandidateValidationError(
                "REJECT disposition requires at least one rejection_reason"
            )
        if (
            self.disposition == CandidateDisposition.ELIGIBLE_FOR_HUMAN_REVIEW
            and self.rejection_reasons
        ):
            raise CandidateValidationError(
                "ELIGIBLE_FOR_HUMAN_REVIEW must not carry rejection_reasons"
            )

        if not (0.0 <= float(self.robustness_score) <= 1.0):
            raise CandidateValidationError("robustness_score must be in [0, 1]")

        self.identification_fit = dict(self.identification_fit or {})
        self.held_out_performance = dict(self.held_out_performance or {})
        self.task_tolerance_compliance = dict(self.task_tolerance_compliance or {})
        self.cross_task_impact = dict(self.cross_task_impact or {})
        self.physical_validity = dict(self.physical_validity or {})
        self.uncertainty_quality = dict(self.uncertainty_quality or {})
        if self.simulator_agreement is not None:
            self.simulator_agreement = dict(self.simulator_agreement)
        if self.counterexample_similarity is not None:
            self.counterexample_similarity = dict(self.counterexample_similarity)
        if self.model_inadequacy is not None:
            self.model_inadequacy = dict(self.model_inadequacy)

        self.rejection_reasons = list(self.rejection_reasons or [])
        self.labels = dict(self.labels or {})
        warnings = list(self.warnings or [])
        for reason in self.rejection_reasons:
            if not (reason or "").strip():
                raise CandidateValidationError("rejection_reasons must not contain empty strings")
            if reason not in KNOWN_REJECTION_REASONS:
                warnings.append(f"unknown rejection_reason: {reason}")
        self.warnings = warnings
        self.quality_observation_ids = list(self.quality_observation_ids or [])

        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

    @property
    def is_promotable_to_human(self) -> bool:
        return self.disposition == CandidateDisposition.ELIGIBLE_FOR_HUMAN_REVIEW

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "candidate_id": self.candidate_id,
            "tenant_id": self.tenant_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "disposition": self.disposition.value,
            "identification_fit": dict(self.identification_fit),
            "held_out_performance": dict(self.held_out_performance),
            "task_tolerance_compliance": dict(self.task_tolerance_compliance),
            "cross_task_impact": dict(self.cross_task_impact),
            "robustness_score": float(self.robustness_score),
            "simulator_agreement": (
                dict(self.simulator_agreement) if self.simulator_agreement else None
            ),
            "counterexample_similarity": (
                dict(self.counterexample_similarity) if self.counterexample_similarity else None
            ),
            "physical_validity": dict(self.physical_validity),
            "uncertainty_quality": dict(self.uncertainty_quality),
            "model_inadequacy": (dict(self.model_inadequacy) if self.model_inadequacy else None),
            "rejection_reasons": list(self.rejection_reasons),
            "created_at": self.created_at.isoformat(),
            "evidence_tier": self.evidence_tier,
            "labels": dict(self.labels),
            "warnings": list(self.warnings),
            "credibility_status": self.credibility_status,
            "quality_observation_ids": list(self.quality_observation_ids),
            "outcome_chain_id": self.outcome_chain_id,
            "evidence_recommendation_triggered": bool(self.evidence_recommendation_triggered),
        }


__all__ = [
    "CandidateDisposition",
    "CandidateValidation",
    "CandidateValidationError",
    "DISPOSITION_VALUES",
    "KNOWN_REJECTION_REASONS",
    "REJECTION_COUNTEREXAMPLE",
    "REJECTION_CROSS_TASK",
    "REJECTION_MODEL_INADEQUACY",
    "REJECTION_OVERFITTING",
    "REJECTION_PHYSICAL",
    "REJECTION_UNCERTAINTY",
    "REJECTION_UNDER_CALIBRATED",
]
