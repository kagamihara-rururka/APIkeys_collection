from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from api_launcher.content_registry import content_registry_report
from api_launcher.core_review_item_contracts import review_item_identity_contract_draft
from api_launcher.core_openspec_evidence import build_core_openspec_evidence
from api_launcher.core_scheduler_contracts import (
    scheduler_job_contract_draft,
    scheduler_lifecycle_event_emission_guard_contract,
    scheduler_next_action_payload_contract,
    scheduler_o1_review_gate_contract,
)
from api_launcher.core_scheduler_persistence_contract import (
    scheduler_queue_owned_test_table_helper_contract,
    scheduler_queue_sqlite_ddl_preview,
)
from api_launcher.crawler_registry_report import crawler_registry_report
from api_launcher.dataset_adapters import dataset_adapter_report
from api_launcher.project_maturity import build_project_maturity_payload
from api_launcher.visual_asset_contracts import (
    SKIN_ASSET_LIFECYCLE_STATUSES,
    skin_asset_status_display_profile,
    visual_asset_registry_persistence_schema,
    visual_asset_registry_summary,
)


def build_core_readiness_sections(repository: Any | None = None) -> dict[str, dict[str, Any]]:
    """Build the evidence sections for the Core readiness report.

    This module keeps the section-specific evidence collection separate from
    report-level gate decisions. The caller still owns schema versioning,
    safety flags, and integration-planning status.
    """

    crawler_report = crawler_registry_report()
    content_report = content_registry_report()
    adapter_report = dataset_adapter_report()
    visual_schema = visual_asset_registry_persistence_schema()
    empty_visual_summary = visual_asset_registry_summary(())
    maturity_payload = build_project_maturity_payload(repository) if repository is not None else {}
    openspec_report = build_core_openspec_evidence()

    return {
        "registry_evidence": _registry_evidence(crawler_report, content_report, adapter_report),
        "lifecycle_evidence": _lifecycle_evidence(visual_schema, empty_visual_summary),
        "manifest_reference_evidence": _manifest_reference_evidence(visual_schema),
        "review_required_evidence": _review_required_evidence(
            content_report,
            empty_visual_summary,
        ),
        "job_status_evidence": _job_status_evidence(visual_schema, maturity_payload),
        "asset_lineage_evidence": _asset_lineage_evidence(visual_schema),
        "openspec_evidence": _openspec_evidence(openspec_report),
    }


def _registry_evidence(
    crawler_report: dict[str, Any],
    content_report: dict[str, Any],
    adapter_report: dict[str, Any],
) -> dict[str, Any]:
    evidence = {
        "crawler_registry": {
            "source_type_count": int(crawler_report.get("source_type_count") or 0),
            "matrix_cell_count": int(crawler_report.get("matrix_cell_count") or 0),
            "capability_group_count": len(crawler_report.get("capability_groups") or ()),
            "next_action": crawler_report.get("next_action", ""),
        },
        "content_registry": {
            "supported_sqlite_format_count": int(content_report.get("supported_sqlite_format_count") or 0),
            "review_rule_count": int(content_report.get("review_rule_count") or 0),
            "resolver_backed_format_count": int(content_report.get("resolver_backed_format_count") or 0),
            "unknown_fallback_review_bucket": content_report.get("unknown_fallback_review_bucket", ""),
        },
        "dataset_adapter_registry": {
            "dataset_adapter_count": int(adapter_report.get("dataset_adapter_count") or 0),
            "adapter_ids": list(adapter_report.get("adapter_ids") or ()),
            "coverage_boundary": adapter_report.get("coverage_boundary", ""),
        },
    }
    missing = []
    if evidence["dataset_adapter_registry"]["dataset_adapter_count"] < evidence["crawler_registry"]["source_type_count"]:
        missing.append("deep_adapter_coverage_does_not_match_supported_source_types")
    return {
        "existing_evidence": evidence,
        "missing_evidence": missing,
        "blocked_surfaces": [],
        "review_required_surfaces": _review_rule_ids(content_report),
        "contract_only_surfaces": [],
        "planned_surfaces": [],
        "next_safe_actions": (
            "add_deep_adapters_only_when_they_close_real_download_import_paths",
            "keep_source_type_dispatch_in_registry_not_scattered_if_else",
        ),
    }


