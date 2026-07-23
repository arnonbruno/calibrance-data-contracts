"""Model adequacy contracts for dynamics twin selection (Gate H1)."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ModelAdequacyClass(str, Enum):
    """Adequacy classification for a dynamics twin against observed residuals."""

    ADEQUATE = "adequate"
    MARGINAL = "marginal"
    INADEQUATE = "inadequate"


class ModelAdequacyMetrics(BaseModel):
    """Quantitative adequacy of a dynamics twin on a calibration dataset."""

    torque_rmse_nm: float = Field(ge=0.0)
    current_rmse_a: float = Field(ge=0.0)
    torque_max_abs_nm: float = Field(ge=0.0)
    residual_whiteness_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional residual autocorrelation score in [0, 1].",
    )
    n_samples: int = Field(ge=1)


class ModelAdequacyDecision(BaseModel):
    """Accept / reject decision for a candidate twin model class."""

    robot_model: Literal["UR3e"]
    model_class: str
    accepted: bool
    classification: ModelAdequacyClass
    metrics: ModelAdequacyMetrics
    reason_codes: list[str] = Field(default_factory=list)
    policy_digest: str
