from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA = "assetcard_governance_checkpoint_validator.v1"
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.assetcard_governance_checkpoint import build_assetcard_governance_checkpoint  # noqa: E402


REQUIRED_SCHEMA = "assetcard_governance_checkpoint.v1"
REQUIRED_CORE_SCHEMA = "core_readiness_report.v1"
REQUIRED_CORE_GATE = "partial"

SAFETY_FALSE_FIELDS = (
    "export_query_api_exists",
    "json_fixture_driver_exists",
    "cross_repo_integration",
    "payload_exposure",
    "private_path_exposure",
    "odoriba_consumption_claim",
)


def validate_checkpoint_payload(payload: dict[str, Any]) -> list[str]:
    """Return validation errors for a checkpoint payload.

    The validator is intentionally stricter than the wrapper display contract:
    any false-safety flag flipping to true, missing governance docs, or gate
    change away from partial blocks the checkpoint.
    """

    errors: list[str] = []
    if payload.get("schema") != REQUIRED_SCHEMA:
        errors.append("schema_mismatch")
    if payload.get("status") != "passed":
        errors.append("status_not_passed")
    if payload.get("core_readiness_schema") != REQUIRED_CORE_SCHEMA:
        errors.append("core_readiness_schema_mismatch")
    if payload.get("core_gate_status") != REQUIRED_CORE_GATE:
        errors.append("core_gate_status_not_partial")
    if payload.get("checkpoint_passed") is not True:
        errors.append("checkpoint_not_passed")
    if payload.get("missing_docs") != []:
        errors.append("missing_docs_not_empty")

    for field in SAFETY_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"{field}_not_false")

    return errors


def run_negative_self_test(payload: dict[str, Any]) -> dict[str, Any]:
    """Mutate in-memory payload copies and confirm the validator rejects them."""

    mutations: dict[str, Any] = {
        "export_query_api_exists": True,
        "json_fixture_driver_exists": True,
        "cross_repo_integration": True,
        "payload_exposure": True,
        "private_path_exposure": True,
        "odoriba_consumption_claim": True,
        "core_gate_status": "ready_for_planning",
        "missing_docs": ["docs/MISSING_ASSETCARD_DOC.md"],
    }

    cases: list[dict[str, Any]] = []
    undetected: list[str] = []
    for field, value in mutations.items():
        mutated = copy.deepcopy(payload)
        mutated[field] = value
        errors = validate_checkpoint_payload(mutated)
        detected = bool(errors)
        cases.append({"mutation": field, "detected": detected, "errors": errors})
        if not detected:
            undetected.append(field)

    return {
        "enabled": True,
        "case_count": len(cases),
        "passed": not undetected,
        "undetected_mutations": undetected,
        "cases": cases,
    }


def build_validation_report(*, self_test_negative: bool = False) -> dict[str, Any]:
    payload = build_assetcard_governance_checkpoint(ROOT)
    errors = validate_checkpoint_payload(payload)
    negative = run_negative_self_test(payload) if self_test_negative else {"enabled": False}
    validation_passed = not errors and (not self_test_negative or bool(negative.get("passed")))

    return {
        "schema": SCHEMA,
        "status": "passed" if validation_passed else "failed",
        "validated_checkpoint_schema": payload.get("schema"),
        "core_readiness_schema": payload.get("core_readiness_schema"),
        "core_gate_status": payload.get("core_gate_status"),
        "checkpoint_passed": payload.get("checkpoint_passed"),
        "missing_docs": payload.get("missing_docs"),
        "safety_false_fields": {
            field: payload.get(field) for field in SAFETY_FALSE_FIELDS
        },
        "errors": errors,
        "negative_self_test": negative,
        "boundary": {
            "validator_only": True,
            "exports_assetcards": False,
            "runs_fixture_packets": False,
            "changes_readiness": False,
            "changes_lifecycle_schema": False,
            "imports_downstream_repos": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the local AssetCard governance checkpoint JSON."
    )
    parser.add_argument(
        "--self-test-negative",
        action="store_true",
        help="Mutate in-memory payload copies and verify unsafe states are rejected.",
    )
    args = parser.parse_args(argv)

    report = build_validation_report(self_test_negative=args.self_test_negative)
    json.dump(report, sys.stdout, ensure_ascii=True, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
