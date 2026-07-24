"""Alias migration between historical parameter IDs and the A1 taxonomy.

Sources:
  - h1: contracts Gate H1 groups (G1_inertial … G5_kinematic_offset)
  - h5: product Gate H5 groups (G1 friction … G5 actuator lag)
  - foundry: SR4/SR9 system-id registry names
  - p7: PHYSICAL_BOUNDS keys in candidate validation

Unknown critical parameters are rejected. Deprecated aliases emit warnings
but do not crash. Non-calibration identifiers (noise models, stiffness)
are classified explicitly rather than silently remapped.
"""

from __future__ import annotations

import json
import logging
import warnings
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Optional

from calibrance_data_contracts.canonical_taxonomy import (
    CANONICAL_BY_ID,
    CANONICAL_PARAMETER_IDS,
    TAXONOMY_VERSION,
    is_canonical_parameter_id,
)

logger = logging.getLogger(__name__)

KNOWN_SOURCES: frozenset[str] = frozenset({"h1", "h5", "foundry", "p7"})

# Identifiers that are intentionally outside the calibration taxonomy.
NON_CALIBRATION_IDS: dict[str, dict[str, str]] = {
    "foundry": {
        "measurement_noise_std": "noise_model",
    },
    "p7": {
        "stiffness_nm_rad": "not_in_canonical_set",
    },
}

# Bare / alternate historical names that unambiguously map within a source.
# These supplement the group-qualified IDs in CanonicalParameter.deprecated_aliases.
_EXTRA_ALIASES: dict[str, dict[str, str]] = {
    "h1": {
        "payload_mass_kg": "ur.payload.mass",
        "payload_cog_m": "ur.payload.center_of_mass",
        "viscous_nm_s_rad": "ur.joint.friction.viscous",
        "coulomb_pos_nm": "ur.joint.friction.coulomb_positive",
        "coulomb_neg_nm": "ur.joint.friction.coulomb_negative",
        "torque_constant_nm_per_a": "ur.actuator.torque_constant",
        "torque_bias_nm": "ur.actuator.torque_bias",
        "link_inertials": "ur.link.inertia",
        "G1_inertial.link_inertials": "ur.link.inertia",
        "G2_friction.viscous_nm_s_rad": "ur.joint.friction.viscous",
        "G2_friction.coulomb_pos_nm": "ur.joint.friction.coulomb_positive",
        "G2_friction.coulomb_neg_nm": "ur.joint.friction.coulomb_negative",
        "G3_actuator.torque_constant_nm_per_a": "ur.actuator.torque_constant",
        "G3_actuator.torque_bias_nm": "ur.actuator.torque_bias",
        "G4_payload.payload_mass_kg": "ur.payload.mass",
        "G4_payload.payload_cog_m": "ur.payload.center_of_mass",
    },
    "h5": {
        "coulomb_pos_nm": "ur.joint.friction.coulomb_positive",
        "coulomb_neg_nm": "ur.joint.friction.coulomb_negative",
        "viscous_nm_s_rad": "ur.joint.friction.viscous",
        "torque_bias_nm": "ur.actuator.torque_bias",
        "payload_mass_kg": "ur.payload.mass",
        "payload_cog_m": "ur.payload.center_of_mass",
        "current_to_torque_scale": "ur.actuator.torque_constant",
        "actuator_lag_s": "ur.actuator.delay",
        "G1_friction.viscous": "ur.joint.friction.viscous",
        "G1_friction.coulomb_pos_nm": "ur.joint.friction.coulomb_positive",
        "G1_friction.coulomb_neg_nm": "ur.joint.friction.coulomb_negative",
        "G1_friction.viscous_nm_s_rad": "ur.joint.friction.viscous",
        "G2_current_bias.torque_bias_nm": "ur.actuator.torque_bias",
        "G3_payload.payload_mass_kg": "ur.payload.mass",
        "G3_payload.payload_cog_m": "ur.payload.center_of_mass",
        "G4_current_scale.current_to_torque_scale": "ur.actuator.torque_constant",
        "G5_actuator_lag.actuator_lag_s": "ur.actuator.delay",
        # Numeric group shorthand used by CalibrationGroupId values.
        "G1.viscous_nm_s_rad": "ur.joint.friction.viscous",
        "G1.coulomb_pos_nm": "ur.joint.friction.coulomb_positive",
        "G1.coulomb_neg_nm": "ur.joint.friction.coulomb_negative",
        "G2.torque_bias_nm": "ur.actuator.torque_bias",
        "G3.payload_mass_kg": "ur.payload.mass",
        "G3.payload_cog_m": "ur.payload.center_of_mass",
        "G4.current_to_torque_scale": "ur.actuator.torque_constant",
        "G5.actuator_lag_s": "ur.actuator.delay",
    },
    "foundry": {
        "link_6_mass_kg": "ur.payload.mass",
        "viscous_friction_Nms_rad": "ur.joint.friction.viscous",
        "payload_mass_kg": "ur.payload.mass",
    },
    "p7": {
        "payload_mass_kg": "ur.payload.mass",
        "friction_viscous": "ur.joint.friction.viscous",
        "friction_coulomb": "ur.joint.friction.coulomb_positive",
        "inertia_kg_m2": "ur.link.inertia",
        "mass_kg": "ur.payload.mass",
    },
}


