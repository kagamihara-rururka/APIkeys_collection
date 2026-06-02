from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_bounded_scheduler_plan_report import (
    CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
    build_core_bounded_scheduler_plan_report,
)


class CoreBoundedSchedulerPlanReportTests(unittest.TestCase):
    def test_report_is_conservative_and_schema_stable(self) -> None:
        report = build_core_bounded_scheduler_plan_report()

        self.assertEqual(
            CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
            report["schema_version"],
        )
        self.assertEqual("partial", report["status"])
        self.assertFalse(
            report["integration_planning_gate"]["ready_for_scheduler_runtime_poc"]
        )
        self.assertIn(
            "unified_scheduler_contract_schema_not_defined",
            report["missing_evidence"],
        )
        self.assertIn(
            "treating_tk_thread_policy_registry_as_full_scheduler",
            report["blocked_surfaces"],
        )
        self.assertIn(
            "bounded_scheduler_openspec",
            report["planned_surfaces"],
        )
        self.assertFalse(report["safety"]["implements_scheduler_runtime"])
        self.assertFalse(report["safety"]["changes_scheduler_schema"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["enables_auto_lifecycle_events"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_existing_evidence_lists_tk_lanes_and_sqlite_gate(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        evidence = report["existing_evidence"]

        lanes = evidence["tk_policy_registry"]["lanes"]
        lane_by_id = {lane["policy_id"]: lane for lane in lanes}
        self.assertGreaterEqual(evidence["tk_policy_registry"]["policy_count"], 8)
        self.assertEqual(1, lane_by_id["sqlite_import"]["max_active_jobs"])
        self.assertEqual(4, lane_by_id["crawler_asset"]["max_active_jobs"])

        gate = evidence["sqlite_write_gate"]
        self.assertEqual("process_per_sqlite_path", gate["scope"])
        self.assertEqual(1, gate["max_active_writers_per_database"])
        self.assertIn("download_plan_import", gate["protects"])

        single_flight = evidence["single_flight_contract"]
        self.assertEqual("TkBackgroundJobStartResult", single_flight["contract"])
        self.assertEqual(
            ("started", "duplicate", "capacity"),
            tuple(single_flight["outcomes"]),
        )

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-bounded-scheduler-plan-json"])
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
                    "--core-bounded-scheduler-plan-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(
            CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
            payload["schema_version"],
        )
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)
        self.assertFalse(payload["safety"]["implements_scheduler_runtime"])


if __name__ == "__main__":
    unittest.main()
