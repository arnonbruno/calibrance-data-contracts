"""Economic assumptions and estimate schemas (P5).

Four value categories must never be conflated:

1. estimated_exposure — what drift/issue COULD cost if unaddressed
2. expected_action — what the recommended intervention is EXPECTED to cost/yield
3. observed_outcome — what ACTUALLY happened (requires real post-intervention data)
4. validated_value — confirmed savings with causal attribution (requires multiple points)

Synthetic / demo estimates may only populate (1) and (2). They must never present
savings as realized (observed or validated).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Common ISO 4217 codes accepted without external dependency.
KNOWN_CURRENCIES: frozenset[str] = frozenset(
    {
        "USD",
        "EUR",
        "BRL",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CHF",
        "CNY",
        "MXN",
        "INR",
        "KRW",
        "SEK",
        "NOK",
        "DKK",
        "NZD",
        "SGD",
        "HKD",
        "ZAR",
        "PLN",
    }
)

CONFIDENCE_LEVELS: frozenset[str] = frozenset({"low", "medium", "high"})

VALUE_STATUSES: frozenset[str] = frozenset(
    {
        "estimated_not_observed",
        "observed_not_validated",
        "validated",
    }
)

# Soft warning threshold — values above this are accepted but flagged.
EXTREME_COST_THRESHOLD = 1_000_000.0

COST_FIELDS: tuple[str, ...] = (
    "downtime_cost_per_hour",
    "engineering_cost_per_hour",
    "scrap_cost_per_unit",
    "rework_cost_per_unit",
    "maintenance_action_cost",
    "production_interruption_cost_per_minute",
    "units_per_hour",
)


class AssumptionSource(str, Enum):
    CUSTOMER_PROVIDED = "customer_provided"
    ESTIMATED = "estimated"
    OBSERVED = "observed"
    INDUSTRY_DEFAULT = "industry_default"


class EconomicValidationError(ValueError):
    """Raised when economic assumptions or estimates violate hard invariants."""


@dataclass
class EconomicAssumptions:
    """Tenant cost/rate assumptions used to compute advisory economic estimates."""

    tenant_id: str
    currency: str  # ISO 4217: USD, EUR, BRL, etc.
    downtime_cost_per_hour: float
    engineering_cost_per_hour: float
    scrap_cost_per_unit: float
    rework_cost_per_unit: float
    maintenance_action_cost: float
    production_interruption_cost_per_minute: float
    units_per_hour: float
    quality_escape_cost: Optional[float] = None
    source: AssumptionSource = AssumptionSource.ESTIMATED
    provided_by: Optional[str] = None
    provided_at: Optional[datetime] = None
    confidence: str = "low"  # low, medium, high
    notes: Optional[str] = None
    assumptions_id: str = ""
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tenant_id:
            raise EconomicValidationError("tenant_id is required")
        currency = (self.currency or "").strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise EconomicValidationError(
                f"currency ambiguity: expected ISO 4217 code, got {self.currency!r}"
            )
        if currency not in KNOWN_CURRENCIES:
            raise EconomicValidationError(
                f"currency ambiguity: unsupported or unknown code {currency!r}"
            )
        self.currency = currency

        if self.confidence not in CONFIDENCE_LEVELS:
            raise EconomicValidationError(
                f"confidence must be one of {sorted(CONFIDENCE_LEVELS)}, got {self.confidence!r}"
            )
        if isinstance(self.source, str):
            self.source = AssumptionSource(self.source)

        warnings: list[str] = list(self.warnings)
        for name in COST_FIELDS:
            value = float(getattr(self, name))
            if value < 0:
                raise EconomicValidationError(f"invalid cost: {name} must be non-negative")
            if value > EXTREME_COST_THRESHOLD:
                warnings.append(f"extremely high value for {name}: {value}")
        if self.quality_escape_cost is not None:
            q = float(self.quality_escape_cost)
            if q < 0:
                raise EconomicValidationError(
                    "invalid cost: quality_escape_cost must be non-negative"
                )
            if q > EXTREME_COST_THRESHOLD:
                warnings.append(f"extremely high value for quality_escape_cost: {q}")
            self.quality_escape_cost = q
        self.warnings = warnings


@dataclass
class EconomicEstimate:
    """Advisory economic estimate with strict four-category separation."""

    estimate_id: str
    tenant_id: str
    asset_id: str
    task_id: str
    recommendation_id: Optional[str] = None

    # Category 1: Estimated Exposure
    estimated_exposure: dict = field(default_factory=dict)

    # Category 2: Expected Action Value
    expected_action: dict = field(default_factory=dict)

    # Category 3: Observed Outcome (empty until real data)
    observed_outcome: Optional[dict] = None

    # Category 4: Validated Value (empty until validated)
    validated_value: Optional[dict] = None

    value_status: str = "estimated_not_observed"
    # Options: estimated_not_observed, observed_not_validated, validated

    assumptions_id: str = ""  # link to EconomicAssumptions
    created_at: datetime = field(default_factory=_utc_now)
    evidence_tier: str = "synthetic"
    currency: str = "USD"
    labels: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    # Hard guard: economic estimates never drive activation decisions.
    affects_activation: bool = False

    def __post_init__(self) -> None:
        if not self.estimate_id:
            raise EconomicValidationError("estimate_id is required")
        if not self.tenant_id:
            raise EconomicValidationError("tenant_id is required")
        if not self.assumptions_id:
            raise EconomicValidationError("economic output without assumptions is forbidden")
        if self.value_status not in VALUE_STATUSES:
            raise EconomicValidationError(f"invalid value_status: {self.value_status!r}")
        if self.affects_activation:
            raise EconomicValidationError(
                "economic score must not affect activation (affects_activation must be false)"
            )

        currency = (self.currency or "").strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise EconomicValidationError(
                f"currency ambiguity: expected ISO 4217 code, got {self.currency!r}"
            )
        self.currency = currency

        # Synthetic / demo must never claim realized savings.
        if self.evidence_tier == "synthetic":
            if self.observed_outcome is not None:
                raise EconomicValidationError(
                    "synthetic savings must not be presented as observed/realized"
                )
            if self.validated_value is not None:
                raise EconomicValidationError(
                    "synthetic savings must not be presented as validated/realized"
                )
            if self.value_status != "estimated_not_observed":
                raise EconomicValidationError(
                    "synthetic estimates must have value_status=estimated_not_observed"
                )
            labels = dict(self.labels)
            labels.setdefault("SYNTHETIC", True)
            labels.setdefault("NOT_REALIZED_SAVINGS", True)
            self.labels = labels

        if self.value_status == "estimated_not_observed":
            if self.observed_outcome is not None or self.validated_value is not None:
                raise EconomicValidationError(
                    "estimated_not_observed forbids observed_outcome and validated_value"
                )
        if self.value_status == "observed_not_validated" and self.validated_value is not None:
            raise EconomicValidationError(
                "observed_not_validated forbids validated_value"
            )
        if self.value_status == "validated" and self.validated_value is None:
            raise EconomicValidationError("validated status requires validated_value")

        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)


def assert_currency_match(assumptions: EconomicAssumptions, estimate_currency: str) -> None:
    """Reject currency mismatch between assumptions and estimate."""
    left = assumptions.currency.upper()
    right = (estimate_currency or "").strip().upper()
    if left != right:
        raise EconomicValidationError(
            f"currency mismatch: assumptions={left} estimate={right}"
        )


__all__ = [
    "KNOWN_CURRENCIES",
    "CONFIDENCE_LEVELS",
    "VALUE_STATUSES",
    "EXTREME_COST_THRESHOLD",
    "COST_FIELDS",
    "AssumptionSource",
    "EconomicValidationError",
    "EconomicAssumptions",
    "EconomicEstimate",
    "assert_currency_match",
]
