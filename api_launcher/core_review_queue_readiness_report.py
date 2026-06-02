from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api_launcher.content_registry import content_registry_report
from api_launcher.core_review_required_report import build_core_review_required_report
from api_launcher.crawler_asset_review_display import (
    CONTENT_IMPORT_STATUS_DISPLAY,
    CONTENT_PIPELINE_LANE_DISPLAY,
    CONTENT_REVIEW_BUCKET_DISPLAY,
)
from api_launcher.crawler_plan_outcome_display import PLAN_OUTCOME_DISPLAY


CORE_REVIEW_QUEUE_READINESS_REPORT_SCHEMA_VERSION = "core_review_queue_readiness_report.v1"


@dataclass(frozen=True)
class ReviewQueueItemContractField:
    """One draft field for a future review queue item.

    This is not a database schema and it does not define resolution statuses.
    It only gives Core a stable item identity shape so review-required evidence
    can be discussed without treating display counters as durable queue rows.
    """

    field_id: str
    category: str
    required: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "category": self.category,
            "required": self.required,
            "description": self.description,
        }


def build_core_review_queue_readiness_report(repository: Any | None = None) -> dict[str, Any]:
    """Report whether Core can persist review-required work as a queue.

    This is evidence aggregation only.  RRKAL already has several review
    surfaces, but a unified queue needs a stable item contract, persistence
    schema, lifecycle/resolution policy, and migration guard.  Keep this report
    conservative so Core does not treat display counters or temporary review
    hints as a durable review queue.
    """

    review_report = build_core_review_required_report(repository)
    content_report = content_registry_report()
    content_rules = tuple(content_report.get("review_rules") or ())

    return {
        "schema_version": CORE_REVIEW_QUEUE_READINESS_REPORT_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "review_required_report": {
                "schema_version": review_report["schema_version"],
                "status": review_report["status"],
                "missing_evidence": list(review_report.get("missing_evidence") or ()),
                "review_required_surface_count": len(
                    review_report.get("review_required_surfaces") or ()
                ),
                "blocked_surface_count": len(review_report.get("blocked_surfaces") or ()),
            },
            "content_review_rules": {
                "rule_count": int(content_report.get("review_rule_count") or 0),
                "rule_ids": [str(rule.get("rule_id") or "") for rule in content_rules],
                "review_buckets": sorted(
                    {
                        str(rule.get("review_bucket") or "")
                        for rule in content_rules
                        if rule.get("review_bucket")
                    }
                ),
            },
            "display_payloads": {
                "plan_outcome_review_buckets": _display_keys_with_review_tone(
                    PLAN_OUTCOME_DISPLAY
                ),
                "content_review_bucket_count": len(CONTENT_REVIEW_BUCKET_DISPLAY),
                "content_import_status_count": len(CONTENT_IMPORT_STATUS_DISPLAY),
                "content_pipeline_lane_count": len(CONTENT_PIPELINE_LANE_DISPLAY),
                "role": (
                    "Display payloads make review work visible to Tk/Web/Qt, "
                    "but they are not durable queue persistence."
                ),
            },
            "volatile_review_surfaces": (
                "adapter_review_payload_summary",
                "plan_outcome_review_required_count",
                "event_context_review_queue_count",
                "visual_skin_asset_review_required_status",
            ),
            "review_item_identity_contract_draft": review_item_identity_contract_draft(),
        },
        "missing_evidence": (
            "review_queue_persistence_schema_not_defined",
            "stable_review_item_identity_not_persisted",
            "review_item_resolution_state_not_defined",
            "review_queue_migration_or_rollback_guard_not_defined",
            "review_queue_repository_read_write_not_defined",
        ),
        "blocked_surfaces": (
            "treating_display_counts_as_persisted_queue",
            "promoting_review_required_items_to_ready_without_resolution",
            "cross_repo_review_contract_without_o1_review",
        ),
        "review_required_surfaces": tuple(review_report.get("review_required_surfaces") or ()),
        "contract_only_surfaces": (
            "review_queue_persistence_readiness",
            "review_item_contract_draft",
            "review_resolution_policy_draft",
        ),
        "planned_surfaces": (
            "review_queue_openspec",
            "owned_test_database_review_queue_poc",
            "review_queue_summary_cli_json",
        ),
        "next_safe_actions": (
            "draft_review_queue_openspec_before_schema_or_db_writes",
            "define_review_item_identity_and_resolution_fields",
            "prototype_only_in_owned_test_database_after_o1_review",
        ),
        "o1_review_triggers": (
            "review_queue_schema_or_persistence",
            "review_item_lifecycle_or_resolution_statuses",
            "cross_repo_review_contract",
            "promotion_from_review_required_to_ready",
        ),
        "safety": {
            "control_plane_only": True,
            "adds_review_queue_schema": False,
            "writes_review_queue_records": False,
            "changes_lifecycle_schema": False,
            "promotes_review_required_to_ready": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def review_item_identity_contract_fields() -> tuple[ReviewQueueItemContractField, ...]:
    return (
        ReviewQueueItemContractField(
            "review_item_id",
            "identity",
            True,
            "Stable id derived from source surface, source reference, and review bucket.",
        ),
        ReviewQueueItemContractField(
            "source_surface",
            "identity",
            True,
            "Core surface that produced the review-required item.",
        ),
        ReviewQueueItemContractField(
            "source_reference",
            "identity",
            True,
            "Stable reference inside the source surface, such as plan id, resource url, or registry id.",
        ),
        ReviewQueueItemContractField(
            "review_bucket",
            "classification",
            True,
            "Backend-defined review bucket; UI must not infer it from display text.",
        ),
        ReviewQueueItemContractField(
            "payload_format_hint",
            "classification",
            False,
            "Optional content format hint that explains why review is needed.",
        ),
        ReviewQueueItemContractField(
            "evidence_url",
            "audit",
            False,
            "Source or artifact URL/path that supports the review decision.",
        ),
        ReviewQueueItemContractField(
            "warning_codes",
            "audit",
            False,
            "Machine-readable warning codes carried from crawler, resolver, downloader, or importer.",
        ),
        ReviewQueueItemContractField(
            "next_action",
            "display",
            True,
            "Backend-defined next safe action for Tk/Web/future Qt rendering.",
        ),
    )


def review_item_identity_contract_draft() -> dict[str, Any]:
    fields = review_item_identity_contract_fields()
    return {
        "schema_version": "core_review_item_identity_contract_draft.v1",
        "status": "contract_only",
        "scope": "stable_identity_shape_only",
        "field_count": len(fields),
        "fields": [field.to_dict() for field in fields],
        "identity_fields": [
            field.field_id
            for field in fields
            if field.category == "identity"
        ],
        "safety": {
            "adds_review_queue_schema": False,
            "writes_review_queue_records": False,
            "defines_review_resolution_statuses": False,
            "changes_lifecycle_schema": False,
            "promotes_review_required_to_ready": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def _display_keys_with_review_tone(display_map: dict[str, dict[str, object]]) -> list[str]:
    return sorted(
        key
        for key, payload in display_map.items()
        if isinstance(payload, dict) and str(payload.get("display_tone") or "") == "review"
    )


__all__ = [
    "CORE_REVIEW_QUEUE_READINESS_REPORT_SCHEMA_VERSION",
    "build_core_review_queue_readiness_report",
    "review_item_identity_contract_draft",
    "review_item_identity_contract_fields",
]
