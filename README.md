# calibrance-data-contracts

Shared schema layer for the Calibrance ecosystem — Pydantic v2 models, enums, and type definitions used by product and foundry.

**Version:** 0.2.0

## Ecosystem

Calibrance is split across three repositories:

| Repo | Role |
|------|------|
| **calibrance-data-contracts** (this repo) | Shared schemas and contracts — the common language between systems |
| **calibrance** (product) | Application, APIs, and UX that consume these contracts |
| **calibrance-data-foundry** | Data pipelines, datasets, and evaluation that produce and validate against these contracts |

Contracts stays intentionally thin: no pipeline logic, scoring, or product behavior — only interchange schemas.

## Install

```bash
pip install -e .
```

For development (tests and lint):

```bash
pip install -e ".[dev]"
```

## Current schemas

| Schema | Module | Purpose |
|--------|--------|---------|
| Task definition / binding | `task` | `TaskDefinition`, `TaskBinding`, `TaskTolerance`, `ActivityFamily` |
| Process event | `process_context` | `ProcessEvent`, `OperatingMode` |
| Quality observation | `quality_observation` | `QualityObservation` |
| Timestamp alignment | `timestamp_alignment` | `TimestampAlignment` |
| Intervention / outcome | `intervention_outcome` | `InterventionOutcomeChain`, recommendations, decisions, outcomes |
| Economic context | `economic_context` | `EconomicAssumptions`, `EconomicEstimate` |
| Evidence recommendation | `evidence_recommendation` | `EvidenceRecommendation` |
| Candidate validation | `candidate_validation` | `CandidateValidation`, dispositions and rejection reasons |

Additional modules (datasets, trajectories, evidence manifests, twin/calibration parameters, capture context, and related enums) are also exported from the package root.

## Quick start

```python
from calibrance_data_contracts import (
    ActivityFamily,
    TaskDefinition,
    TaskTolerance,
    ProcessEvent,
    QualityObservation,
    TimestampAlignment,
    InterventionOutcomeChain,
    EconomicAssumptions,
    EvidenceRecommendation,
    CandidateValidation,
)

task = TaskDefinition(
    task_id="precision-assembly-ur3e",
    name="UR3e precision assembly",
    activity_family=ActivityFamily.PRECISION_ASSEMBLY,
    robot_model="UR3e",
    tool_configuration={"tool": "gripper"},
    payload_range_kg=(0.0, 3.0),
    workspace_region={"frame": "base"},
    speed_range_m_s=(0.01, 0.5),
    acceleration_range_m_s2=(0.1, 2.0),
    required_signals=["actual_q", "actual_current"],
    relevant_parameter_groups=["friction", "inertia"],
    tolerances=TaskTolerance(
        position_tolerance_mm=1.0,
        orientation_tolerance_deg=2.0,
        torque_tolerance_pct=10.0,
        cycle_time_tolerance_pct=15.0,
    ),
    intended_monitoring_use="Detect drift during precision assembly cycles",
)
```

## Requirements

- Python ≥ 3.10
- Pydantic ≥ 2.0

## Testing

```bash
pytest
```

## License

MIT
