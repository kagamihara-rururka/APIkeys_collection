from __future__ import annotations

from typing import Any

from api_launcher.core_job_status_report import build_core_job_status_report
from api_launcher.core_scheduler_contracts import (
    scheduler_lifecycle_event_emission_guard_contract,
    scheduler_job_contract_draft,
    scheduler_job_contract_fields,
    scheduler_next_action_payload_contract,
    scheduler_o1_review_gate_contract,
)
from api_launcher.core_scheduler_persistence_contract import (
    scheduler_queue_owned_test_table_helper_contract,
    scheduler_queue_sqlite_ddl_preview,
)
from api_launcher.sqlite_write_gate import sqlite_write_gate_profile
from api_launcher.visual_asset_contracts import visual_asset_registry_persistence_schema
from frontends.tk.background_job_policies import iter_tk_background_job_policies


CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION = "core_bounded_scheduler_plan_report.v1"


def build_core_bounded_scheduler_plan_report(
    repository: Any | None = None,
) -> dict[str, Any]:
    """Plan the next bounded scheduler slice without implementing a scheduler.

    RRKAL already has Tk capacity policies and a process-local SQLite write
    gate. This report keeps those hardening layers visible while making the
    missing runtime scheduler work explicit. It must not create queues, change
    lifecycle states, enable automatic events, or import downstream renderer or
    compressor projects.
    """

    job_status_report = build_core_job_status_report(repository)
    tk_lanes = _tk_scheduler_lane_candidates()
    sqlite_gate = sqlite_write_gate_profile().to_dict()
    lane_contract_coverage = _scheduler_lane_contract_coverage(tk_lanes)
    visual_registry_schema = visual_asset_registry_persistence_schema()
    explicit_event_writer = str(
        visual_registry_schema.get("migration_guards", {}).get("event_writer") or ""
    )

    return {
        "schema_version": CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "job_status_report_bridge": _job_status_report_bridge(job_status_report),
            "scheduler_job_contract_draft": scheduler_job_contract_draft(),
            "scheduler_next_action_payload_contract": scheduler_next_action_payload_contract(),
            "scheduler_lifecycle_event_emission_guard": (
                scheduler_lifecycle_event_emission_guard_contract(
                    explicit_event_writer=explicit_event_writer,
                )
            ),
            "scheduler_o1_review_gate_contract": scheduler_o1_review_gate_contract(),
            "scheduler_queue_ddl_preview": scheduler_queue_sqlite_ddl_preview(),
            "scheduler_owned_test_table_helper": scheduler_queue_owned_test_table_helper_contract(),
            "tk_policy_registry": {
                "policy_count": len(tk_lanes),
                "lanes": tk_lanes,
            },
            "scheduler_lane_contract_coverage": lane_contract_coverage,
            "single_flight_contract": {
                "contract": "TkBackgroundJobStartResult",
                "outcomes": ("started", "duplicate", "capacity"),
                "owner": "frontends.tk.background_jobs",
            },
            "sqlite_write_gate": sqlite_gate,
        },
        "missing_evidence": (
            "scheduler_contract_not_bound_to_runtime_or_persistence",
            "durable_job_queue_persistence_not_promoted_beyond_owned_test",
            "cross_process_sqlite_write_coordination_not_defined",
            "cancellation_retry_and_timeout_policy_not_unified",
            "job_event_status_stream_not_unified",
            "lifecycle_event_emission_policy_not_authorized",
        ),
        "blocked_surfaces": (
            "treating_tk_thread_policy_registry_as_full_scheduler",
            "treating_process_local_sqlite_gate_as_cross_process_lock",
            "enabling_auto_lifecycle_events_without_o1_review",
            "adopting_asyncio_runtime_rewrite_without_openspec",
        ),
        "contract_only_surfaces": (
            "tk_background_job_policy_registry",
            "TkBackgroundJobStartResult",
            "SQLiteWriteGateProfile",
            "core_job_status_report.v1",
        ),
        "planned_surfaces": (
            "bounded_scheduler_openspec",
            "scheduler_state_contract",
            "job_event_summary_cli_json",
            "owned_test_scheduler_poc",
        ),
        "scheduler_plan": {
            "first_poc_scope": (
                "owned_test_scheduler_contract_only",
                "sqlite_import_lane",
                "crawler_asset_lane",
            ),
            "design_principles": (
                "bounded_queue_not_unbounded_threads",
                "declarative_lane_policy",
                "single_writer_gate_for_sqlite_paths",
                "structured_status_payload_for_ui",
                "no_auto_lifecycle_event_until_o1_review",
            ),
            "not_in_scope": (
                "full_asyncio_rewrite",
                "cross_process_scheduler_lock",
                "renderer_or_compressor_job_adapter",
                "lifecycle_schema_or_status_change",
                "automatic_visual_asset_ready_event",
            ),
        },
        "integration_planning_gate": {
            "status": "partial",
            "ready_for_scheduler_runtime_poc": False,
            "reason": (
                "Existing Tk lane caps and SQLite write gate are hardening "
                "evidence, but RRKAL still lacks a unified scheduler contract, "
                "durable queue state, cancellation/retry policy, and cross-process "
                "write coordination."
            ),
        },
        "next_safe_actions": (
            "write_bounded_scheduler_openspec_before_runtime_code",
            "define_scheduler_lane_contract_without_changing_lifecycle_schema",
            "prototype_owned_test_scheduler_status_json_before_ui_integration",
        ),
        "o1_review_triggers": (
            "new_scheduler_schema_or_persistence",
            "automatic_lifecycle_event_emission",
            "cross_process_or_cross_repo_scheduler_contract",
            "renderer_or_compressor_job_adapter",
            "asyncio_runtime_migration",
        ),
        "safety": {
            "control_plane_only": True,
            "implements_scheduler_runtime": False,
            "changes_scheduler_schema": False,
            "changes_lifecycle_schema": False,
            "changes_lifecycle_statuses": False,
            "enables_auto_lifecycle_events": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def _tk_scheduler_lane_candidates() -> tuple[dict[str, Any], ...]:
    lanes: list[dict[str, Any]] = []
    for policy in iter_tk_background_job_policies():
        lanes.append(
            {
                "policy_id": policy.policy_id,
                "max_active_jobs": policy.max_active_jobs,
                "active_jobs_attr": policy.active_jobs_attr,
                "active_jobs_lock_attr": policy.active_jobs_lock_attr,
                "description": policy.description,
                "current_scope": "tk_ui_instance",
            }
        )
    return tuple(lanes)


def _job_status_report_bridge(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": str(report.get("schema_version") or ""),
        "status": str(report.get("status") or ""),
        "missing_evidence": list(report.get("missing_evidence") or ()),
        "blocked_surfaces": list(report.get("blocked_surfaces") or ()),
        "safety": dict(report.get("safety") or {}),
    }


def _scheduler_lane_contract_coverage(tk_lanes: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Compare current Tk worker caps with the future scheduler policy contract.

    This is intentionally conservative.  The Tk policy registry only proves a
    UI-instance concurrency cap today; it does not prove timeout, retry,
    cancellation, or review-required handling.  The SQLite import lane gets a
    narrow write-policy credit because RRKAL also exposes the process-local
    SQLite write gate in this same report.
    """

    required_facets = tuple(
        field.field_id
        for field in scheduler_job_contract_fields()
        if field.category == "policy"
    )
    lane_reports: list[dict[str, Any]] = []
    covered_anywhere: set[str] = set()

    for lane in tk_lanes:
        covered = _covered_scheduler_contract_facets_for_tk_lane(lane)
        covered_anywhere.update(covered)
        missing = tuple(facet for facet in required_facets if facet not in covered)
        lane_reports.append(
            {
                "policy_id": lane["policy_id"],
                "current_scope": lane["current_scope"],
                "max_active_jobs": lane["max_active_jobs"],
                "covered_contract_facets": covered,
                "missing_contract_facets": missing,
                "coverage_status": "partial",
                "evidence_source": (
                    "frontends.tk.background_job_policies plus "
                    "api_launcher.sqlite_write_gate"
                ),
                "next_action": "define_scheduler_lane_contract_before_runtime_scheduler",
            }
        )

    return {
        "schema_version": "scheduler_lane_contract_coverage.v1",
        "status": "partial",
        "policy_count": len(tk_lanes),
        "required_policy_facets": required_facets,
        "covered_policy_facets": tuple(
            facet for facet in required_facets if facet in covered_anywhere
        ),
        "missing_policy_facets": tuple(
            facet for facet in required_facets if facet not in covered_anywhere
        ),
        "lanes": tuple(lane_reports),
        "safety": {
            "treats_tk_policy_registry_as_full_scheduler": False,
            "implements_scheduler_runtime": False,
            "changes_scheduler_schema": False,
            "changes_lifecycle_schema": False,
            "enables_auto_lifecycle_events": False,
        },
    }


def _covered_scheduler_contract_facets_for_tk_lane(lane: dict[str, Any]) -> tuple[str, ...]:
    covered = ["concurrency_policy"]
    if lane["policy_id"] == "sqlite_import":
        covered.append("write_policy")
    return tuple(covered)


__all__ = [
    "CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION",
    "build_core_bounded_scheduler_plan_report",
]
