from __future__ import annotations

from pathlib import Path
from typing import Any


CORE_OPENSPEC_EVIDENCE_SCHEMA_VERSION = "core_openspec_evidence.v1"


def build_core_openspec_evidence(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Summarize OpenSpec files without running OpenSpec or changing state.

    RRKAL uses OpenSpec as a governance contract layer. This helper is an
    inventory surface only: it checks which spec files are present and which
    archived changes exist, while leaving validation to the explicit
    `openspec validate --all` checkpoint command.
    """

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    specs_dir = root / "openspec" / "specs"
    archive_dir = root / "openspec" / "changes" / "archive"

    active_specs = _active_spec_entries(root, specs_dir)
    archived_changes = _archived_change_entries(root, archive_dir)
    return {
        "schema_version": CORE_OPENSPEC_EVIDENCE_SCHEMA_VERSION,
        "status": "partial" if active_specs else "not_ready",
        "scope": "inventory_only_no_validation_execution",
        "active_spec_count": len(active_specs),
        "active_specs": active_specs,
        "archived_change_count": len(archived_changes),
        "archived_changes": archived_changes,
        "validation": {
            "executed_by_report": False,
            "required_checkpoint_command": "npx.cmd -y @fission-ai/openspec@latest validate --all --no-interactive",
        },
        "safety": {
            "executes_openspec": False,
            "changes_openspec_files": False,
            "changes_product_behavior": False,
            "cross_repo_implementation": False,
        },
    }


def _active_spec_entries(root: Path, specs_dir: Path) -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    if not specs_dir.is_dir():
        return ()
    for spec_dir in sorted(path for path in specs_dir.iterdir() if path.is_dir()):
        spec_path = spec_dir / "spec.md"
        if not spec_path.is_file():
            continue
        entries.append(
            {
                "spec_id": spec_dir.name,
                "spec_path": _relative_posix_path(root, spec_path),
            }
        )
    return tuple(entries)


def _archived_change_entries(root: Path, archive_dir: Path) -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    if not archive_dir.is_dir():
        return ()
    for change_dir in sorted(path for path in archive_dir.iterdir() if path.is_dir()):
        entries.append(
            {
                "change_id": change_dir.name,
                "change_path": _relative_posix_path(root, change_dir),
            }
        )
    return tuple(entries)


def _relative_posix_path(root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return path.as_posix()
    return relative.as_posix()


__all__ = [
    "CORE_OPENSPEC_EVIDENCE_SCHEMA_VERSION",
    "build_core_openspec_evidence",
]
