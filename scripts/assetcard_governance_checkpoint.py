from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SCHEMA = "assetcard_governance_checkpoint.v1"
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_launcher.core_readiness_report import build_core_readiness_report  # noqa: E402


GOVERNANCE_DOCS: dict[str, str] = {
    "reference_boundary_audit": "docs/ASSETCARD_REFERENCE_BOUNDARY_AND_CORE_CONSOLIDATION_AUDIT.zh-TW.md",
    "export_query_adr_draft": "docs/ASSETCARD_EXPORT_QUERY_CONTRACT_ADR_DRAFT.zh-TW.md",
    "preimplementation_gate": "docs/ASSETCARD_EXPORT_QUERY_PREIMPLEMENTATION_GATE.zh-TW.md",
    "touchpoint_negative_test_matrix": "docs/ASSETCARD_EXPORT_QUERY_TOUCHPOINT_NEGATIVE_TEST_MATRIX.zh-TW.md",
    "redaction_fixture_matrix": "docs/ASSETCARD_EXPORT_QUERY_REDACTION_FIXTURE_MATRIX.zh-TW.md",
    "redaction_fixture_packet_design": "docs/ASSETCARD_REDACTION_FIXTURE_PACKET_DESIGN.zh-TW.md",
    "governance_checkpoint_index": "docs/ASSETCARD_GOVERNANCE_CHECKPOINT_INDEX.zh-TW.md",
    "governance_checkpoint_command_design": "docs/ASSETCARD_GOVERNANCE_CHECKPOINT_COMMAND_DESIGN.zh-TW.md",
}

REDACTION_DOC_IDS = {
    "redaction_fixture_matrix",
    "redaction_fixture_packet_design",
}


def build_assetcard_governance_checkpoint(repo_root: Path = ROOT) -> dict[str, Any]:
    """Build a Core-only governance checkpoint without exposing AssetCards.

    This is a local governance wrapper. It aggregates readiness evidence and
    tracked document presence only; it must not export cards, execute fixture
    packets, read payload files, or import downstream renderer/compressor repos.
    """

    readiness = build_core_readiness_report()
    core_schema = str(readiness.get("schema_version", ""))
    gate = readiness.get("integration_planning_gate", {})
    core_gate_status = str(gate.get("status", "unknown")) if isinstance(gate, dict) else "unknown"

    docs = _document_presence(repo_root)
    missing_docs = sorted(doc_id for doc_id, present in docs.items() if not present)
    assetcard_governance_docs_present = not missing_docs
    redaction_docs_present = all(docs.get(doc_id, False) for doc_id in REDACTION_DOC_IDS)

    safety = {
        "export_query_api_exists": False,
        "json_fixture_driver_exists": False,
        "cross_repo_integration": False,
        "payload_exposure": False,
        "private_path_exposure": False,
        "odoriba_consumption_claim": False,
    }
    checkpoint_passed = (
        core_schema == "core_readiness_report.v1"
        and core_gate_status == "partial"
        and assetcard_governance_docs_present
        and redaction_docs_present
        and not any(safety.values())
    )

    return {
        "schema": SCHEMA,
        "status": "passed" if checkpoint_passed else "blocked",
        "core_readiness_schema": core_schema,
        "core_gate_status": core_gate_status,
        "assetcard_governance_docs_present": assetcard_governance_docs_present,
        "redaction_docs_present": redaction_docs_present,
        "docs": {
            doc_id: {
                "path": rel_path,
                "present": docs[doc_id],
            }
            for doc_id, rel_path in GOVERNANCE_DOCS.items()
        },
        "missing_docs": missing_docs,
        **safety,
        "checkpoint_passed": checkpoint_passed,
        "next_safe_actions": (
            "keep_assetcard_governance_docs_current",
            "request_review_before_export_query_or_fixture_driver_implementation",
            "keep_core_readiness_gate_partial_until_evidence_changes",
        ),
        "boundary": {
            "control_plane_only": True,
            "exports_assetcards": False,
            "runs_fixture_packets": False,
            "changes_readiness": False,
            "changes_lifecycle_schema": False,
            "imports_downstream_repos": False,
        },
        "evidence_command": "py -3 -B APIkeys_collection.py --core-readiness-report-json",
    }


def _document_presence(repo_root: Path) -> dict[str, bool]:
    return {doc_id: (repo_root / rel_path).is_file() for doc_id, rel_path in GOVERNANCE_DOCS.items()}


def main() -> int:
    json.dump(build_assetcard_governance_checkpoint(), sys.stdout, ensure_ascii=True, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
