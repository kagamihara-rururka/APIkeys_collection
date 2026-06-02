from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_review_required_report import (
    CORE_REVIEW_REQUIRED_REPORT_SCHEMA_VERSION,
    build_core_review_required_report,
)


class CoreReviewRequiredReportTests(unittest.TestCase):
    def test_report_summarizes_review_required_surfaces_conservatively(self) -> None:
        report = build_core_review_required_report()

        self.assertEqual(CORE_REVIEW_REQUIRED_REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("partial", report["status"])
        self.assertIn("unsupported_payload_format", report["blocked_surfaces"])
        self.assertIn("review_queue_persistence_not_unified", report["missing_evidence"])
        self.assertIn("visual_skin_asset_review_required", report["review_required_surfaces"])
        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["changes_review_queue_schema"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_report_uses_content_registry_review_rules(self) -> None:
        report = build_core_review_required_report()
        rules = report["existing_evidence"]["content_review_rules"]

        self.assertGreaterEqual(report["existing_evidence"]["content_review_rule_count"], 6)
        self.assertIn("archive_or_compressed_review", {rule["rule_id"] for rule in rules})
        self.assertIn("scientific_grid_review", {rule["rule_id"] for rule in rules})
        self.assertEqual(
            "unsupported_payload_format",
            report["existing_evidence"]["unknown_fallback"]["review_bucket"],
        )

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-review-required-report-json"])
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
                    "--core-review-required-report-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_REVIEW_REQUIRED_REPORT_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