def _lifecycle_evidence(visual_schema: dict[str, Any], empty_summary: dict[str, Any]) -> dict[str, Any]:
    statuses = sorted(SKIN_ASSET_LIFECYCLE_STATUSES)
    display_profiles = {
        status: skin_asset_status_display_profile(status)
        for status in statuses
    }
    return {
        "existing_evidence": {
            "status_count": len(statuses),
            "statuses": statuses,
            "status_display_profiles": display_profiles,
            "empty_registry_status_counts": dict(empty_summary.get("status_counts") or {}),
            "schema_allowed_lifecycle_statuses": list(visual_schema.get("allowed_lifecycle_statuses") or ()),
        },
        "missing_evidence": ("runtime_lifecycle_state_machine_not_unified",),
        "blocked_surfaces": [],
        "review_required_surfaces": ("review_required",),
        "contract_only_surfaces": ("visual_skin_asset_registry_persistence",),
        "planned_surfaces": ("future_external_skin_builder_lifecycle_updates",),
        "next_safe_actions": (
            "keep_lifecycle_vocabulary_fixed_until_o1_review_approves_schema_change",
            "use_display_profiles_for_ui_instead_of_frontend_status_guessing",
        ),
    }


def _manifest_reference_evidence(visual_schema: dict[str, Any]) -> dict[str, Any]:
    columns = _column_names(visual_schema)
    required_manifest_fields = ("manifest_path", "skin_asset_id", "source_curated_asset_id", "dataset_uid")
    missing = [field for field in required_manifest_fields if field not in columns]
    return {
        "existing_evidence": {
            "schema_contract": visual_schema.get("table_name"),
            "persistence_status": visual_schema.get("persistence_status"),
            "required_manifest_fields": list(required_manifest_fields),
            "present_manifest_fields": [field for field in required_manifest_fields if field in columns],
            "payload_columns_allowed": bool(
                (visual_schema.get("migration_guards") or {}).get("payload_columns_allowed")
            ),
            "payload_loading": bool((visual_schema.get("safety") or {}).get("payload_loading")),
        },
        "missing_evidence": tuple(missing),
        "blocked_surfaces": [] if not missing else ("manifest_reference_schema_incomplete",),
        "review_required_surfaces": (),
        "contract_only_surfaces": ("visual_skin_asset_registry_table",),
        "planned_surfaces": ("formal_user_database_visual_registry_persistence",),
        "next_safe_actions": (
            "keep_manifest_reference_control_plane_only",
            "do_not_read_npz_or_renderer_payloads_in_core_readiness",
        ),
    }


def _review_required_evidence(
    content_report: dict[str, Any],
    empty_summary: dict[str, Any],
) -> dict[str, Any]:
    content_review_rules = _review_rule_ids(content_report)
    return {
        "existing_evidence": {
            "content_review_rule_count": int(content_report.get("review_rule_count") or 0),
            "content_review_rules": content_review_rules,
            "unknown_fallback_review_bucket": content_report.get("unknown_fallback_review_bucket"),
            "visual_registry_review_required_count": int(empty_summary.get("review_required_count") or 0),
            "visual_review_status_available": "review_required" in SKIN_ASSET_LIFECYCLE_STATUSES,
            "review_item_identity_contract_draft": review_item_identity_contract_draft(),
        },
        "missing_evidence": (
            "review_queue_persistence_not_unified",
            "stable_review_item_identity_not_persisted",
            "review_item_resolution_state_not_defined",
        ),
        "blocked_surfaces": (
            "unsupported_payload_format",
            "treating_display_counts_as_persisted_queue",
            "promoting_review_required_items_to_ready_without_resolution",
        ),
        "review_required_surfaces": tuple(content_review_rules) + ("visual_skin_asset_review_required",),
        "contract_only_surfaces": (
            "visual_review_required_lifecycle_contract",
            "core_review_item_identity_contract_draft",
        ),
        "planned_surfaces": (
            "unified_review_dashboard",
            "review_queue_persistence_schema_after_o1_review",
        ),
        "next_safe_actions": (
            "surface_review_required_from_backend_payloads",
            "do_not_promote_unknown_or_heavy_formats_to_ready_without_parser_evidence",
            "keep_review_item_identity_contract_separate_from_persistence_schema",
        ),
    }


