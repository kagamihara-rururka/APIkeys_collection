from __future__ import annotations

from dataclasses import fields
from typing import Any

from api_launcher.core_readiness_report import build_core_readiness_report
from api_launcher.manifests import AssetManifest, HASH_CHUNK_SIZE
from api_launcher.visual_asset_contracts import (
    visual_asset_registry_persistence_schema,
    visual_asset_ready_event_log_context,
    visual_asset_registry_entry_persistence_record,
    renderer_skin_asset_manifest_projection,
)


CORE_MANIFEST_REFERENCE_REPORT_SCHEMA_VERSION = "core_manifest_reference_report.v1"


def build_core_manifest_reference_report(repository: Any | None = None) -> dict[str, Any]:
    """Summarize manifest-reference evidence without reading payload bytes.

    RRKAL Core already has ordinary download sidecar manifests and a
    Visual/Skin manifest-reference contract. This diagnostic keeps those lanes
    distinct: it reports what Core can describe today, which parts remain
    contract-only, and which future persistence or health checks require a
    separate planning gate.
    """

    visual_schema = visual_asset_registry_persistence_schema()
    readiness_report = build_core_readiness_report(repository)
    manifest_evidence = readiness_report["manifest_reference_evidence"]
    lineage_evidence = readiness_report["asset_lineage_evidence"]

    return {
        "schema_version": CORE_MANIFEST_REFERENCE_REPORT_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "download_sidecar_manifest_contract": _download_sidecar_manifest_contract(),
            "visual_skin_manifest_reference_contract": _visual_skin_manifest_reference_contract(
                visual_schema
            ),
            "registry_persistence_projection": _registry_persistence_projection(visual_schema),
            "ready_event_manifest_context": _ready_event_manifest_context(),
            "readiness_report_bridge": {
                "schema_version": readiness_report["schema_version"],
                "gate_status": readiness_report["integration_planning_gate"]["status"],
                "manifest_reference_missing_evidence": list(
                    manifest_evidence.get("missing_evidence") or ()
                ),
                "manifest_reference_contract_only_surfaces": list(
                    manifest_evidence.get("contract_only_surfaces") or ()
                ),
                "asset_lineage_missing_evidence": list(
                    lineage_evidence.get("missing_evidence") or ()
                ),
            },
        },
        "missing_evidence": (
            "formal_user_database_manifest_reference_persistence_not_unified",
            "manifest_reference_payload_health_check_not_implemented",
            "cross_project_manifest_consumer_contract_not_finalized",
        ),
        "blocked_surfaces": (
            "renderer_payload_loading_disabled",
            "npz_payload_reading_disabled",
            "automatic_manifest_ready_event_emission_disabled",
        ),
        "review_required_surfaces": (
            "missing_manifest_path",
            "missing_checksum_or_size",
            "unsupported_manifest_payload_format",
            "unverified_external_manifest_reference",
        ),
        "contract_only_surfaces": (
            "visual_skin_asset_registry_table",
            "renderer_skin_asset_manifest_projection",
            "visual_asset_ready_event_log_context",
        ),
        "planned_surfaces": (
            "formal_user_database_visual_registry_persistence",
            "manifest_reference_health_audit",
            "downstream_manifest_consumer_contract",
        ),
        "next_safe_actions": (
            "keep_manifest_references_control_plane_only",
            "add_health_checks_without_reading_renderer_payloads",
            "request_o1_review_before_cross_project_manifest_consumer_contracts",
        ),
        "o1_review_triggers": (
            "cross_project_manifest_consumer_contract",
            "renderer_skin_asset_payload_health_check",
            "formal_user_database_manifest_reference_migration",
            "automatic_visual_asset_ready_event_emission",
            "any_npz_or_renderer_payload_read_in_core",
        ),
        "safety": {
            "control_plane_only": True,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "creates_manifest_persistence_schema": False,
            "changes_lifecycle_schema": False,
            "cross_repo_implementation": False,
        },
    }


def _download_sidecar_manifest_contract() -> dict[str, Any]:
    field_names = tuple(field.name for field in fields(AssetManifest))
    required_fields = (
        "provider_id",
        "dataset_uid",
        "dataset_id",
        "version",
        "source_url",
        "path",
        "size_bytes",
        "sha256",
    )
    return {
        "contract": "AssetManifest",
        "field_count": len(field_names),
        "fields": list(field_names),
        "required_fields": list(required_fields),
        "present_required_fields": [field for field in required_fields if field in field_names],
        "hash_algorithm": "sha256",
        "hash_chunk_size_bytes": HASH_CHUNK_SIZE,
        "schema_fingerprint_field": "schema_fingerprint" in field_names,
        "source_url_field": "source_url" in field_names,
        "sidecar_json_encoding": "utf-8",
    }


def _visual_skin_manifest_reference_contract(visual_schema: dict[str, Any]) -> dict[str, Any]:
    columns = _column_names(visual_schema)
    required_fields = (
        "manifest_path",
        "skin_asset_id",
        "source_request_id",
        "source_curated_asset_id",
        "dataset_uid",
        "renderer_targets_json",
        "checksum",
        "size_bytes",
    )
    return {
        "contract": "RendererSkinAssetReference",
        "projection_contract": renderer_skin_asset_manifest_projection.__name__,
        "required_fields": list(required_fields),
        "present_required_fields": [field for field in required_fields if field in columns],
        "missing_required_fields": [field for field in required_fields if field not in columns],
        "payload_columns_allowed": bool(
            (visual_schema.get("migration_guards") or {}).get("payload_columns_allowed")
        ),
        "payload_loading": bool((visual_schema.get("safety") or {}).get("payload_loading")),
    }


def _registry_persistence_projection(visual_schema: dict[str, Any]) -> dict[str, Any]:
    migration_guards = visual_schema.get("migration_guards") or {}
    safety = visual_schema.get("safety") or {}
    indexes = visual_schema.get("indexes") if isinstance(visual_schema.get("indexes"), list) else []
    return {
        "schema_contract": visual_schema.get("table_name", ""),
        "persistence_status": visual_schema.get("persistence_status", ""),
        "row_projection_contract": visual_asset_registry_entry_persistence_record.__name__,
        "primary_key": visual_schema.get("primary_key", ""),
        "index_count": len(indexes),
        "index_names": [
            str(index.get("name"))
            for index in indexes
            if isinstance(index, dict) and index.get("name")
        ],
        "requires_explicit_migration": bool(migration_guards.get("requires_explicit_migration")),
        "create_table_automatically": bool(migration_guards.get("create_table_automatically")),
        "auto_event_emission": bool(migration_guards.get("auto_event_emission")),
        "control_plane_only": bool(safety.get("control_plane_only")),
        "payload_loading": bool(safety.get("payload_loading")),
    }


def _ready_event_manifest_context() -> dict[str, Any]:
    return {
        "event_context_contract": visual_asset_ready_event_log_context.__name__,
        "carries_manifest_path": True,
        "carries_checksum": True,
        "carries_size_bytes": True,
        "carries_lineage": True,
        "ready_event_requires_ready_status": True,
        "automatic_event_emission": False,
        "payload_loading": False,
    }


def _column_names(visual_schema: dict[str, Any]) -> tuple[str, ...]:
    columns = visual_schema.get("columns") if isinstance(visual_schema.get("columns"), list) else []
    return tuple(
        str(column.get("name"))
        for column in columns
        if isinstance(column, dict) and column.get("name")
    )


__all__ = [
    "CORE_MANIFEST_REFERENCE_REPORT_SCHEMA_VERSION",
    "build_core_manifest_reference_report",
]
