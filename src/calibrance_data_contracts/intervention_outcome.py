"""Intervention and outcome lifecycle schemas (P4).

Records the full chain without conflating nodes:

    recommendation → human decision → physical intervention → observed outcome

Causal attribution is never implied by the presence of an outcome; outcomes
carry provenance and optional evidence links only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InterventionState(str, Enum):
    """Lifecycle / decision states for the intervention chain."""

    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    MODIFIED = "modified"
    REJECTED = "rejected"
    EXECUTED = "executed"
    OBSERVATION_WINDOW = "observation_window"
    OUTCOME_ASSESSED = "outcome_assessed"
    CLOSED = "closed"


# Human decisions may only use these states — never EXECUTED / CLOSED / etc.
HUMAN_DECISION_STATES: frozenset[InterventionState] = frozenset(
    {
        InterventionState.ACCEPTED,
        InterventionState.MODIFIED,
        InterventionState.REJECTED,
    }
)


class OutcomeType(str, Enum):
    """Observed post-intervention result types (facts, not causal claims)."""

    RESIDUAL_IMPROVED = "residual_improved"
    RESIDUAL_WORSENED = "residual_worsened"
    QUALITY_IMPROVED = "quality_improved"
    QUALITY_WORSENED = "quality_worsened"
    CYCLE_TIME_IMPROVED = "cycle_time_improved"
    NO_MEASURABLE_EFFECT = "no_measurable_effect"
    FALSE_ALERT = "false_alert"
    MAINTENANCE_REQUIRED = "maintenance_required"
    PROBLEM_RECURRED = "problem_recurred"
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"


class CausalAttribution(str, Enum):
    """Whether the intervention is claimed to have caused the outcome."""

    NOT_CLAIMED = "not_claimed"
    SUPPORTED = "supported"
    UNCERTAIN = "uncertain"
    CONTRADICTED = "contradicted"


@dataclass
class NodeProvenance:
    """Common provenance fields required on every chain node (P4.5)."""

    tenant_id: str
    asset_id: str
    task_id: str
    timestamp: datetime = field(default_factory=_utc_now)
    evidence_tier: str = "synthetic"
    actor: str = "system"  # system | human | technician
    source: str = "api"  # api | batch | mqtt
    confidence: float = 0.0
    audit_event_id: Optional[str] = None


@dataclass
class CalibrationRecommendation:
    """What Calibrance suggested — never what was executed."""

    recommendation_id: str
    tenant_id: str
    asset_id: str
    task_id: str
    candidate_id: str
    recommended_parameters: dict
    expected_improvement: dict
    confidence: float
    evidence_tier: str
    created_at: datetime = field(default_factory=_utc_now)
    created_by: str = "calibrance"
    actor: str = "system"
    source: str = "api"
    audit_event_id: Optional[str] = None
    # Explicit: recommendations are never recorded as executed.
    state: InterventionState = InterventionState.PROPOSED
    is_executed: bool = False

    def __post_init__(self) -> None:
        if self.is_executed:
            raise ValueError("recommendation must never be recorded as executed")
        if self.state == InterventionState.EXECUTED:
            raise ValueError("recommendation state must never be EXECUTED")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class HumanDecision:
    """What a human decided — distinct from recommendation and physical action."""

    decision_id: str
    recommendation_id: str
    tenant_id: str
    asset_id: str
    task_id: str
    state: InterventionState  # accepted | modified | rejected only
    modified_parameters: Optional[dict] = None
    reason: Optional[str] = None
    decided_by: str = ""
    decided_at: datetime = field(default_factory=_utc_now)
    evidence_tier: str = "synthetic"
    actor: str = "human"
    source: str = "api"
    confidence: float = 1.0
    audit_event_id: Optional[str] = None
    # Synthetic decisions must never be labeled as real plant decisions.
    is_synthetic: bool = True
    labeled_as_real: bool = False

    def __post_init__(self) -> None:
        if self.state not in HUMAN_DECISION_STATES:
            raise ValueError(
                f"human decision state must be one of "
                f"{sorted(s.value for s in HUMAN_DECISION_STATES)}, got {self.state!r}"
            )
        if self.state == InterventionState.MODIFIED and not self.modified_parameters:
            raise ValueError("modified decision requires modified_parameters")
        if self.is_synthetic and self.labeled_as_real:
            raise ValueError("synthetic human decisions must not be labeled as real")
        if self.evidence_tier == "synthetic" and self.labeled_as_real:
            raise ValueError("synthetic evidence_tier decisions must not be labeled as real")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class PhysicalIntervention:
    """What was actually applied on the asset — never the recommendation itself."""

    intervention_id: str
    decision_id: str
    tenant_id: str
    asset_id: str
    task_id: str
    actual_parameters_applied: dict
    applied_by: str
    applied_at: datetime = field(default_factory=_utc_now)
    notes: Optional[str] = None
    evidence_tier: str = "synthetic"
    actor: str = "technician"
    source: str = "api"
    confidence: float = 1.0
    audit_event_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not (self.intervention_id or "").strip():
            raise ValueError("intervention_id is required")
        if not (self.decision_id or "").strip():
            raise ValueError("decision_id is required")
        if not self.actual_parameters_applied:
            raise ValueError("actual_parameters_applied is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class ObservedOutcome:
    """What was observed after an intervention — facts with provenance, not causal claims."""

    outcome_id: str
    intervention_id: str
    tenant_id: str
    asset_id: str
    task_id: str
    outcome_type: OutcomeType
    measured_improvement: Optional[dict] = None
    observation_window_hours: float = 0.0
    observation_start: Optional[datetime] = None
    observation_end: Optional[datetime] = None
    quality_observations: list[str] = field(default_factory=list)
    process_events: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    assessed_at: datetime = field(default_factory=_utc_now)
    assessed_by: str = "calibrance"
    evidence_tier: str = "synthetic"
    actor: str = "system"
    source: str = "api"
    confidence: float = 0.0
    audit_event_id: Optional[str] = None
    causal_attribution: CausalAttribution = CausalAttribution.NOT_CLAIMED
    causal_evidence_ids: list[str] = field(default_factory=list)
    observation_window_closed: bool = True
    # Must match intervention.asset_id — cross-asset links are forbidden.
    intervention_asset_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.audit_event_id and self.evidence_tier != "synthetic":
            raise ValueError("non-synthetic outcomes require audit_event_id for provenance")
        if self.intervention_asset_id and self.intervention_asset_id != self.asset_id:
            raise ValueError("cross-asset outcome link is forbidden")
        if self.causal_attribution == CausalAttribution.SUPPORTED and not self.causal_evidence_ids:
            raise ValueError("causal claim without evidence is forbidden")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if float(self.observation_window_hours) < 0:
            raise ValueError("observation_window_hours must be non-negative")
        if not self.observation_window_closed and self.outcome_type not in {
            OutcomeType.EVIDENCE_INSUFFICIENT,
        }:
            # Open windows may only record insufficient evidence placeholders.
            if self.observation_end is not None:
                raise ValueError(
                    "open observation window must not set observation_end "
                    "unless outcome is evidence_insufficient"
                )


@dataclass
class InterventionOutcomeChain:
    """Full chain from recommendation to outcome. Never conflate nodes."""

    recommendation: CalibrationRecommendation
    human_decision: HumanDecision
    physical_intervention: Optional[PhysicalIntervention] = None
    observed_outcome: Optional[ObservedOutcome] = None

    def __post_init__(self) -> None:
        rec = self.recommendation
        dec = self.human_decision
        if dec.recommendation_id != rec.recommendation_id:
            raise ValueError("decision.recommendation_id must match recommendation")
        if dec.tenant_id != rec.tenant_id:
            raise ValueError("decision tenant must match recommendation tenant")
        if dec.asset_id != rec.asset_id:
            raise ValueError("decision asset must match recommendation asset")

        if dec.state == InterventionState.REJECTED:
            if self.physical_intervention is not None:
                raise ValueError("rejected recommendation must not have physical intervention")
            if self.observed_outcome is not None:
                raise ValueError("rejected recommendation must not have observed outcome")
            return

        if self.physical_intervention is not None:
            pi = self.physical_intervention
            if pi.decision_id != dec.decision_id:
                raise ValueError("intervention.decision_id must match decision")
            if pi.asset_id != rec.asset_id:
                raise ValueError("intervention asset must match recommendation asset")
            if pi.tenant_id != rec.tenant_id:
                raise ValueError("intervention tenant must match recommendation tenant")

        if self.observed_outcome is not None:
            if self.physical_intervention is None:
                raise ValueError("outcome requires a physical intervention")
            oo = self.observed_outcome
            if oo.intervention_id != self.physical_intervention.intervention_id:
                raise ValueError("outcome.intervention_id must match intervention")
            if oo.asset_id != rec.asset_id:
                raise ValueError("cross-asset outcome link is forbidden")
            if oo.tenant_id != rec.tenant_id:
                raise ValueError("outcome tenant must match recommendation tenant")


__all__ = [
    "InterventionState",
    "HUMAN_DECISION_STATES",
    "OutcomeType",
    "CausalAttribution",
    "NodeProvenance",
    "CalibrationRecommendation",
    "HumanDecision",
    "PhysicalIntervention",
    "ObservedOutcome",
    "InterventionOutcomeChain",
]