def _job_status_evidence(visual_schema: dict[str, Any], maturity_payload: dict[str, Any]) -> dict[str, Any]:
    rows = maturity_payload.get("rows") if isinstance(maturity_payload.get("rows"), list) else []
    scheduler_row = _maturity_row_by_id(rows, "background_jobs_and_scheduler")
    return {
        "existing_evidence": {
            "visual_lifecycle_statuses": sorted(SKIN_ASSET_LIFECYCLE_STATUSES),
            "auto_event_emission": bool(
                (visual_schema.get("migration_guards") or {}).get("auto_event_emission")
            ),
            "event_writer_contract": (visual_schema.get("migration_guards") or {}).get("event_writer", ""),
            "background_scheduler_maturity": scheduler_row.get("maturity_level", ""),
            "background_scheduler_metrics": scheduler_row.get("metrics", {}),
            "scheduler_job_contract_draft": scheduler_job_contract_draft(),
            "scheduler_queue_ddl_preview": scheduler_queue_sqlite_ddl_preview(),
            "scheduler_owned_test_table_helper": scheduler_queue_owned_test_table_helper_contract(),
            "scheduler_next_action_payload_contract": scheduler_next_action_payload_contract(),
            "scheduler_lifecycle_event_emission_guard": (
                scheduler_lifecycle_event_emission_guard_contract(
                    explicit_event_writer=str(
                        (visual_schema.get("migration_guards") or {}).get("event_writer") or ""
                    ),
                )
            ),
            "scheduler_o1_review_gate_contract": scheduler_o1_review_gate_contract(),
        },
        "missing_evidence": (
            "unified_bounded_job_scheduler_not_yet_implemented",
            "scheduler_contract_not_bound_to_runtime_or_persistence",
            "durable_job_queue_persistence_not_promoted_beyond_owned_test",
            "job_event_status_stream_not_unified",
        ),
        "blocked_surfaces": (
            "auto_lifecycle_event_emission_disabled",
            "future_scheduler_runtime_changes_require_o1_review",
        ),
        "review_required_surfaces": ("failed_lifecycle_status", "review_required_lifecycle_status"),
        "contract_only_surfaces": (
            "visual_ready_event_writer_contract",
            "core_scheduler_job_contract_draft",
            "core_scheduler_queue_persistence_contract",
            "core_scheduler_next_action_payload_contract",
            "core_scheduler_lifecycle_event_emission_guard",
            "core_scheduler_o1_review_gate_contract",
        ),
        "planned_surfaces": (
            "external_builder_job_status_adapter",
            "owned_test_scheduler_poc",
            "bounded_scheduler_runtime_after_o1_review",
        ),
        "next_safe_actions": (
            "keep_auto_event_emission_disabled_until_migration_and_o1_review_are_clear",
            "design_bounded_scheduler_before_async_rewrite",
            "use_scheduler_o1_review_gates_before_runtime_or_persistence_work",
        ),
    }


def _asset_lineage_evidence(visual_schema: dict[str, Any]) -> dict[str, Any]:
    columns = _column_names(visual_schema)
    lineage_fields = ("source_request_id", "source_curated_asset_id", "dataset_uid")
    missing = [field for field in lineage_fields if field not in columns]
    return {
        "existing_evidence": {
            "lineage_fields": list(lineage_fields),
            "present_lineage_fields": [field for field in lineage_fields if field in columns],
            "indexes": list((index.get("name") for index in visual_schema.get("indexes", ())) or ()),
            "control_plane_only": bool((visual_schema.get("safety") or {}).get("control_plane_only")),
        },
        "missing_evidence": tuple(missing),
        "blocked_surfaces": [] if not missing else ("lineage_schema_incomplete",),
        "review_required_surfaces": (),
        "contract_only_surfaces": ("visual_asset_lineage_persistence_schema",),
        "planned_surfaces": ("cross_project_lineage_consumption",),
        "next_safe_actions": (
            "persist_lineage_only_after_explicit_migration_guard",
            "do_not_copy_notional_or_archive_threads_into_product_lineage",
        ),
    }


def _openspec_evidence(openspec_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "existing_evidence": {
            "openspec_inventory": openspec_report,
            "active_spec_count": int(openspec_report.get("active_spec_count") or 0),
            "archived_change_count": int(openspec_report.get("archived_change_count") or 0),
        },
        "missing_evidence": ("openspec_validate_result_not_embedded_in_report",),
        "blocked_surfaces": (),
        "review_required_surfaces": (),
        "contract_only_surfaces": ("openspec_governance_inventory",),
        "planned_surfaces": (),
        "next_safe_actions": (
            "run_openspec_validate_as_explicit_checkpoint_command",
            "keep_openspec_inventory_separate_from_runtime_product_behavior",
        ),
    }


def _review_rule_ids(content_report: dict[str, Any]) -> tuple[str, ...]:
    rules = content_report.get("review_rules") if isinstance(content_report.get("review_rules"), list) else []
    return tuple(
        str(rule.get("rule_id"))
        for rule in rules
        if isinstance(rule, dict) and rule.get("rule_id")
    )


def _column_names(schema: dict[str, Any]) -> set[str]:
    columns = schema.get("columns") if isinstance(schema.get("columns"), list) else []
    return {
        str(column.get("name"))
        for column in columns
        if isinstance(column, dict) and column.get("name")
    }


def _maturity_row_by_id(rows: Iterable[Any], area_id: str) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, dict) and row.get("area_id") == area_id:
            return row
    return {}


__all__ = [
    "build_core_readiness_sections",
]
