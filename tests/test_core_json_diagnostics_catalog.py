from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_json_diagnostic_sweep_plan import build_core_json_diagnostic_sweep_plan
from api_launcher.core_json_diagnostics_catalog import (
    core_json_diagnostic_flags,
    core_json_diagnostic_schema_versions,
    core_json_diagnostic_specs_by_flag,
    iter_core_json_diagnostic_specs,
    status_from_payload,
)


class CoreJsonDiagnosticsCatalogTests(unittest.TestCase):
    def test_catalog_lists_current_core_json_entrypoints(self) -> None:
        flags = core_json_diagnostic_flags()

        self.assertEqual(
            (
                "--core-readiness-report-json",
                "--core-review-required-report-json",
                "--core-review-queue-readiness-json",
                "--core-job-status-report-json",
                "--core-manifest-reference-report-json",
                "--core-lifecycle-audit-json",
                "--core-deep-adapter-coverage-json",
                "--core-bounded-scheduler-plan-json",
            ),
            flags,
        )
        self.assertEqual(len(flags), len(set(flags)))

    def test_catalog_schema_versions_are_explicit(self) -> None:
        versions = core_json_diagnostic_schema_versions()

        self.assertEqual("core_readiness_report.v1", versions["--core-readiness-report-json"])
        self.assertEqual("core_review_required_report.v1", versions["--core-review-required-report-json"])
        self.assertEqual(
            "core_review_queue_readiness_report.v1",
            versions["--core-review-queue-readiness-json"],
        )
        self.assertEqual("core_job_status_report.v1", versions["--core-job-status-report-json"])
        self.assertEqual(
            "core_manifest_reference_report.v1",
            versions["--core-manifest-reference-report-json"],
        )
        self.assertEqual("core_lifecycle_audit_report.v1", versions["--core-lifecycle-audit-json"])
        self.assertEqual(
            "core_deep_adapter_coverage_report.v1",
            versions["--core-deep-adapter-coverage-json"],
        )
        self.assertEqual(
            "core_bounded_scheduler_plan_report.v1",
            versions["--core-bounded-scheduler-plan-json"],
        )

    def test_catalog_flags_are_parseable_commands(self) -> None:
        for spec in iter_core_json_diagnostic_specs():
            with self.subTest(flag=spec.flag):
                args = parse_args([spec.flag])
                self.assertTrue(getattr(args, spec.argparse_attr))
                self.assertTrue(command_requested(args))

    def test_status_extraction_supports_nested_gate_status(self) -> None:
        specs = core_json_diagnostic_specs_by_flag()

        readiness = specs["--core-readiness-report-json"]
        review_required = specs["--core-review-required-report-json"]

        self.assertEqual(
            "partial",
            status_from_payload(readiness, {"integration_planning_gate": {"status": "partial"}}),
        )
        self.assertEqual("partial", status_from_payload(review_required, {"status": "partial"}))
        self.assertEqual("", status_from_payload(readiness, {"status": "partial"}))

    def test_catalog_status_paths_resolve_against_live_cli_payloads(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        for spec in iter_core_json_diagnostic_specs():
            with self.subTest(flag=spec.flag), tempfile.TemporaryDirectory() as temp_dir:
                db_path = Path(temp_dir) / "rrkal_core_json_catalog_status_test.sqlite"
                plan = build_core_json_diagnostic_sweep_plan(str(db_path), specs=(spec,))[0]
                completed = subprocess.run(
                    [sys.executable, "-B", *plan.launcher_args],
                    cwd=repo_root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                payload = json.loads(completed.stdout)
                self.assertEqual(spec.schema_version, payload["schema_version"])
                self.assertEqual("local_temp", plan.db_path_kind)
                self.assertEqual("", completed.stderr)
                self.assertIn(status_from_payload(spec, payload), {"partial", "not_ready", "contract_only"})


if __name__ == "__main__":
    unittest.main()
