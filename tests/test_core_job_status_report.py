from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_job_status_report import (
    CORE_JOB_STATUS_REPORT_SCHEMA_VERSION,
    build_core_job_status_report,
)


class CoreJobStatusReportTests(unittest.TestCase):
    def test_report_keeps_job_status_evidence_conservative(self) -> None:
        report = build_core_job_status_report()

        self.assertEqual(CORE_JOB_STATUS_REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("partial", report["status"])
        self.assertIn(
            "unified_bounded_job_scheduler_not_yet_implemented",
            report["missing_evidence"],
        )
        self.assertIn("auto_lifecycle_event_emission_disabled", report["blocked_surfaces"])
        self.assertIn("visual_ready_event_writer_contract", report["contract_only_surfaces"])
        self.assertIn("external_builder_job_status_adapter", report["planned_surfaces"])
        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["changes_scheduler_schema"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["changes_lifecycle_statuses"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_visual_lifecycle_evidence_keeps_auto_events_disabled(self) -> None:
        report = build_core_job_status_report()
        visual = report["existing_evidence"]["visual_lifecycle"]

        self.assertIn("ready", visual["statuses"])
        self.assertIn("review_required", visual["statuses"])
        self.assertFalse(visual["auto_event_emission"])
        self.assertEqual(
            "log_visual_asset_ready_registry_entry",
            visual["event_writer_contract"],
        )
        self.assertIn("ready", visual["status_display_profiles"])

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-job-status-report-json"])
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
                    "--core-job-status-report-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_JOB_STATUS_REPORT_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)

        policy = payload["existing_evidence"]["background_job_policy"]
        self.assertTrue(policy["policy_registry_available"])
        self.assertGreaterEqual(policy["bounded_tk_policy_count"], 8)
        self.assertEqual(1, policy["max_active_jobs_by_policy"]["sqlite_import"])
        self.assertEqual(
            "TkBackgroundJobStartResult",
            policy["single_flight_start_result_contract"],
        )
        self.assertEqual(
            ("started", "duplicate", "capacity"),
            tuple(policy["single_flight_start_outcomes"]),
        )
        self.assertTrue(policy["direct_thread_spawn_guarded"])


if __name__ == "__main__":
    unittest.main()
