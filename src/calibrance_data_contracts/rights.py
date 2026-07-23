"""
Dataset rights policy model for the Calibrance data foundry.

A :class:`DatasetRightsPolicy` captures the licensing and usage constraints
for a dataset source.  It is the authoritative object consulted by the
rights-review gate in the ingestion state machine.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Licence identifiers that are considered "clearly permissive".
# ---------------------------------------------------------------------------

PERMISSIVE_LICENSE_IDS: frozenset[str] = frozenset(
    {
        "CC0",
        "CC0_1_0",
        "CC_BY_4_0",
        "CC_BY_3_0",
        "MIT",
        "APACHE_2_0",
        "BSD_2_CLAUSE",
        "BSD_3_CLAUSE",
        "ISC",
        "OFL_1_1",
    }
)

# "yes" | "no" | "unknown"
TriBool = Literal["yes", "no", "unknown"]


class DatasetRightsPolicy(BaseModel):
    """
    Rights and licensing policy attached to a dataset source.

    Fields follow the Calibrance data foundry spec §5.3.
    """

    license_id: str = Field(
        ..., description="SPDX-style or custom license identifier (e.g. 'CC_BY_4_0')."
    )
    license_text_sha256: Optional[str] = Field(
        default=None, description="SHA-256 of the canonical license text."
    )
    terms_url_hash: Optional[str] = Field(
        default=None, description="SHA-256 of the terms-of-use page content at review time."
    )
    reviewed_at: Optional[datetime] = Field(
        default=None, description="When the rights review was completed (UTC)."
    )
    reviewer_id: Optional[str] = Field(
        default=None, description="Identifier of the human/system reviewer."
    )

    # Usage permissions (tri-valued: yes / no / unknown)
    commercial_training: TriBool = Field(
        default="unknown", description="May the data be used for commercial training?"
    )
    commercial_evaluation: TriBool = Field(
        default="unknown", description="May the data be used for commercial evaluation?"
    )
    redistribution: TriBool = Field(
        default="unknown", description="May the dataset be redistributed?"
    )
    derivative_datasets: TriBool = Field(
        default="unknown", description="May derivative datasets be created?"
    )
    model_distribution: TriBool = Field(
        default="unknown", description="May models trained on this data be distributed?"
    )

    # Licence clauses (boolean flags)
    attribution_required: bool = Field(
        default=False, description="Does the licence require attribution?"
    )
    share_alike: bool = Field(
        default=False, description="Does the licence impose a share-alike clause (copyleft)?"
    )
    noncommercial: bool = Field(default=False, description="Is the licence non-commercial only?")
    no_derivatives: bool = Field(
        default=False, description="Does the licence prohibit derivative works?"
    )

    # Risk flags – any True value blocks auto-approval
    personal_data_possible: bool = Field(
        default=False,
        description="Could the dataset contain personal data?",
    )
    human_subjects_possible: bool = Field(
        default=False,
        description="Could the dataset involve human subjects data?",
    )
    export_restriction_possible: bool = Field(
        default=False,
        description="Is there a potential export-control restriction?",
    )

    notes: str = Field(default="", description="Free-text notes from the reviewer.")

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def is_commercial_training_allowed(self) -> bool:
        """Return True only if commercial training is explicitly permitted."""
        return self.commercial_training == "yes"

    def is_auto_approvable(self) -> bool:
        """
        Return True if the rights policy can be auto-approved without
        manual review.

        Criteria:
        - ``license_id`` is in :data:`PERMISSIVE_LICENSE_IDS`
        - None of the risk flags (personal data, human subjects, export
          restriction) are set.
        - ``noncommercial`` and ``no_derivatives`` are not set (these would
          block commercial training).
        """
        if self.license_id not in PERMISSIVE_LICENSE_IDS:
            return False

        if (
            self.personal_data_possible
            or self.human_subjects_possible
            or self.export_restriction_possible
        ):
            return False

        if self.noncommercial or self.no_derivatives:
            return False

        return True


__all__ = ["DatasetRightsPolicy", "PERMISSIVE_LICENSE_IDS", "TriBool"]
