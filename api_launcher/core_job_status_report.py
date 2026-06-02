from __future__ import annotations

from typing import Any

from api_launcher.core_readiness_report import build_core_readiness_report
from api_launcher.project_maturity import build_project_maturity_payload
from api_launcher.visual_asset_contracts import (
    SKIN_ASSET_LIFECYCLE_STATUSES,
    skin_asset_status_display_profile,
    visual_asset_registry_persistence_schema,
)


CORE_JOB_STATUS_REPORT_SCHEMA_VERSION = "core_job_status_report.v1"


def build_core_job_status_report(repository: Any | None = None) -> dict[str, Any]:
    """Summarize Core-owned job-status evidence without introducing a scheduler.

    This diagnostic separates the evidence RRKAL Core already has from the
    operational scheduler work that is still missing. It must stay conservative:
    Tk single-flight policies and visual lifecycle contracts are useful
    evidence, but they are not a unified background-job scheduler and they do
    not authorize downstream renderer/compressor integration.
    """

    visual_schema = visual_asset_registry_persistence_schema()
    readiness_report = build_core_readiness_report(repository)
    readiness_job_status = readiness_report["job_status_evidence"]
    maturity_payload = build_project_maturity_payload(repository) if repository is not None else {}
    scheduler_row = _maturity_row_by_id(maturity_payload, "background_jobs_and_scheduler")
    scheduler_metrics = _dict_or_empty(scheduler_row.get("metrics"))

    return {
        "schema_version": CORE_JOB_STATUS_REPORT_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "visual_lifecycle": _visual_lifecycle_evidence(visual_schema),
            "background_job_policy": _background_job_policy_evidence(scheduler_row, scheduler_metrics),
            "readiness_report_bridge": {
                "schema_version": readiness_report["schema_version"],
                "gate_status": readiness_report["integration_planning_gate"]["status"],
                "job_status_missing_evidence": list(
                    readiness_job_status.get("missing_evidence") or ()
                ),
                "job_status_blocked_surfaces": list(
                    readiness_job_status.get("blocked_surfaces") or ()
                ),
            },
        },
        "missing_evidence": tuple(readiness_job_status.get("missing_evidence") or ()),
        "blocked_surfaces": tuple(readiness_job_status.get("blocked_surfaces") or ()),
        "review_required_surfaces": tuple(
            readiness_job_status.get("review_required_surfaces") or ()
        ),
        "contract_only_surfaces": tuple(
            readiness_job_status.get("contract_only_surfaces") or ()
        ),
        "planned_surfaces": tuple(readiness_job_status.get("planned_surfaces") or ()),
        "next_safe_actions": (
            "design_bounded_scheduler_before_async_rewrite",
            "keep_auto_event_emission_disabled_until_migration_and_o1_review_are_clear",
            "treat_tk_background_policy_registry_as_hardening_evidence_not_full_scheduler",
        ),
        "o1_review_triggers": (
            "unified_scheduler_schema_or_persistence",
            "automatic_lifecycle_event_emission",
            "new_or_renamed_lifecycle_status",
            "cross_repo_builder_job_adapter",
            "renderer_or_compressor_job_status_integration",
        ),
        "safety": {
            "control_plane_only": True,
            "changes_scheduler_schema": False,
            "changes_lifecycle_schema": False,
            "changes_lifecycle_statuses": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def _visual_lifecycle_evidence(visual_schema: dict[str, Any]) -> dict[str, Any]:
    migration_guards = _dict_or_empty(visual_schema.get("migration_guards"))
    statuses = tuple(sorted(SKIN_ASSET_LIFECYCLE_STATUSES))
    return {
        "statuses": list(statuses),
        "status_display_profiles": {
            status: skin_asset_status_display_profile(status)
            for status in statuses
        },
        "auto_event_emission": bool(migration_guards.get("auto_event_emission")),
        "event_writer_contract": str(migration_guards.get("event_writer") or ""),
        "persistence_status": str(visual_schema.get("persistence_status") or ""),
        "table_name": str(visual_schema.get("table_name") or ""),
    }


def _background_job_policy_evidence(
    scheduler_row: dict[str, Any],
    scheduler_metrics: dict[str, Any],
) -> dict[str, Any]:
    max_active_jobs = _dict_or_empty(scheduler_metrics.get("max_active_jobs_by_policy"))
    sqlite_write_gate = _dict_or_empty(scheduler_metrics.get("sqlite_write_gate"))
    guard_tests = tuple(str(item) for item in scheduler_metrics.get("guard_tests") or ())
    return {
        "maturity_level": str(scheduler_row.get("maturity_level") or ""),
        "maturity_label_zh_TW": str(scheduler_row.get("maturity_label_zh_TW") or ""),
        "policy_registry_available": bool(
            scheduler_metrics.get("policy_registry_available")
        ),
        "bounded_tk_policy_count": int(
            scheduler_metrics.get("bounded_tk_policy_count") or 0
        ),
        "max_active_jobs_by_policy": {
            str(policy_id): int(max_jobs)
            for policy_id, max_jobs in max_active_jobs.items()
        },
        "single_flight_start_result_contract": str(
            scheduler_metrics.get("single_flight_start_result_contract") or ""
        ),
        "single_flight_start_outcomes": list(
            scheduler_metrics.get("single_flight_start_outcomes") or ()
        ),
        "sqlite_write_gate": sqlite_write_gate,
        "guard_tests": list(guard_tests),
        "capacity_policy_call_site_guarded": bool(
            scheduler_metrics.get("capacity_policy_call_site_guarded")
        ),
        "direct_thread_spawn_guarded": bool(
            scheduler_metrics.get("direct_thread_spawn_guarded")
        ),
        "direct_thread_spawn_owner": str(
            scheduler_metrics.get("direct_thread_spawn_owner") or ""
        ),
    }


def _maturity_row_by_id(payload: dict[str, Any], area_id: str) -> dict[str, Any]:
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    for row in rows:
        if isinstance(row, dict) and row.get("area_id") == area_id:
            return row
    return {}


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


__all__ = [
    "CORE_JOB_STATUS_REPORT_SCHEMA_VERSION",
    "build_core_job_status_report",
]
