# Task: Phase M0 — Contracts repo changes (PR-C1 + PR-C2 + EvidenceTier + ContributionMode)

## Context

You are working in the `calibrance-data-contracts` repository at `/var/home/bruno/calibrance-data-contracts`.
This is a MIT-licensed public Pydantic v2 schema package shared between the Calibrance product and data-foundry.

## What to do

### 1. Add EvidenceTier enum to enums.py

Add this enum to `src/calibrance_data_contracts/enums.py`:

```python
class EvidenceTier(str, Enum):
    """Evidence provenance tier for exported lifecycle facts.

    Tiers must never be merged silently. Every exported record must state exactly one tier.
    Ordered from least to most authoritative.
    """
    SYNTHETIC = "synthetic"
    RECORDED_REAL_REPLAY = "recorded_real_replay"
    URSIM_HIL = "ursim_hil"
    LIVE_SHADOW = "live_shadow"
    LIVE_HUMAN_APPROVED = "live_human_approved"
```

### 2. Add ContributionMode enum to enums.py

```python
class ContributionMode(str, Enum):
    """Tenant data contribution policy for moat/derived knowledge.

    PRIVATE (default) — no cross-customer derived use.
    COHORT — raw telemetry stays tenant-isolated; de-identified sufficient statistics allowed.
    RESEARCH_PARTNER — governed derived learning allowed.
    """
    PRIVATE = "private"
    COHORT = "cohort"
    RESEARCH_PARTNER = "research_partner"
```

### 3. Create CalibrationOutcomeEnvelope schema (PR-C1)

Create `src/calibrance_data_contracts/calibration_outcome.py`:

This is a NEUTRAL interchange schema. It describes facts and provenance only.
It must NOT contain scoring logic, proprietary cohort definitions, or promotion thresholds.
It must NOT contain hidden simulator truth, expected decisions, future golden outcomes, or evaluator-only fields.

Fields (Pydantic v2 BaseModel):

```yaml
event_id: str  # unique id
event_type: str  # e.g. "calibration.candidate_created.v1"
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
source_record_type: str  # e.g. "calibration_sessions"
source_record_id: str
source_record_version: int = 1
source_event_ids: list[str] = Field(default_factory=list)
provenance_digest: str
payload: dict = Field(default_factory=dict)  # type-specific facts, no hidden truth
created_at: datetime
```

### 4. Create ActivityFingerprint schema (PR-C2)

Create `src/calibrance_data_contracts/activity_fingerprint.py`:

A deterministic fingerprint of a robot activity for the Activity-Identifiability Atlas.
No learned embedding. Pure physical/kinematic descriptors.

Fields:

```yaml
fingerprint_version: str = "1.0"
robot_model: str
controller_major_version: str | None = None
configuration_digest: str
program_digest: str | None = None
activity_family: str  # e.g. "FAST_ACCELERATION_DECELERATION"
duration_s: float
sample_rate_hz: float
position_range_by_joint: dict[str, tuple[float, float]] = Field(default_factory=dict)
velocity_range_by_joint: dict[str, tuple[float, float]] = Field(default_factory=dict)
acceleration_range_by_joint: dict[str, tuple[float, float]] = Field(default_factory=dict)
velocity_reversals_by_joint: dict[str, int] = Field(default_factory=dict)
direction_coverage: float = 0.0  # 0-1
gravity_pose_diversity: float = 0.0  # 0-1
contact_fraction: float = 0.0  # 0-1
temperature_range: tuple[float, float] | None = None
channel_availability: list[str] = Field(default_factory=list)
```

### 5. Update __init__.py

Export all new types:
- `EvidenceTier` and `ContributionMode` from enums
- `CalibrationOutcomeEnvelope` from calibration_outcome
- `ActivityFingerprint` from activity_fingerprint

Add them to `__all__` as well.

### 6. Write tests

Create `tests/test_m0_contracts.py` with:

- EvidenceTier has exactly 5 members with correct values
- ContributionMode has exactly 3 members with correct values
- CalibrationOutcomeEnvelope validates a complete envelope
- CalibrationOutcomeEnvelope rejects unknown evidence_tier
- CalibrationOutcomeEnvelope rejects unknown contribution_mode
- CalibrationOutcomeEnvelope defaults contribution_mode to PRIVATE
- ActivityFingerprint validates a complete fingerprint
- ActivityFingerprint defaults optional fields correctly
- A hidden-truth scan test: verify that CalibrationOutcomeEnvelope payload field does not allow keys named: scenario_class, hidden_parameters, expected_outcome, true_candidate_error, future_golden_result (this should be a schema validator or a test function that checks the payload dict keys)

### 7. Run tests

Run: `cd /var/home/bruno/calibrance-data-contracts && python3 -m pytest tests/test_m0_contracts.py -v`

### 8. Commit

```bash
git add -A && git -c user.email=tarsdabot@gmail.com -c user.name=TARS commit -m 'feat(m0): add EvidenceTier, ContributionMode, CalibrationOutcomeEnvelope, ActivityFingerprint schemas'
```

Do NOT push.
