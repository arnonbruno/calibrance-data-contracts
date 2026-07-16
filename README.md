# calibrance-data-contracts

Shared Pydantic v2 schemas, enums, and type definitions for the Calibrance data foundry.

## Install

```bash
pip install -e .
```

## What's included

| Module | Contents |
|--------|----------|
| `enums` | `SourceType`, `HydrationLevel`, `SourceState`, `SignalChannel`, `AugmentationClass`, `TransformClass`, … |
| `rights` | `DatasetRightsPolicy` |
| `dataset` | `DatasetSource`, `DatasetVersionManifest`, `ArtifactRecord` |
| `signals` | `CanonicalSignals`, `QualityFlags` |
| `trajectory` | `CanonicalTrajectory`, `EventLabel`, `MediaStreamRef` |
| `provenance` | `ProvenanceRecord` |
| `augmentation` | `AugmentationConfig`, `AugmentationRecord` |
| `ontology` | `ObservedEvent`, `RootCause`, `Intervention`, `Outcome` |

## Quick start

```python
from calibrance_data_contracts import (
    CanonicalTrajectory,
    DatasetSource,
    SourceType,
    ObservedEvent,
)

source = DatasetSource(
    source_type=SourceType.UCI_ROBOT_FAILURES,
    name="UCI Robot Execution Failures",
)
```

## Requirements

- Python ≥ 3.10
- Pydantic ≥ 2.0

## License

MIT
