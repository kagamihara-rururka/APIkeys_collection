from __future__ import annotations

from typing import Any

from api_launcher.crawler_registry_report import crawler_registry_report
from api_launcher.dataset_adapters import dataset_adapter_report


CORE_DEEP_ADAPTER_COVERAGE_REPORT_SCHEMA_VERSION = "core_deep_adapter_coverage_report.v1"


def build_core_deep_adapter_coverage_report() -> dict[str, Any]:
    """Report the current source-crawler versus deep-adapter coverage gap.

    A source crawler can discover metadata for a protocol family. A deep
    adapter owns a provider-specific download/import path. This diagnostic
    keeps those concepts separate so RRKAL Core does not overstate maturity or
    treat every metadata crawler as a completed adapter.
    """

    crawler_report = crawler_registry_report()
    adapter_report = dataset_adapter_report()
    specs = _crawler_specs(crawler_report)
    adapters = _adapter_entries(adapter_report)
    gap_table = _source_type_gap_table(specs)

    return {
        "schema_version": CORE_DEEP_ADAPTER_COVERAGE_REPORT_SCHEMA_VERSION,
        "status": "partial",
        "existing_evidence": {
            "crawler_registry": _crawler_registry_evidence(crawler_report, specs),
            "deep_adapter_inventory": _deep_adapter_inventory(adapter_report, adapters),
            "coverage_boundary": adapter_report.get("coverage_boundary", ""),
            "source_type_gap_table": gap_table,
            "implemented_adapter_paths": _implemented_adapter_paths(adapters),
        },
        "missing_evidence": (
            "source_type_to_deep_adapter_mapping_not_defined",
            "deep_adapter_coverage_does_not_match_supported_source_types",
            "download_import_closure_matrix_not_ranked",
        ),
        "blocked_surfaces": (
            "claiming_metadata_crawler_as_deep_adapter",
            "cross_repo_renderer_or_compressor_adapter_scope",
        ),
        "review_required_surfaces": (
            "heavy_scientific_payload_needs_adapter_review",
            "non_importable_content_format_needs_adapter_review",
            "terms_or_credentials_need_adapter_review",
        ),
        "contract_only_surfaces": (
            "deep_adapter_coverage_plan",
            "source_type_adapter_need_matrix",
        ),
        "planned_surfaces": (
            "ranked_adapter_backlog",
            "download_import_closure_matrix",
        ),
        "next_safe_actions": (
            "rank_source_types_by_mvp_download_import_closure_value",
            "add_deep_adapters_only_when_they_close_real_download_import_paths",
            "keep_crawler_registry_and_dataset_adapter_inventory_separate",
        ),
        "o1_review_triggers": (
            "cross_project_adapter_contract",
            "renderer_or_compressor_adapter_scope",
            "new_lifecycle_or_lineage_schema_for_adapter_outputs",
            "claiming_integration_readiness_from_adapter_coverage",
        ),
        "safety": {
            "control_plane_only": True,
            "adds_new_adapter": False,
            "changes_crawler_dispatch": False,
            "changes_download_import_behavior": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "cross_repo_implementation": False,
        },
    }


def _crawler_specs(crawler_report: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    specs = crawler_report.get("specs") if isinstance(crawler_report.get("specs"), list) else []
    return tuple(spec for spec in specs if isinstance(spec, dict))


def _adapter_entries(adapter_report: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    entries = (
        adapter_report.get("registered_adapters")
        if isinstance(adapter_report.get("registered_adapters"), list)
        else []
    )
    return tuple(entry for entry in entries if isinstance(entry, dict))


def _crawler_registry_evidence(
    crawler_report: dict[str, Any],
    specs: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    return {
        "source_type_count": int(crawler_report.get("source_type_count") or 0),
        "matrix_cell_count": int(crawler_report.get("matrix_cell_count") or 0),
        "capability_group_count": len(crawler_report.get("capability_groups") or ()),
        "source_types": [str(spec.get("source_type") or "") for spec in specs],
        "dimensions": crawler_report.get("dimensions") or {},
        "registry_role": crawler_report.get("role", ""),
    }


def _deep_adapter_inventory(
    adapter_report: dict[str, Any],
    adapters: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    return {
        "dataset_adapter_count": int(adapter_report.get("dataset_adapter_count") or 0),
        "adapter_ids": list(adapter_report.get("adapter_ids") or ()),
        "provider_ids": list(adapter_report.get("provider_ids") or ()),
        "source_type_scope": adapter_report.get("source_type_scope", ""),
        "registered_adapters": adapters,
        "next_action": adapter_report.get("next_action", ""),
    }


def _source_type_gap_table(specs: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for spec in specs:
        source_type = str(spec.get("source_type") or "")
        table.append(
            {
                "source_type": source_type,
                "source_family": str(spec.get("source_family") or ""),
                "transport": str(spec.get("transport") or ""),
                "auth_profile": str(spec.get("auth_profile") or ""),
                "result_shape": str(spec.get("result_shape") or ""),
                "seed_scope": str(spec.get("seed_scope") or ""),
                "capability_binary": str(spec.get("capability_binary") or ""),
                "deep_adapter_status": "unmapped_to_provider_specific_adapter_inventory",
                "coverage_note": (
                    "This source_type has a metadata crawler handler. It is not "
                    "automatically a provider-specific deep adapter."
                ),
                "next_action": "rank_before_adding_adapter",
            }
        )
    return table


def _implemented_adapter_paths(adapters: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [
        {
            "adapter_id": str(adapter.get("adapter_id") or ""),
            "provider_id": str(adapter.get("provider_id") or ""),
            "adapter_class": str(adapter.get("adapter_class") or ""),
            "module": str(adapter.get("module") or ""),
            "supported_formats": list(adapter.get("supported_formats") or ()),
            "status": str(adapter.get("status") or ""),
            "source_type_handler": False,
        }
        for adapter in adapters
    ]


__all__ = [
    "CORE_DEEP_ADAPTER_COVERAGE_REPORT_SCHEMA_VERSION",
    "build_core_deep_adapter_coverage_report",
]
