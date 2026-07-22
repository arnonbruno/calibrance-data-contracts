"""Neutral calibration outcome interchange schema (PR-C1).

Describes facts and provenance only. Must not contain scoring logic,
proprietary cohort definitions, promotion thresholds, hidden simulator truth,
expected decisions, future golden outcomes, or evaluator-only fields.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .enums import ContributionMode, EvidenceTier

# Keys that must never appear in the type-specific payload (hidden truth / evaluator-only).
FORBIDDEN_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        "scenario_class",
        "hidden_parameters",
        "expected_outcome",
        "true_candidate_error",
        "future_golden_result",
    }
)


class CalibrationOutcomeEnvelope(BaseModel):
    """Neutral interchange envelope for exported calibration lifecycle facts."""

    event_id: str
    event_type: str
    schema_version: str = "1.0"
    organization_id: str
    site_id: str
    asset_id: str
    session_id: str | None = None
    candidate_id: str | None = None
    profile_id: str | None = None
    configuration_digest: str
    activity_fingerprint_id: str | None = None
    evidence_tier: EvidenceTier
    contribution_mode: ContributionMode = ContributionMode.PRIVATE
    source_record_type: str
    source_record_id: str
    source_record_version: int = 1
    source_event_ids: list[str] = Field(default_factory=list)
    provenance_digest: str
    payload: dict = Field(default_factory=dict)
    created_at: datetime

    @field_validator("payload")
    @classmethod
    def reject_hidden_truth_keys(cls, value: dict) -> dict:
        """Reject evaluator-only / hidden-truth keys in the type-specific payload."""
        forbidden = FORBIDDEN_PAYLOAD_KEYS.intersection(value.keys())
        if forbidden:
            raise ValueError(
                "payload must not contain hidden-truth keys: "
                + ", ".join(sorted(forbidden))
            )
        return value
