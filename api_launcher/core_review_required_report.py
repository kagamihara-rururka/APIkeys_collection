from __future__ import annotations

from typing import Any

from api_launcher.content_registry import content_registry_report
from api_launcher.core_readiness_report import build_core_readiness_report
from api_launcher.visual_asset_contracts import (
    SKIN_ASSET_LIFECYCLE_STATUSES,
    skin_asset_status_display_profile,
    visual_asset_registry_summary,
)


CORE_REVIEW_REQUIRED_REPORT_SCHEMA_VERSION = "core_review_required_report.v1"


def build_core_review_required_report(repository: Any | None = None) -> dict[str, Any]:
    """Summarize Core-owned review-required evidence without creating a queue schema.

    This report is a planning diagnostic. It explains which payload/content
    surfaces RRKAL Core can already route into review and which evidence is
    still missing before a unified review queue or downstream integration can
    be planned.
    """

    content_report = content_registry_report()
    readiness_report = build_core_readiness_report(repository)
    readiness_review = readiness_report["review_required_evidence"]
    visual_summary = visual_asset_registry_summary(())
    content_rules = tuple(content_report.get("review_rules") or ())

    return {
        "schema_version": CORE_REVIEW_REQUIRED_REPORT_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "content_review_rule_count": int(content_report.get("review_rule_count") or 0),
            "content_review_rules": [_content_rule_summary(rule) for rule in content_rules],
            "unknown_fallback": {
                "parser_id": content_report.get("unknown_fallback_parser_id", ""),
                "review_bucket": content_report.get("unknown_fallback_review_bucket", ""),
                "blocked_surface": "unsupported_payload_format",
            },
            "visual_review_required": {
                "status_available": "review_required" in SKIN_ASSET_LIFECYCLE_STATUSES,
                "display_profile": skin_asset_status_display_profile("review_required"),
                "empty_registry_review_required_count": int(
                    visual_summary.get("review_required_count") or 0
                ),
            },
            "readiness_report_bridge": {
                "schema_version": readiness_report["schema_version"],
                "gate_status": readiness_report["integration_planning_gate"]["status"],
                "review_required_surfaces": list(
                    readiness_review.get("review_required_surfaces") or ()
                ),
                "blocked_surfaces": list(readiness_review.get("blocked_surfaces") or ()),
            },
        },
        "missing_evidence": tuple(readiness_review.get("missing_evidence") or ()),
        "blocked_surfaces": tuple(readiness_review.get("blocked_surfaces") or ()),
        "review_required_surfaces": tuple(readiness_review.get("review_required_surfaces") or ()),
        "contract_only_surfaces": tuple(readiness_review.get("contract_only_surfaces") or ()),
        "planned_surfaces": tuple(readiness_review.get("planned_surfaces") or ()),
        "next_safe_actions": (
            "keep_unknown_and_heavy_payloads_in_review_until_parser_or_adapter_evidence_exists",
            "add_review_queue_persistence_only_after_schema_and_o1_review_are_clear",
            "surface_review_required_from_backend_payloads_not_frontend_guessing",
        ),
        "o1_review_triggers": (
            "review_queue_schema_or_persistence",
            "new_or_renamed_review_lifecycle_status",
            "cross_repo_review_contract",
            "promotion_from_review_required_to_ready",
        ),
        "safety": {
            "control_plane_only": True,
            "changes_review_queue_schema": False,
            "changes_lifecycle_schema": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def _content_rule_summary(rule: Any) -> dict[str, Any]:
    formats = tuple(rule.get("formats") or ())
    return {
        "rule_id": str(rule.get("rule_id") or ""),
        "content_family": str(rule.get("content_family") or ""),
        "review_bucket": str(rule.get("review_bucket") or ""),
        "parser_id": str(rule.get("parser_id") or ""),
        "format_count": len(formats),
        "sample_formats": list(formats[:8]),
    }


__all__ = [
    "CORE_REVIEW_REQUIRED_REPORT_SCHEMA_VERSION",
    "build_core_review_required_report",
]