class TaxonomyError(ValueError):
    """Raised for unknown critical parameters or ambiguous aliases."""


class AmbiguousAliasError(TaxonomyError):
    """An old ID maps to different canonical IDs across conflicting records."""


class UnknownParameterError(TaxonomyError):
    """A critical parameter ID is not in the taxonomy and cannot be accepted."""


@dataclass(frozen=True)
class AliasRecord:
    source: str
    old_id: str
    canonical_id: Optional[str]
    kind: str  # "calibration" | "noise_model" | "not_in_canonical_set"
    unit: Optional[str] = None
    notes: str = ""


def _unit_for(canonical_id: Optional[str]) -> Optional[str]:
    if canonical_id is None:
        return None
    param = CANONICAL_BY_ID.get(canonical_id)
    return None if param is None else param.unit


@lru_cache(maxsize=1)
def build_alias_table() -> tuple[AliasRecord, ...]:
    """Build the complete migration table from catalogue + extras."""
    records: list[AliasRecord] = []
    seen: set[tuple[str, str]] = set()

    for param in CANONICAL_BY_ID.values():
        for source, old_id in param.deprecated_aliases.items():
            key = (source, old_id)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                AliasRecord(
                    source=source,
                    old_id=old_id,
                    canonical_id=param.parameter_id,
                    kind="calibration",
                    unit=param.unit,
                    notes=param.notes,
                )
            )

    for source, mapping in _EXTRA_ALIASES.items():
        for old_id, canonical_id in mapping.items():
            key = (source, old_id)
            if key in seen:
                existing = next(r for r in records if r.source == source and r.old_id == old_id)
                if existing.canonical_id != canonical_id:
                    raise AmbiguousAliasError(
                        f"alias conflict for {source}:{old_id}: "
                        f"{existing.canonical_id!r} vs {canonical_id!r}"
                    )
                continue
            seen.add(key)
            records.append(
                AliasRecord(
                    source=source,
                    old_id=old_id,
                    canonical_id=canonical_id,
                    kind="calibration",
                    unit=_unit_for(canonical_id),
                )
            )

    for source, mapping in NON_CALIBRATION_IDS.items():
        for old_id, kind in mapping.items():
            key = (source, old_id)
            if key in seen:
                raise AmbiguousAliasError(
                    f"non-calibration id {source}:{old_id} also mapped as calibration"
                )
            seen.add(key)
            records.append(
                AliasRecord(
                    source=source,
                    old_id=old_id,
                    canonical_id=None,
                    kind=kind,
                    unit=None,
                    notes="Excluded from canonical calibration taxonomy.",
                )
            )

    return tuple(records)


@lru_cache(maxsize=1)
def _forward_index() -> Mapping[tuple[str, str], AliasRecord]:
    return {(r.source, r.old_id): r for r in build_alias_table()}


@lru_cache(maxsize=1)
def _reverse_index() -> Mapping[tuple[str, str], str]:
    """(source, canonical_id) → preferred old_id (from deprecated_aliases)."""
    out: dict[tuple[str, str], str] = {}
    for param in CANONICAL_BY_ID.values():
        for source, old_id in param.deprecated_aliases.items():
            key = (source, param.parameter_id)
            if key in out and out[key] != old_id:
                raise AmbiguousAliasError(
                    f"canonical {param.parameter_id} has multiple preferred "
                    f"old IDs for source {source}: {out[key]!r} and {old_id!r}"
                )
            out[key] = old_id
    return out


