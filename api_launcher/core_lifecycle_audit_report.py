from __future__ import annotations

from typing import Any

from api_launcher.core_readiness_report import build_core_readiness_report
from api_launcher.visual_asset_contracts import (
    SKIN_ASSET_LIFECYCLE_STATUSES,
    SkinAssetLifecycleStatus,
    skin_asset_status_display_profile,
    visual_asset_registry_persistence_schema,
)


CORE_LIFECYCLE_AUDIT_REPORT_SCHEMA_VERSION = "core_lifecycle_audit_report.v1"


def build_core_lifecycle_audit_report(repository: Any | None = None) -> dict[str, Any]:
    """Audit Core lifecycle evidence without defining a runtime state machine.

    RRKAL Core currently has stable lifecycle vocabulary, display profiles, and
    ready-event guards. This report makes that explicit while keeping the
    missing runtime transition layer visible. It must not add statuses, change
    schemas, or authorize automatic lifecycle transitions.
    """

    visual_schema = visual_asset_registry_persistence_schema()
    readiness_report = build_core_readiness_report(repository)
    lifecycle_evidence = readiness_report["lifecycle_evidence"]

    return {
        "schema_version": CORE_LIFECYCLE_AUDIT_REPORT_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "lifecycle_vocabulary": _lifecycle_vocabulary(visual_schema),
            "status_classification": _status_classification(),
            "contract_edges": _contract_edges(),
            "readiness_report_bridge": {
                "schema_version": readiness_report["schema_version"],
                "gate_status": readiness_report["integration_planning_gate"]["status"],
                "lifecycle_missing_evidence": list(
                    lifecycle_evidence.get("missing_evidence") or ()
                ),
                "lifecycle_contract_only_surfaces": list(
                    lifecycle_evidence.get("contract_only_surfaces") or ()
                ),
            },
        },
        "missing_evidence": (
            "runtime_lifecycle_state_machine_not_unified",
            "transition_rule_persistence_not_defined",
        ),
        "blocked_surfaces": (
            "automatic_lifecycle_transition_execution_disabled",
            "ready_event_factory_rejects_non_ready_registry_entry",
        ),
        "review_required_surfaces": _review_required_statuses(),
        "contract_only_surfaces": (
            "visual_skin_asset_lifecycle_display_profile",
            "visual_ready_event_factory_guard",
        ),
        "planned_surfaces": (
            "runtime_transition_audit",
            "external_builder_lifecycle_updates",
        ),
        "next_safe_actions": (
            "draft_transition_policy_without_adding_statuses",
            "keep_ui_consuming_display_profiles_not_raw_status_guessing",
            "request_o1_review_before_runtime_transition_or_schema_changes",
        ),
        "o1_review_triggers": (
            "new_or_renamed_lifecycle_status",
            "lifecycle_transition_runtime",
            "lifecycle_transition_persistence",
            "automatic_ready_event_emission",
            "cross_repo_builder_lifecycle_adapter",
        ),
        "safety": {
            "control_plane_only": True,
            "changes_lifecycle_statuses": False,
            "changes_lifecycle_schema": False,
            "implements_runtime_state_machine": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def _lifecycle_vocabulary(visual_schema: dict[str, Any]) -> dict[str, Any]:
    statuses = tuple(sorted(SKIN_ASSET_LIFECYCLE_STATUSES))
    return {
        "status_count": len(statuses),
        "statuses": list(statuses),
        "enum_class": "SkinAssetLifecycleStatus",
        "schema_allowed_lifecycle_statuses": list(
            visual_schema.get("allowed_lifecycle_statuses") or ()
        ),
        "schema_matches_runtime_vocabulary": statuses
        == tuple(visual_schema.get("allowed_lifecycle_statuses") or ()),
    }


def _status_classification() -> dict[str, Any]:
    statuses = tuple(sorted(SKIN_ASSET_LIFECYCLE_STATUSES))
    profiles = {
        status: skin_asset_status_display_profile(status)
        for status in statuses
    }
    return {
        "display_profiles": profiles,
        "ready_statuses": _profile_statuses(profiles, "is_ready"),
        "terminal_statuses": _profile_statuses(profiles, "is_terminal"),
        "review_required_statuses": _profile_statuses(profiles, "review_required"),
        "construction_statuses": _profile_statuses(profiles, "construction"),
    }


def _contract_edges() -> dict[str, Any]:
    return {
        "build_request_to_build_result": {
            "contract": "SkinBuildRequest -> SkinBuildResult",
            "runtime_transition": False,
            "notes": "Build result records status evidence; it does not execute a state transition.",
        },
        "ready_registry_entry_to_ready_event": {
            "contract": "visual_asset_ready_event_from_registry_entry",
            "requires_status": SkinAssetLifecycleStatus.READY.value,
            "rejects_non_ready": True,
            "runtime_transition": False,
        },
        "registry_entry_status": {
            "contract": "RendererSkinAssetRegistryEntry.status",
            "source": "RendererSkinAssetReference.lifecycle_status",
            "runtime_transition": False,
        },
    }


def _review_required_statuses() -> tuple[str, ...]:
    statuses = _profile_statuses(
        {
            status: skin_asset_status_display_profile(status)
            for status in sorted(SKIN_ASSET_LIFECYCLE_STATUSES)
        },
        "review_required",
    )
    return tuple(statuses) + ("unknown_lifecycle_status",)


def _profile_statuses(profiles: dict[str, dict[str, Any]], flag: str) -> list[str]:
    return [
        status
        for status, profile in profiles.items()
        if bool(profile.get(flag))
    ]


__all__ = [
    "CORE_LIFECYCLE_AUDIT_REPORT_SCHEMA_VERSION",
    "build_core_lifecycle_audit_report",
]
