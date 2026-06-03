from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from api_launcher.core_readiness_sections import build_core_readiness_sections


CORE_READINESS_SCHEMA_VERSION = "core_readiness_report.v1"


def build_core_readiness_report(repository: Any | None = None) -> dict[str, Any]:
    """Aggregate RRKAL Core readiness evidence without integrating downstream projects.

    This report is intentionally conservative. It describes the control-plane
    contracts RRKAL already has for registries, lifecycle vocabulary, manifest
    references, review-required lanes, job-status evidence, and lineage. It
    must not import renderer/compressor projects, read renderer payloads, or
    mark future integration as ready while evidence is still contract-only.
    """

    sections = build_core_readiness_sections(repository)
    gate = _integration_planning_gate(sections)
    return {
        "schema_version": CORE_READINESS_SCHEMA_VERSION,
        **sections,
        "integration_planning_gate": gate,
        "safety": {
            "control_plane_only": True,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "changes_lifecycle_schema": False,
            "cross_repo_implementation": False,
        },
    }


def _integration_planning_gate(sections: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = sorted(_flatten_section_items(sections, "missing_evidence"))
    blocked = sorted(_flatten_section_items(sections, "blocked_surfaces"))
    contract_only = sorted(_flatten_section_items(sections, "contract_only_surfaces"))
    planned = sorted(_flatten_section_items(sections, "planned_surfaces"))
    if blocked:
        status = "partial"
    elif missing or contract_only or planned:
        status = "partial"
    else:
        status = "ready_for_planning"
    return {
        "status": status,
        "blocked_reasons": blocked,
        "missing_evidence": missing,
        "contract_only_surfaces": contract_only,
        "planned_surfaces": planned,
        "next_safe_actions": (
            "prepare_integration_planning_gate_evidence_without_downstream_imports",
            "request_o1_review_before_lifecycle_schema_or_cross_project_contract_changes",
            "keep_github_ci_and_smoke_as_product_evidence",
        ),
    }


def _flatten_section_items(sections: dict[str, dict[str, Any]], key: str) -> set[str]:
    values: set[str] = set()
    for section in sections.values():
        raw_items = section.get(key, ())
        if isinstance(raw_items, str):
            values.add(raw_items)
            continue
        if isinstance(raw_items, Iterable):
            values.update(str(item) for item in raw_items if item)
    return values


__all__ = [
    "CORE_READINESS_SCHEMA_VERSION",
    "build_core_readiness_report",
]