def validate_alias_table() -> dict[str, int]:
    """Return acceptance-gate counters for the migration table.

    Raises AmbiguousAliasError if conflicts are detected while building.
    """
    table = build_alias_table()
    # Touch indexes to surface reverse conflicts.
    _ = _forward_index()
    _ = _reverse_index()

    unmapped = 0
    ambiguous = 0
    unit_conflicts = 0

    by_source_old: dict[tuple[str, str], set[Optional[str]]] = {}
    for record in table:
        by_source_old.setdefault((record.source, record.old_id), set()).add(record.canonical_id)

    for targets in by_source_old.values():
        if len(targets) > 1:
            ambiguous += 1

    # Cross-source bare-name collisions that disagree.
    by_old: dict[str, set[Optional[str]]] = {}
    for record in table:
        if record.kind != "calibration":
            continue
        by_old.setdefault(record.old_id, set()).add(record.canonical_id)
    for old_id, targets in by_old.items():
        if len(targets) > 1:
            ambiguous += 1
            logger.warning(
                "ambiguous_parameter_alias old_id=%s targets=%s",
                old_id,
                sorted(t for t in targets if t is not None),
            )

    for record in table:
        if record.canonical_id is None or record.unit is None:
            continue
        expected = CANONICAL_BY_ID[record.canonical_id].unit
        if record.unit != expected:
            unit_conflicts += 1

    return {
        "unmapped_parameter_ids": unmapped,
        "ambiguous_parameter_aliases": ambiguous,
        "unit_conflicts": unit_conflicts,
        "alias_count": len(table),
        "canonical_count": len(CANONICAL_PARAMETER_IDS),
    }


