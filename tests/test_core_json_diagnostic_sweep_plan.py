from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_json_diagnostic_sweep_plan import (
    CORE_JSON_DIAGNOSTIC_SWEEP_PLAN_SCHEMA_VERSION,
    build_core_json_diagnostic_sweep_plan,
    build_core_json_diagnostic_sweep_plan_report,
    classify_core_json_sweep_db_path,
)
from api_launcher.core_json_diagnostics_catalog import (
    core_json_diagnostic_flags,
    core_json_diagnostic_schema_versions,
    core_json_diagnostic_specs_by_flag,
)


class CoreJsonDiagnosticSweepPlanTests(unittest.TestCase):
    def test_sweep_plan_uses_explicit_db_for_all_catalog_flags(self) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "rrkal_core_json_sweep_test.sqlite")
        plans = build_core_json_diagnostic_sweep_plan(db_path)
        versions = core_json_diagnostic_schema_versions()
        specs_by_flag = core_json_diagnostic_specs_by_flag()

        self.assertEqual(core_json_diagnostic_flags(), tuple(plan.flag for plan in plans))
        for plan in plans:
            with self.subTest(flag=plan.flag):
                self.assertTrue(plan.uses_explicit_db)
                self.assertEqual("local_temp", plan.db_path_kind)
                self.assertEqual(versions[plan.flag], plan.schema_version)
                self.assertEqual(specs_by_flag[plan.flag].requires_repository, plan.requires_repository)
                self.assertEqual(("APIkeys_collection.py", "--db", db_path, plan.flag), plan.launcher_args)

    def test_sweep_plan_preserves_non_repository_diagnostic_metadata(self) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "rrkal_core_json_sweep_test.sqlite")
        plans = build_core_json_diagnostic_sweep_plan(db_path)
        requires_repo = {plan.flag: plan.requires_repository for plan in plans}

        self.assertFalse(requires_repo["--core-deep-adapter-coverage-json"])
        self.assertTrue(requires_repo["--core-readiness-report-json"])

    def test_sweep_plan_report_is_non_executing_and_agent_readable(self) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "rrkal_core_json_sweep_test.sqlite")
        report = build_core_json_diagnostic_sweep_plan_report(db_path)

        self.assertEqual(CORE_JSON_DIAGNOSTIC_SWEEP_PLAN_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("planned", report["status"])
        self.assertEqual("non_executing_command_plan", report["scope"])
        self.assertEqual("local_temp", report["db_path_kind"])
        self.assertEqual(len(core_json_diagnostic_flags()), report["command_count"])
        self.assertFalse(report["safety"]["executes_commands"])
        self.assertFalse(report["safety"]["creates_sqlite"])
        self.assertFalse(report["safety"]["changes_product_behavior"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_sweep_plan_cli_json_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-json-diagnostic-sweep-plan-json"])
        self.assertTrue(command_requested(args))

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "rrkal_core_json_sweep_plan.sqlite"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "APIkeys_collection.py",
                    "--db",
                    str(db_path),
                    "--core-json-diagnostic-sweep-plan-json",
                ],
                cwd=Path(__file__).resolve().parents[1],
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_JSON_DIAGNOSTIC_SWEEP_PLAN_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("planned", payload["status"])
        self.assertEqual("local_temp", payload["db_path_kind"])
        self.assertEqual("", completed.stderr)

    def test_db_path_classifier_marks_cloud_drives_as_risky_for_sweeps(self) -> None:
        cloud_paths = (
            r"L:\RRKAL_project\state\launcher.sqlite",
            r"L:/RRKAL_project/state/launcher.sqlite",
            "L:",
            r"K:\APIkeys_collection\state\launcher.sqlite",
            r"K:/APIkeys_collection/state/launcher.sqlite",
            "K:",
        )

        for path in cloud_paths:
            with self.subTest(path=path):
                self.assertEqual("cloud_drive", classify_core_json_sweep_db_path(path))

    def test_db_path_classifier_accepts_temp_path(self) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "rrkal_core_json_sweep_test.sqlite")

        self.assertEqual("local_temp", classify_core_json_sweep_db_path(db_path))


if __name__ == "__main__":
    unittest.main()
