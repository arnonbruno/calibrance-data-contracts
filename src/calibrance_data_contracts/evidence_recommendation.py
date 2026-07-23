"""Active evidence recommendation schema (P6).

Calibrance recommends which evidence activity would best distinguish competing
explanations. Authority is recommend_only — never commands a robot, never
changes an active profile decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

ACTIVE_IDENTIFICATION_AUTHORITY = "recommend_only"
AUTHORITY_VALUES: frozenset[str] = frozenset({ACTIVE_IDENTIFICATION_AUTHORITY})

REQUIRED_CONSTRAINT_KEYS: frozenset[str] = frozenset(
    {
        "workspace",
        "speed",
        "acceleration",
        "tool",
        "payload",
        "duration",
        "available_signals",
        "site_policy",
        "safety_declaration",
        "human_approval",
    }
)


class EvidenceRecommendationValidationError(ValueError):
    """Raised when an evidence recommendation violates hard invariants."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class EvidenceRecommendation:
    """Advisory recommendation for next evidence activity (never a robot command)."""

    recommendation_id: str
    tenant_id: str
    asset_id: str
    task_id: str

    recommended_activity: str  # activity name/ID
    expected_information_gain: float
    expected_duration_minutes: float
    target_parameter_groups: list[str]  # which parameters this would help identify
    competing_hypotheses: list[str]  # what explanations this distinguishes
    required_signals: list[str]
    constraints: dict  # workspace, speed, acceleration, tool, payload, duration, …
    estimated_interruption_cost_usd: float
    alternatives: list[dict]  # next-best options

    # Ranking / explanation metadata
    ranking_strategy: str = "cost_aware_calibrance"
    score: float = 0.0
    explanation: str = ""
    operator_burden_penalty: float = 0.0
    uncertainty_penalty: float = 0.0
    transfer_risk_penalty: float = 0.0
    blocked_reason: Optional[str] = None

    # Hard constraints — frozen authority
    commands_robot: bool = False  # ALWAYS false
    human_approval_required: bool = True
    active_identification_authority: str = ACTIVE_IDENTIFICATION_AUTHORITY
    affects_active_profile: bool = False  # ALWAYS false

    created_at: datetime = field(default_factory=_utc_now)
    evidence_tier: str = "synthetic"
    labels: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            raise EvidenceRecommendationValidationError("recommendation_id is required")
        if not self.tenant_id:
            raise EvidenceRecommendationValidationError("tenant_id is required")
        if not self.asset_id:
            raise EvidenceRecommendationValidationError("asset_id is required")
        if not self.task_id:
            raise EvidenceRecommendationValidationError("task_id is required")

        # Hard authority invariants.
        if self.commands_robot:
            raise EvidenceRecommendationValidationError(
                "commands_robot must be false (recommend_only authority)"
            )
        if not self.human_approval_required:
            raise EvidenceRecommendationValidationError(
                "human_approval_required must be true"
            )
        if self.active_identification_authority not in AUTHORITY_VALUES:
            raise EvidenceRecommendationValidationError(
                f"active_identification_authority must be "
                f"{ACTIVE_IDENTIFICATION_AUTHORITY!r}, "
                f"got {self.active_identification_authority!r}"
            )
        if self.affects_active_profile:
            raise EvidenceRecommendationValidationError(
                "evidence recommendations must not change active profile decisions"
            )

        # Recommendation without explanation is forbidden (unless blocked).
        if self.blocked_reason is None:
            if not (self.recommended_activity or "").strip():
                raise EvidenceRecommendationValidationError(
                    "recommended_activity is required when not blocked"
                )
            if not (self.explanation or "").strip():
                raise EvidenceRecommendationValidationError(
                    "recommendation without explanation is forbidden"
                )
            if not self.competing_hypotheses and not self.target_parameter_groups:
                raise EvidenceRecommendationValidationError(
                    "recommendation must target parameter groups or competing hypotheses"
                )

        if float(self.expected_information_gain) < 0:
            raise EvidenceRecommendationValidationError(
                "expected_information_gain must be non-negative"
            )
        if float(self.expected_duration_minutes) < 0:
            raise EvidenceRecommendationValidationError(
                "expected_duration_minutes must be non-negative"
            )
        if float(self.estimated_interruption_cost_usd) < 0:
            raise EvidenceRecommendationValidationError(
                "estimated_interruption_cost_usd must be non-negative"
            )

        # Constraints must declare the required safety / site keys.
        constraints = dict(self.constraints or {})
        missing = sorted(REQUIRED_CONSTRAINT_KEYS - set(constraints.keys()))
        if missing and self.blocked_reason is None:
            raise EvidenceRecommendationValidationError(
                f"constraints missing required keys: {missing}"
            )
        safety = constraints.get("safety_declaration")
        if isinstance(safety, dict) and safety.get("commands_robot") is True:
            raise EvidenceRecommendationValidationError(
                "unsafe recommendation: safety_declaration.commands_robot must be false"
            )
        self.constraints = constraints

        self.target_parameter_groups = list(self.target_parameter_groups or [])
        self.competing_hypotheses = list(self.competing_hypotheses or [])
        self.required_signals = list(self.required_signals or [])
        self.alternatives = [dict(a) for a in (self.alternatives or [])]
        self.labels = dict(self.labels or {})
        self.warnings = list(self.warnings or [])

        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)

        # Force hard flags after validation (immutability of authority).
        self.commands_robot = False
        self.human_approval_required = True
        self.active_identification_authority = ACTIVE_IDENTIFICATION_AUTHORITY
        self.affects_active_profile = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "tenant_id": self.tenant_id,
            "asset_id": self.asset_id,
            "task_id": self.task_id,
            "recommended_activity": self.recommended_activity,
            "expected_information_gain": float(self.expected_information_gain),
            "expected_duration_minutes": float(self.expected_duration_minutes),
            "target_parameter_groups": list(self.target_parameter_groups),
            "competing_hypotheses": list(self.competing_hypotheses),
            "required_signals": list(self.required_signals),
            "constraints": dict(self.constraints),
            "estimated_interruption_cost_usd": float(self.estimated_interruption_cost_usd),
            "alternatives": list(self.alternatives),
            "ranking_strategy": self.ranking_strategy,
            "score": float(self.score),
            "explanation": self.explanation,
            "operator_burden_penalty": float(self.operator_burden_penalty),
            "uncertainty_penalty": float(self.uncertainty_penalty),
            "transfer_risk_penalty": float(self.transfer_risk_penalty),
            "blocked_reason": self.blocked_reason,
            "commands_robot": False,
            "human_approval_required": True,
            "active_identification_authority": ACTIVE_IDENTIFICATION_AUTHORITY,
            "affects_active_profile": False,
            "created_at": self.created_at.isoformat(),
            "evidence_tier": self.evidence_tier,
            "labels": dict(self.labels),
            "warnings": list(self.warnings),
        }


