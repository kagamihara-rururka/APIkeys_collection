from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from api_launcher.core_json_diagnostics_catalog import (
    CoreJsonDiagnosticSpec,
    iter_core_json_diagnostic_specs,
)


CORE_JSON_DIAGNOSTIC_SWEEP_PLAN_SCHEMA_VERSION = "core_json_diagnostic_sweep_plan.v1"


@dataclass(frozen=True)
class CoreJsonDiagnosticCommandPlan:
    flag: str
    schema_version: str
    evidence_area: str
    status_path: tuple[str, ...]
    launcher_args: tuple[str, ...]
    db_path: str
    db_path_kind: str
    uses_explicit_db: bool
    requires_repository: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "flag": self.flag,
            "schema_version": self.schema_version,
            "evidence_area": self.evidence_area,
            "status_path": list(self.status_path),
            "launcher_args": list(self.launcher_args),
            "db_path": self.db_path,
            "db_path_kind": self.db_path_kind,
            "uses_explicit_db": self.uses_explicit_db,
            "requires_repository": self.requires_repository,
        }


def build_core_json_diagnostic_sweep_plan_report(db_path: str | os.PathLike[str]) -> dict[str, object]:
    """Return a non-executing agent-readable plan for Core JSON sweeps."""

    plans = build_core_json_diagnostic_sweep_plan(db_path)
    db_path_kinds = tuple(sorted({plan.db_path_kind for plan in plans}))
    return {
        "schema_version": CORE_JSON_DIAGNOSTIC_SWEEP_PLAN_SCHEMA_VERSION,
        "status": "planned",
        "scope": "non_executing_command_plan",
        "command_count": len(plans),
        "db_path_kind": db_path_kinds[0] if len(db_path_kinds) == 1 else "mixed",
        "db_path_kinds": list(db_path_kinds),
        "commands": [plan.to_dict() for plan in plans],
        "safety": {
            "executes_commands": False,
            "creates_sqlite": False,
            "changes_product_behavior": False,
            "changes_lifecycle_schema": False,
            "cross_repo_implementation": False,
        },
        "next_safe_actions": (
            "run_planned_commands_only_with_explicit_local_temp_db",
            "treat_cloud_drive_db_path_kind_as_sweep_risk",
        ),
    }


def build_core_json_diagnostic_sweep_plan(
    db_path: str | os.PathLike[str],
    *,
    launcher: str = "APIkeys_collection.py",
    specs: tuple[CoreJsonDiagnosticSpec, ...] | None = None,
) -> tuple[CoreJsonDiagnosticCommandPlan, ...]:
    """Describe how to run Core diagnostics with an explicit SQLite path.

    The helper does not execute commands and does not touch the database. It is
    an evidence/planning surface for agents and tests that need a repeatable
    sweep without accidentally falling back to the cloud-drive default DB.
    """

    normalized_db_path = str(db_path)
    diagnostic_specs = specs if specs is not None else iter_core_json_diagnostic_specs()
    return tuple(
        CoreJsonDiagnosticCommandPlan(
            flag=spec.flag,
            schema_version=spec.schema_version,
            evidence_area=spec.evidence_area,
            status_path=spec.status_path,
            launcher_args=(launcher, "--db", normalized_db_path, spec.flag),
            db_path=normalized_db_path,
            db_path_kind=classify_core_json_sweep_db_path(normalized_db_path),
            uses_explicit_db=True,
            requires_repository=spec.requires_repository,
        )
        for spec in diagnostic_specs
    )


def classify_core_json_sweep_db_path(db_path: str | os.PathLike[str]) -> str:
    raw_path = str(db_path)
    if _looks_like_cloud_drive_path(raw_path):
        return "cloud_drive"

    path = Path(raw_path)
    drive = path.drive.upper()
    if drive in {"L:", "K:"}:
        return "cloud_drive"

    temp_roots = _normalized_temp_roots()
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        resolved = path.absolute()
    normalized = os.path.normcase(str(resolved))
    for temp_root in temp_roots:
        if normalized == temp_root or normalized.startswith(temp_root + os.sep):
            return "local_temp"
    return "other"


def _looks_like_cloud_drive_path(raw_path: str) -> bool:
    """Detect Windows cloud-drive paths even when tests run on POSIX.

    `pathlib.Path()` cannot infer a Windows drive from a raw L-drive
    string on Linux, so CI needs a raw string guard before
    platform-native path normalization runs.
    """

    normalized = raw_path.strip().replace("/", "\\").upper()
    return normalized == "L:" or normalized == "K:" or normalized.startswith(("L:\\", "K:\\"))


def _normalized_temp_roots() -> tuple[str, ...]:
    roots = {
        tempfile.gettempdir(),
        os.environ.get("TEMP", ""),
        os.environ.get("TMP", ""),
    }
    normalized: list[str] = []
    for root in roots:
        if not root:
            continue
        try:
            resolved = Path(root).resolve(strict=False)
        except OSError:
            resolved = Path(root).absolute()
        normalized.append(os.path.normcase(str(resolved)))
    return tuple(sorted(set(normalized)))


__all__ = [
    "CORE_JSON_DIAGNOSTIC_SWEEP_PLAN_SCHEMA_VERSION",
    "CoreJsonDiagnosticCommandPlan",
    "build_core_json_diagnostic_sweep_plan",
    "build_core_json_diagnostic_sweep_plan_report",
    "classify_core_json_sweep_db_path",
]
