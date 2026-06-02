from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_readiness_report import (
    CORE_READINESS_SCHEMA_VERSION,
    build_core_readiness_report,
)


class CoreReadinessReportTests(unittest.TestCase):
    def test_report_has_required_sections_and_safety_flags(self) -> None:
        report = build_core_readiness_report()

        self.assertEqual(CORE_READINESS_SCHEMA_VERSION, report["schema_version"])
        for section in (
            "registry_evidence",
            "lifecycle_evidence",
            "manifest_reference_evidence",
            "review_required_evidence",
            "job_status_evidence",
            "asset_lineage_evidence",
            "integration_planning_gate",
        ):
            self.assertIn(section, report)

        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["imports_renderer_projects"])
        self.assertFalse(report["safety"]["imports_compressor_projects"])
        self.assertFalse(report["safety"]["reads_renderer_payloads"])
        self.assertFalse(report["safety"]["reads_npz"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_report_separates_evidence_categories(self) -> None:
        report = build_core_readiness_report()

        for section_name in (
            "registry_evidence",
            "lifecycle_evidence",
            "manifest_reference_evidence",
            "review_required_evidence",
            "job_status_evidence",
            "asset_lineage_evidence",
        ):
            section = report[section_name]
            self.assertIn("existing_evidence", section)
            self.assertIn("missing_evidence", section)
            self.assertIn("blocked_surfaces", section)
            self.assertIn("review_required_surfaces", section)
            self.assertIn("contract_only_surfaces", section)
            self.assertIn("planned_surfaces", section)
            self.assertIn("next_safe_actions", section)

    def test_missing_or_contract_only_evidence_does_not_fake_ready_for_planning(self) -> None:
        report = build_core_readiness_report()
        gate = report["integration_planning_gate"]

        self.assertIn(gate["status"], {"partial", "not_ready"})
        self.assertNotEqual("ready_for_planning", gate["status"])
        self.assertIn("visual_skin_asset_registry_persistence", gate["contract_only_surfaces"])
        self.assertIn("unified_bounded_job_scheduler_not_yet_implemented", gate["missing_evidence"])

    def test_registry_and_review_evidence_use_existing_reports(self) -> None:
        report = build_core_readiness_report()

        registry = report["registry_evidence"]["existing_evidence"]
        self.assertGreaterEqual(registry["crawler_registry"]["source_type_count"], 14)
        self.assertGreaterEqual(registry["content_registry"]["review_rule_count"], 1)
        self.assertGreaterEqual(registry["dataset_adapter_registry"]["dataset_adapter_count"], 3)

        review = report["review_required_evidence"]
        self.assertIn("unsupported_payload_format", review["blocked_surfaces"])
        self.assertTrue(review["existing_evidence"]["visual_review_status_available"])

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-readiness-report-json"])
        self.assertTrue(command_requested(args))

        with tempfile.TemporaryDirectory() as tmpdir:
            launcher_db = Path(tmpdir) / "launcher.sqlite"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "APIkeys_collection.py",
                    "--db",
                    str(launcher_db),
                    "--core-readiness-report-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_READINESS_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["integration_planning_gate"]["status"])
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