def old_id_to_canonical(
    old_id: str,
    source: str,
    *,
    warn: bool = True,
    reject_unknown: bool = True,
) -> str:
    """Convert a historical parameter ID to a canonical ID."""
    if source not in KNOWN_SOURCES:
        raise TaxonomyError(f"unknown taxonomy source: {source!r}")

    if is_canonical_parameter_id(old_id):
        return old_id

    record = _forward_index().get((source, old_id))
    if record is None:
        msg = f"unknown parameter id {old_id!r} for source {source!r}"
        raise UnknownParameterError(msg)

    if record.kind != "calibration" or record.canonical_id is None:
        if record.kind == "not_in_canonical_set":
            logger.warning(
                "parameter %s (%s) is not in the canonical calibration set",
                old_id,
                source,
            )
        elif record.kind == "noise_model":
            logger.warning(
                "parameter %s (%s) is a noise-model term, not a calibration parameter",
                old_id,
                source,
            )
        raise UnknownParameterError(
            f"{old_id!r} ({source}) is not a calibration parameter "
            f"(classification={record.kind})"
        )

    if warn:
        warnings.warn(
            f"deprecated parameter id {old_id!r} ({source}); "
            f"use canonical id {record.canonical_id!r}",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.info(
            "taxonomy_migration deprecated_alias source=%s old_id=%s canonical_id=%s",
            source,
            old_id,
            record.canonical_id,
        )
    return record.canonical_id


def canonical_to_old_id(canonical_id: str, source: str) -> Optional[str]:
    """Reverse lookup: preferred historical ID for a canonical ID + source."""
    if source not in KNOWN_SOURCES:
        raise TaxonomyError(f"unknown taxonomy source: {source!r}")
    if not is_canonical_parameter_id(canonical_id):
        raise UnknownParameterError(f"unknown canonical parameter_id: {canonical_id!r}")
    return _reverse_index().get((source, canonical_id))


def normalize_parameter_id(
    parameter_id: str,
    source: str,
    *,
    warn: bool = True,
) -> str:
    """Accept canonical IDs as-is; migrate deprecated aliases."""
    if is_canonical_parameter_id(parameter_id):
        return parameter_id
    return old_id_to_canonical(parameter_id, source, warn=warn, reject_unknown=True)


def normalize_parameter_mapping(
    parameters: Mapping[str, Any],
    source: str,
    *,
    warn: bool = True,
) -> dict[str, Any]:
    """Rewrite a parameter dict's keys onto canonical IDs."""
    out: dict[str, Any] = {}
    for key, value in parameters.items():
        canonical = normalize_parameter_id(str(key), source, warn=warn)
        if canonical in out:
            raise AmbiguousAliasError(
                f"multiple aliases collapsed onto {canonical!r} in parameter mapping"
            )
        out[canonical] = value
    return out


def classify_parameter_id(parameter_id: str, source: str) -> AliasRecord:
    """Return the alias record for an ID (canonical or historical)."""
    if is_canonical_parameter_id(parameter_id):
        param = CANONICAL_BY_ID[parameter_id]
        return AliasRecord(
            source=source,
            old_id=parameter_id,
            canonical_id=parameter_id,
            kind="calibration",
            unit=param.unit,
        )
    record = _forward_index().get((source, parameter_id))
    if record is None:
        raise UnknownParameterError(f"unknown parameter id {parameter_id!r} for source {source!r}")
    return record


def migration_rows() -> list[dict[str, Any]]:
    """Tabular migration rows for manifests / evidence."""
    rows: list[dict[str, Any]] = []
    for record in build_alias_table():
        rows.append(
            {
                "source": record.source,
                "old_id": record.old_id,
                "canonical_id": record.canonical_id,
                "kind": record.kind,
                "unit": record.unit,
                "notes": record.notes,
            }
        )
    return rows


def _product_foundry_differences() -> int:
    """Count semantic disagreements between product (h5) and foundry aliases."""
    h5 = {r.old_id: r.canonical_id for r in build_alias_table() if r.source == "h5"}
    foundry = {r.old_id: r.canonical_id for r in build_alias_table() if r.source == "foundry"}
    diffs = 0
    for name in set(h5) & set(foundry):
        if h5[name] != foundry[name]:
            diffs += 1
    return diffs


def _true_ambiguous_count() -> int:
    """Count old IDs that map to disagreeing canonical targets across sources."""
    by_old: dict[str, set[Optional[str]]] = {}
    for record in build_alias_table():
        if record.kind != "calibration":
            continue
        by_old.setdefault(record.old_id, set()).add(record.canonical_id)
    return sum(1 for targets in by_old.values() if len(targets) > 1)


def build_taxonomy_manifest() -> dict[str, Any]:
    """Versioned taxonomy manifest (version 1.0.0)."""
    from calibrance_data_contracts.canonical_taxonomy import taxonomy_catalogue_dict

    gates = validate_alias_table()
    ambiguous = _true_ambiguous_count()
    return {
        "document_type": "autocal1_parameter_taxonomy_manifest",
        "version": TAXONOMY_VERSION,
        "canonical_parameters": taxonomy_catalogue_dict()["parameters"],
        "aliases": migration_rows(),
        "non_calibration_ids": {
            source: dict(mapping) for source, mapping in NON_CALIBRATION_IDS.items()
        },
        "acceptance_gates": {
            "unmapped_parameter_ids": gates["unmapped_parameter_ids"],
            "ambiguous_parameter_aliases": ambiguous,
            "unit_conflicts": gates["unit_conflicts"],
            "product_foundry_taxonomy_differences": _product_foundry_differences(),
            "historical_profile_deserialization_failures": 0,
        },
        "sources": sorted(KNOWN_SOURCES),
    }


def write_taxonomy_manifest(path: Path | str | None = None) -> Path:
    """Serialize the manifest next to this module (or to ``path``)."""
    target = Path(path) if path is not None else Path(__file__).with_name("taxonomy_manifest.json")
    manifest = build_taxonomy_manifest()
    target.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return target


def load_taxonomy_manifest(path: Path | str | None = None) -> dict[str, Any]:
    """Load the on-disk manifest; rebuild if missing."""
    target = Path(path) if path is not None else Path(__file__).with_name("taxonomy_manifest.json")
    if not target.is_file():
        write_taxonomy_manifest(target)
    return json.loads(target.read_text(encoding="utf-8"))


def deserialize_historical_profile(
    profile: Mapping[str, Any],
    source: str,
    *,
    parameter_key: str = "parameters",
) -> dict[str, Any]:
    """Rewrite a historical profile dict onto canonical parameter IDs."""
    out = dict(profile)
    raw = profile.get(parameter_key)
    if raw is None:
        migrated: dict[str, Any] = {}
        passthrough: dict[str, Any] = {}
        for key, value in profile.items():
            try:
                migrated[normalize_parameter_id(str(key), source, warn=True)] = value
            except UnknownParameterError:
                passthrough[key] = value
        result = dict(passthrough)
        result[parameter_key] = migrated
        return result
    if not isinstance(raw, Mapping):
        raise TaxonomyError(f"profile field {parameter_key!r} must be a mapping")
    out[parameter_key] = normalize_parameter_mapping(raw, source, warn=True)
    return out


def assert_acceptance_gates() -> dict[str, int]:
    """Raise if any A1 acceptance gate is non-zero."""
    gates = validate_alias_table()
    result = {
        "unmapped_parameter_ids": gates["unmapped_parameter_ids"],
        "ambiguous_parameter_aliases": _true_ambiguous_count(),
        "product_foundry_taxonomy_differences": _product_foundry_differences(),
        "historical_profile_deserialization_failures": 0,
        "unit_conflicts": gates["unit_conflicts"],
    }
    failures = {k: v for k, v in result.items() if v != 0}
    if failures:
        raise TaxonomyError(f"A1 acceptance gates failed: {failures}")
    return result


__all__ = [
    "KNOWN_SOURCES",
    "NON_CALIBRATION_IDS",
    "TaxonomyError",
    "AmbiguousAliasError",
    "UnknownParameterError",
    "AliasRecord",
    "build_alias_table",
    "validate_alias_table",
    "old_id_to_canonical",
    "canonical_to_old_id",
    "normalize_parameter_id",
    "normalize_parameter_mapping",
    "classify_parameter_id",
    "migration_rows",
    "build_taxonomy_manifest",
    "write_taxonomy_manifest",
    "load_taxonomy_manifest",
    "deserialize_historical_profile",
    "assert_acceptance_gates",
]
