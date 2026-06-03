from __future__ import annotations

import unittest

from api_launcher.core_openspec_evidence import (
    CORE_OPENSPEC_EVIDENCE_SCHEMA_VERSION,
    build_core_openspec_evidence,
)


class CoreOpenSpecEvidenceTests(unittest.TestCase):
    def test_openspec_inventory_lists_active_specs_without_validation_claim(self) -> None:
        evidence = build_core_openspec_evidence()
        spec_ids = {entry["spec_id"] for entry in evidence["active_specs"]}

        self.assertEqual(CORE_OPENSPEC_EVIDENCE_SCHEMA_VERSION, evidence["schema_version"])
        self.assertEqual("inventory_only_no_validation_execution", evidence["scope"])
        self.assertFalse(evidence["validation"]["executed_by_report"])
        self.assertFalse(evidence["safety"]["executes_openspec"])
        self.assertFalse(evidence["safety"]["changes_product_behavior"])
        self.assertIn("bounded-scheduler-core-contract", spec_ids)
        self.assertIn("development-workflow", spec_ids)
        self.assertIn("visual-asset-registry-persistence", spec_ids)

    def test_openspec_inventory_keeps_paths_repo_relative(self) -> None:
        evidence = build_core_openspec_evidence()

        for entry in evidence["active_specs"]:
            with self.subTest(spec_id=entry["spec_id"]):
                self.assertTrue(entry["spec_path"].startswith("openspec/specs/"))
                self.assertTrue(entry["spec_path"].endswith("/spec.md"))


if __name__ == "__main__":
    unittest.main()
