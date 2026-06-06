from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.assetcard_governance_checkpoint import build_assetcard_governance_checkpoint
from scripts.validate_assetcard_governance_checkpoint import (
    SAFETY_FALSE_FIELDS,
    build_validation_report,
    validate_checkpoint_payload,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_assetcard_governance_checkpoint.py"
CHECKPOINT = ROOT / "scripts" / "assetcard_governance_checkpoint.py"


class AssetCardGovernanceCheckpointValidatorTests(unittest.TestCase):
    def test_validator_stdout_is_pure_json_and_validates_checkpoint(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(VALIDATOR)],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
            timeout=60,
        )

        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("assetcard_governance_checkpoint_validator.v1", payload["schema"])
        self.assertEqual("passed", payload["status"])
        self.assertEqual("assetcard_governance_checkpoint.v1", payload["validated_checkpoint_schema"])
        self.assertEqual("core_readiness_report.v1", payload["core_readiness_schema"])
        self.assertEqual("partial", payload["core_gate_status"])
        self.assertIs(payload["checkpoint_passed"], True)
        self.assertEqual([], payload["missing_docs"])
        self.assertEqual([], payload["errors"])
        self.assertIs(payload["runner_constraints"]["aggregates_leaf_evidence_only"], True)
        self.assertIs(payload["runner_constraints"]["invokes_tests"], False)
        self.assertIs(payload["runner_constraints"]["invokes_checkpoint_as_subprocess"], False)
        self.assertEqual(0, payload["process_fanout"]["subprocess_count"])
        self.assertEqual(0, payload["process_fanout"]["test_runner_count"])
        self.assertEqual(0, payload["process_fanout"]["checkpoint_subprocess_count"])
        for field in SAFETY_FALSE_FIELDS:
            self.assertIs(payload["safety_false_fields"][field], False)

    def test_validator_negative_self_test_detects_unsafe_mutations(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), "--self-test-negative"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
            timeout=60,
        )

        payload = json.loads(result.stdout)
        negative = payload["negative_self_test"]
        self.assertEqual("passed", payload["status"])
        self.assertIs(negative["enabled"], True)
        self.assertIs(negative["passed"], True)
        self.assertEqual([], negative["undetected_mutations"])
        self.assertEqual(8, negative["case_count"])
        self.assertTrue(all(case["detected"] for case in negative["cases"]))

    def test_validate_checkpoint_payload_rejects_false_safety_flags(self) -> None:
        payload = build_assetcard_governance_checkpoint(ROOT)

        for field in SAFETY_FALSE_FIELDS:
            with self.subTest(field=field):
                mutated = copy.deepcopy(payload)
                mutated[field] = True
                self.assertIn(f"{field}_not_false", validate_checkpoint_payload(mutated))

    def test_validate_checkpoint_payload_rejects_gate_and_missing_docs(self) -> None:
        payload = build_assetcard_governance_checkpoint(ROOT)

        gate_mutated = copy.deepcopy(payload)
        gate_mutated["core_gate_status"] = "ready_for_planning"
        self.assertIn("core_gate_status_not_partial", validate_checkpoint_payload(gate_mutated))

        docs_mutated = copy.deepcopy(payload)
        docs_mutated["missing_docs"] = ["docs/MISSING_ASSETCARD_DOC.md"]
        self.assertIn("missing_docs_not_empty", validate_checkpoint_payload(docs_mutated))

    def test_build_validation_report_does_not_claim_integration(self) -> None:
        payload = build_validation_report(self_test_negative=True)

        self.assertEqual("passed", payload["status"])
        self.assertIs(payload["boundary"]["exports_assetcards"], False)
        self.assertIs(payload["boundary"]["runs_fixture_packets"], False)
        self.assertIs(payload["boundary"]["imports_downstream_repos"], False)

    def test_validator_does_not_fan_out_to_tests_or_checkpoint_subprocess(self) -> None:
        source = VALIDATOR.read_text(encoding="utf-8")

        self.assertNotIn("subprocess.", source)
        self.assertNotIn("pytest", source)
        self.assertNotIn("unittest", source)
        self.assertNotIn(str(CHECKPOINT), source)


if __name__ == "__main__":
    unittest.main()
