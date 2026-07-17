# Capability declarations — Milestone B (corrected)

## generic_anomaly_detection

```yaml
generic_anomaly_detection:
  detectable: true
  diagnosable: true
  method: "summary_forest"
  evidence_level: "E2"
  scope: "recorded UR3e screwdriving cycles (AURSAD dataset)"
  scope_limitation: "Single dataset. Other UR models, tasks, and real-time monitoring NOT validated."
  superiority_note: "Leads all baselines at every operating point. Paired superiority over logistic and RLS is inconclusive (CIs include zero). Selected as best available method."
  legacy_code_name: "summary_tree"
  actual_estimator: "sklearn.ensemble.RandomForestClassifier"
  n_estimators: 10
  max_depth: 5
```

## Erratum

`summary_tree` was the development codename. The qualified model is
`RandomForestClassifier(n_estimators=10, max_depth=5)`. Canonical family name:
`summary_forest`. Decision reason enum retains `USING_SUMMARY_TREE` for loader
compatibility and adds `USING_SUMMARY_FOREST`.

## Scope boundary

E2 applies ONLY to recorded UR3e screwdriving cycles from the AURSAD dataset.
This is NOT general UR e-Series digital-twin drift detection.
