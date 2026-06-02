from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_lifecycle_audit_report import (
    CORE_LIFECYCLE_AUDIT_REPORT_SCHEMA_VERSION,
    build_core_lifecycle_audit_report,
)


class CoreLifecycleAuditReportTests(unittest.TestCase):
    def test_report_audits_lifecycle_without_creating_state_machine(self) -> None:
        report = build_core_lifecycle_audit_report()

        self.assertEqual(CORE_LIFECYCLE_AUDIT_REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("partial", report["status"])
        self.assertIn("runtime_lifecycle_state_machine_not_unified", report["missing_evidence"])
        self.assertIn("transition_rule_persistence_not_defined", report["missing_evidence"])
        self.assertIn(
            "automatic_lifecycle_transition_execution_disabled",
            report["blocked_surfaces"],
        )
        self.assertIn("visual_skin_asset_lifecycle_display_profile", report["contract_only_surfaces"])
        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["changes_lifecycle_statuses"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["implements_runtime_state_machine"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_report_classifies_current_status_vocabulary(self) -> None:
        report = build_core_lifecycle_audit_report()
        vocabulary = report["existing_evidence"]["lifecycle_vocabulary"]
        classification = report["existing_evidence"]["status_classification"]

        self.assertEqual(7, vocabulary["status_count"])
        self.assertTrue(vocabulary["schema_matches_runtime_vocabulary"])
        self.assertIn("ready", classification["ready_statuses"])
        self.assertIn("failed", classification["terminal_statuses"])
        self.assertIn("rejected", classification["terminal_statuses"])
        self.assertIn("review_required", classification["review_required_statuses"])
        self.assertIn("planned", classification["construction_statuses"])
        self.assertIn("building", classification["construction_statuses"])

    def test_report_marks_ready_event_contract_as_guard_not_transition(self) -> None:
        report = build_core_lifecycle_audit_report()
        edges = report["existing_evidence"]["contract_edges"]

        self.assertFalse(edges["build_request_to_build_result"]["runtime_transition"])
        self.assertEqual(
            "ready",
            edges["ready_registry_entry_to_ready_event"]["requires_status"],
        )
        self.assertTrue(edges["ready_registry_entry_to_ready_event"]["rejects_non_ready"])
        self.assertFalse(edges["ready_registry_entry_to_ready_event"]["runtime_transition"])

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-lifecycle-audit-json"])
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
                    "--core-lifecycle-audit-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_LIFECYCLE_AUDIT_REPORT_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
