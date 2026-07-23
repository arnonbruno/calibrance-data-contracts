"""P5 economic context schema — assumptions and four-category estimates."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from calibrance_data_contracts import (
    AssumptionSource,
    EconomicAssumptions,
    EconomicEstimate,
    EconomicValidationError,
    assert_currency_match,
)

TS = datetime(2026, 7, 23, 14, 0, tzinfo=timezone.utc)


def _assumptions(**overrides) -> EconomicAssumptions:
    data = dict(
        assumptions_id="asm-001",
        tenant_id="tenant-a",
        currency="USD",
        downtime_cost_per_hour=2500.0,
        engineering_cost_per_hour=200.0,
        scrap_cost_per_unit=50.0,
        rework_cost_per_unit=25.0,
        maintenance_action_cost=500.0,
        production_interruption_cost_per_minute=30.0,
        units_per_hour=120.0,
        quality_escape_cost=1000.0,
        source=AssumptionSource.ESTIMATED,
        confidence="low",
        provided_at=TS,
    )
    data.update(overrides)
    return EconomicAssumptions(**data)


def _estimate(**overrides) -> EconomicEstimate:
    data = dict(
        estimate_id="est-001",
        tenant_id="tenant-a",
        asset_id="asset-1",
        task_id="task-1",
        recommendation_id="rec-001",
        estimated_exposure={
            "downtime_range_usd": [2500, 5000],
            "engineering_investigation_usd": 800,
            "quality_risk_usd": [500, 2000],
            "confidence": "hypothetical_demo",
        },
        expected_action={
            "expected_duration_minutes": 10,
            "interruption_cost_usd": 300,
            "expected_information_gain": 0.58,
            "expected_residual_improvement_pct": 15,
        },
        observed_outcome=None,
        validated_value=None,
        value_status="estimated_not_observed",
        assumptions_id="asm-001",
        created_at=TS,
        evidence_tier="synthetic",
        currency="USD",
        labels={"DEMO": True, "SYNTHETIC": True, "NOT_REALIZED_SAVINGS": True},
        affects_activation=False,
    )
    data.update(overrides)
    return EconomicEstimate(**data)


def test_assumptions_accept_valid() -> None:
    a = _assumptions()
    assert a.currency == "USD"
    assert a.source == AssumptionSource.ESTIMATED
    assert a.warnings == []


def test_negative_cost_rejected() -> None:
    with pytest.raises(EconomicValidationError, match="invalid cost"):
        _assumptions(downtime_cost_per_hour=-1.0)


def test_currency_ambiguity_rejected() -> None:
    with pytest.raises(EconomicValidationError, match="currency ambiguity"):
        _assumptions(currency="US")
    with pytest.raises(EconomicValidationError, match="currency ambiguity"):
        _assumptions(currency="XXX")


def test_extreme_values_warn() -> None:
    a = _assumptions(downtime_cost_per_hour=2_000_000.0)
    assert any("extremely high" in w for w in a.warnings)


def test_estimate_requires_assumptions() -> None:
    with pytest.raises(EconomicValidationError, match="without assumptions"):
        _estimate(assumptions_id="")


def test_synthetic_cannot_be_realized() -> None:
    with pytest.raises(EconomicValidationError, match="realized"):
        _estimate(observed_outcome={"savings_usd": 1000})
    with pytest.raises(EconomicValidationError, match="realized"):
        _estimate(validated_value={"savings_usd": 1000})


def test_affects_activation_forbidden() -> None:
    with pytest.raises(EconomicValidationError, match="activation"):
        _estimate(affects_activation=True)


def test_currency_mismatch() -> None:
    a = _assumptions(currency="EUR")
    with pytest.raises(EconomicValidationError, match="currency mismatch"):
        assert_currency_match(a, "USD")


def test_demo_estimate_labels() -> None:
    e = _estimate()
    assert e.value_status == "estimated_not_observed"
    assert e.observed_outcome is None
    assert e.validated_value is None
    assert e.labels["NOT_REALIZED_SAVINGS"] is True
    assert e.affects_activation is False
