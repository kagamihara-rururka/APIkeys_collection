from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CoreJsonDiagnosticSpec:
    """Static metadata for an existing Core diagnostic JSON CLI entrypoint."""

    flag: str
    argparse_attr: str
    schema_version: str
    evidence_area: str
    status_path: tuple[str, ...] = ("status",)
    requires_repository: bool = True


CORE_JSON_DIAGNOSTICS: tuple[CoreJsonDiagnosticSpec, ...] = (
    CoreJsonDiagnosticSpec(
        flag="--core-readiness-report-json",
        argparse_attr="core_readiness_report_json",
        schema_version="core_readiness_report.v1",
        evidence_area="registry_lifecycle_manifest_review_job_lineage",
        status_path=("integration_planning_gate", "status"),
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-review-required-report-json",
        argparse_attr="core_review_required_report_json",
        schema_version="core_review_required_report.v1",
        evidence_area="review_required",
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-review-queue-readiness-json",
        argparse_attr="core_review_queue_readiness_json",
        schema_version="core_review_queue_readiness_report.v1",
        evidence_area="review_queue_readiness",
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-job-status-report-json",
        argparse_attr="core_job_status_report_json",
        schema_version="core_job_status_report.v1",
        evidence_area="job_status",
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-manifest-reference-report-json",
        argparse_attr="core_manifest_reference_report_json",
        schema_version="core_manifest_reference_report.v1",
        evidence_area="manifest_reference",
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-lifecycle-audit-json",
        argparse_attr="core_lifecycle_audit_json",
        schema_version="core_lifecycle_audit_report.v1",
        evidence_area="lifecycle_audit",
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-deep-adapter-coverage-json",
        argparse_attr="core_deep_adapter_coverage_json",
        schema_version="core_deep_adapter_coverage_report.v1",
        evidence_area="deep_adapter_coverage",
        requires_repository=False,
    ),
    CoreJsonDiagnosticSpec(
        flag="--core-bounded-scheduler-plan-json",
        argparse_attr="core_bounded_scheduler_plan_json",
        schema_version="core_bounded_scheduler_plan_report.v1",
        evidence_area="bounded_scheduler_plan",
    ),
)


def iter_core_json_diagnostic_specs() -> tuple[CoreJsonDiagnosticSpec, ...]:
    return CORE_JSON_DIAGNOSTICS


def core_json_diagnostic_flags() -> tuple[str, ...]:
    return tuple(spec.flag for spec in CORE_JSON_DIAGNOSTICS)


def core_json_diagnostic_specs_by_flag() -> dict[str, CoreJsonDiagnosticSpec]:
    return {spec.flag: spec for spec in CORE_JSON_DIAGNOSTICS}


def core_json_diagnostic_schema_versions() -> dict[str, str]:
    return {spec.flag: spec.schema_version for spec in CORE_JSON_DIAGNOSTICS}


def status_from_payload(spec: CoreJsonDiagnosticSpec, payload: dict[str, Any]) -> str:
    current: Any = payload
    for key in spec.status_path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return str(current or "")


__all__ = [
    "CORE_JSON_DIAGNOSTICS",
    "CoreJsonDiagnosticSpec",
    "core_json_diagnostic_flags",
    "core_json_diagnostic_schema_versions",
    "core_json_diagnostic_specs_by_flag",
    "iter_core_json_diagnostic_specs",
    "status_from_payload",
]