def default_constraints(
    *,
    workspace: str = "declared",
    speed_limit_rad_s: float = 1.0,
    acceleration_limit_rad_s2: float = 2.0,
    tool: str = "default",
    payload_kg_min: float = 0.0,
    payload_kg_max: float = 3.0,
    duration_budget_minutes: float = 30.0,
    available_signals: list[str] | None = None,
    site_policy: str = "allow_recommend_only",
) -> dict[str, Any]:
    """Canonical constraint envelope for recommend_only activities."""
    return {
        "workspace": workspace,
        "speed": {"max_rad_s": speed_limit_rad_s},
        "acceleration": {"max_rad_s2": acceleration_limit_rad_s2},
        "tool": tool,
        "payload": {"min_kg": payload_kg_min, "max_kg": payload_kg_max},
        "duration": {"budget_minutes": duration_budget_minutes},
        "available_signals": list(
            available_signals
            or ["joint_position", "joint_velocity", "joint_torque", "timestamp"]
        ),
        "site_policy": site_policy,
        "safety_declaration": {
            "commands_robot": False,
            "requires_qualified_operator": True,
            "requires_local_safety_review": True,
            "automatic_execution_authorized": False,
        },
        "human_approval": True,
    }


__all__ = [
    "ACTIVE_IDENTIFICATION_AUTHORITY",
    "AUTHORITY_VALUES",
    "REQUIRED_CONSTRAINT_KEYS",
    "EvidenceRecommendation",
    "EvidenceRecommendationValidationError",
    "default_constraints",
]
