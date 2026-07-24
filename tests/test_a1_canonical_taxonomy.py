"""AUTOCAL-1 Stage A1 — canonical parameter taxonomy tests."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from calibrance_data_contracts.canonical_taxonomy import (
    CANONICAL_BY_ID,
    CANONICAL_PARAMETERS,
    TAXONOMY_VERSION,
    get_canonical_parameter,
)
from calibrance_data_contracts.taxonomy_migration import (
    AmbiguousAliasError,
    UnknownParameterError,
    assert_acceptance_gates,
    build_alias_table,
    build_taxonomy_manifest,
    canonical_to_old_id,
    deserialize_historical_profile,
    load_taxonomy_manifest,
    migration_rows,
    normalize_parameter_mapping,
    old_id_to_canonical,
    validate_alias_table,
)


REQUIRED_MIGRATIONS = [
    ("h1", "G4_payload.payload_mass_kg", "ur.payload.mass"),
    ("h1", "G2_friction.viscous_nm_s_rad", "ur.joint.friction.viscous"),
    ("h1", "G2_friction.coulomb_pos_nm", "ur.joint.friction.coulomb_positive"),
    ("h1", "G2_friction.coulomb_neg_nm", "ur.joint.friction.coulomb_negative"),
    ("h1", "G3_actuator.torque_constant_nm_per_a", "ur.actuator.torque_constant"),
    ("h1", "G3_actuator.torque_bias_nm", "ur.actuator.torque_bias"),
    ("h1", "G4_payload.payload_cog_m", "ur.payload.center_of_mass"),
    ("h5", "G1_friction.viscous", "ur.joint.friction.viscous"),
    ("h5", "G2_current_bias.torque_bias_nm", "ur.actuator.torque_bias"),
    ("h5", "G3_payload.payload_mass_kg", "ur.payload.mass"),
    ("h5", "G3_payload.payload_cog_m", "ur.payload.center_of_mass"),
    ("h5", "G4_current_scale.current_to_torque_scale", "ur.actuator.torque_constant"),
    ("h5", "G5_actuator_lag.actuator_lag_s", "ur.actuator.delay"),
    ("foundry", "link_6_mass_kg", "ur.payload.mass"),
    ("foundry", "viscous_friction_Nms_rad", "ur.joint.friction.viscous"),
    ("p7", "payload_mass_kg", "ur.payload.mass"),
    ("p7", "friction_viscous", "ur.joint.friction.viscous"),
    ("p7", "friction_coulomb", "ur.joint.friction.coulomb_positive"),
    ("p7", "inertia_kg_m2", "ur.link.inertia"),
]


def test_taxonomy_version() -> None:
    assert TAXONOMY_VERSION == "1.0.0"


def test_canonical_parameters_have_required_fields() -> None:
    required = {
        "parameter_id",
        "display_name",
        "group_id",
        "unit",
        "shape",
        "robot_model_scope",
        "joint_scope",
        "default_bounds",
        "physical_constraints",
        "identifiability_requirements",
        "supported_estimators",
        "profile_type",
        "deprecated_aliases",
    }
    for param in CANONICAL_PARAMETERS:
        missing = required - set(param.to_dict())
        assert not missing, f"{param.parameter_id} missing {missing}"
        assert param.parameter_id.startswith("ur.")
        assert "G1" not in param.parameter_id
        assert param.default_bounds["lower"] <= param.default_bounds["upper"]


def test_all_required_old_ids_map_to_exactly_one_canonical() -> None:
    for source, old_id, expected in REQUIRED_MIGRATIONS:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            got = old_id_to_canonical(old_id, source, warn=False)
        assert got == expected


def test_no_canonical_maps_to_multiple_preferred_old_ids_per_source() -> None:
    seen: dict[tuple[str, str], str] = {}
    for param in CANONICAL_PARAMETERS:
        for source, old_id in param.deprecated_aliases.items():
            key = (source, param.parameter_id)
            if key in seen:
                assert seen[key] == old_id
            seen[key] = old_id


def test_units_consistent_across_aliases() -> None:
    for record in build_alias_table():
        if record.canonical_id is None or record.unit is None:
            continue
        assert record.unit == CANONICAL_BY_ID[record.canonical_id].unit


def test_historical_profile_deserializes_with_canonical_ids() -> None:
    profile = {
        "profile_id": "hist-1",
        "parameters": {
            "G3_payload.payload_mass_kg": 1.5,
            "G1_friction.viscous": 0.12,
            "G2_current_bias.torque_bias_nm": 0.01,
        },
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        migrated = deserialize_historical_profile(profile, "h5")
    assert migrated["profile_id"] == "hist-1"
    assert migrated["parameters"] == {
        "ur.payload.mass": 1.5,
        "ur.joint.friction.viscous": 0.12,
        "ur.actuator.torque_bias": 0.01,
    }


def test_unknown_parameter_ids_are_rejected() -> None:
    with pytest.raises(UnknownParameterError):
        old_id_to_canonical("not_a_real_parameter", "h5", warn=False)


def test_non_calibration_ids_rejected_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        with pytest.raises(UnknownParameterError, match="noise-model|not a calibration"):
            old_id_to_canonical("measurement_noise_std", "foundry", warn=False)
    assert any("noise-model" in r.message or "noise" in r.message.lower() for r in caplog.records)

    with caplog.at_level("WARNING"):
        with pytest.raises(UnknownParameterError):
            old_id_to_canonical("stiffness_nm_rad", "p7", warn=False)


def test_deprecated_aliases_trigger_warnings() -> None:
    with pytest.warns(DeprecationWarning, match="ur.payload.mass"):
        old_id_to_canonical("G4_payload.payload_mass_kg", "h1", warn=True)


def test_canonical_to_old_id_roundtrip() -> None:
    assert canonical_to_old_id("ur.payload.mass", "h1") == "G4_payload.payload_mass_kg"
    assert canonical_to_old_id("ur.payload.mass", "h5") == "G3_payload.payload_mass_kg"
    assert canonical_to_old_id("ur.actuator.delay", "h1") is None
    assert canonical_to_old_id("ur.actuator.delay", "h5") == "G5_actuator_lag.actuator_lag_s"


def test_normalize_mapping_rejects_collapsing_aliases() -> None:
    with pytest.raises(AmbiguousAliasError):
        normalize_parameter_mapping(
            {
                "payload_mass_kg": 1.0,
                "G3_payload.payload_mass_kg": 2.0,
            },
            "h5",
            warn=False,
        )


def test_acceptance_gates_pass() -> None:
    gates = assert_acceptance_gates()
    assert gates == {
        "unmapped_parameter_ids": 0,
        "ambiguous_parameter_aliases": 0,
        "product_foundry_taxonomy_differences": 0,
        "historical_profile_deserialization_failures": 0,
        "unit_conflicts": 0,
    }


def test_manifest_on_disk_matches_builder() -> None:
    manifest_path = Path(__file__).resolve().parents[1] / (
        "src/calibrance_data_contracts/taxonomy_manifest.json"
    )
    assert manifest_path.is_file()
    on_disk = json.loads(manifest_path.read_text(encoding="utf-8"))
    built = build_taxonomy_manifest()
    assert on_disk["version"] == built["version"] == "1.0.0"
    assert on_disk["acceptance_gates"] == built["acceptance_gates"]
    assert len(on_disk["canonical_parameters"]) == len(CANONICAL_PARAMETERS)
    loaded = load_taxonomy_manifest(manifest_path)
    assert loaded["version"] == "1.0.0"


def test_get_canonical_parameter() -> None:
    p = get_canonical_parameter("ur.payload.mass")
    assert p.unit == "kg"
    with pytest.raises(KeyError):
        get_canonical_parameter("G1")


def test_migration_rows_cover_required() -> None:
    rows = {(r["source"], r["old_id"], r["canonical_id"]) for r in migration_rows()}
    for source, old_id, canonical in REQUIRED_MIGRATIONS:
        assert (source, old_id, canonical) in rows


def test_validate_alias_table_counts() -> None:
    counts = validate_alias_table()
    assert counts["unmapped_parameter_ids"] == 0
    assert counts["unit_conflicts"] == 0
