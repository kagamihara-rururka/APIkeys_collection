from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_deep_adapter_coverage_report import (
    CORE_DEEP_ADAPTER_COVERAGE_REPORT_SCHEMA_VERSION,
    build_core_deep_adapter_coverage_report,
)


class CoreDeepAdapterCoverageReportTests(unittest.TestCase):
    def test_report_keeps_source_crawlers_and_deep_adapters_separate(self) -> None:
        report = build_core_deep_adapter_coverage_report()

        self.assertEqual(CORE_DEEP_ADAPTER_COVERAGE_REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("partial", report["status"])
        self.assertIn(
            "deep_adapter_coverage_does_not_match_supported_source_types",
            report["missing_evidence"],
        )
        self.assertIn("claiming_metadata_crawler_as_deep_adapter", report["blocked_surfaces"])
        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["adds_new_adapter"])
        self.assertFalse(report["safety"]["changes_crawler_dispatch"])
        self.assertFalse(report["safety"]["changes_download_import_behavior"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_report_surfaces_current_counts_without_fake_coverage(self) -> None:
        report = build_core_deep_adapter_coverage_report()
        evidence = report["existing_evidence"]
        crawler_registry = evidence["crawler_registry"]
        adapter_inventory = evidence["deep_adapter_inventory"]
        gap_table = evidence["source_type_gap_table"]

        self.assertGreaterEqual(crawler_registry["source_type_count"], 14)
        self.assertEqual(3, adapter_inventory["dataset_adapter_count"])
        self.assertEqual(crawler_registry["source_type_count"], len(gap_table))
        self.assertTrue(
            all(
                row["deep_adapter_status"] == "unmapped_to_provider_specific_adapter_inventory"
                for row in gap_table
            )
        )
        self.assertIn("provider_specific_dataset_adapter_not_source_crawler_handler", adapter_inventory["source_type_scope"])

    def test_report_lists_implemented_adapter_paths_as_not_source_type_handlers(self) -> None:
        report = build_core_deep_adapter_coverage_report()
        adapter_paths = report["existing_evidence"]["implemented_adapter_paths"]

        self.assertEqual(3, len(adapter_paths))
        self.assertIn("gebco_topography", {adapter["adapter_id"] for adapter in adapter_paths})
        self.assertTrue(all(adapter["source_type_handler"] is False for adapter in adapter_paths))

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-deep-adapter-coverage-json"])
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
                    "--core-deep-adapter-coverage-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_DEEP_ADAPTER_COVERAGE_REPORT_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
