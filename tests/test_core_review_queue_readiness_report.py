from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_review_queue_readiness_report import (
    CORE_REVIEW_QUEUE_READINESS_REPORT_SCHEMA_VERSION,
    build_core_review_queue_readiness_report,
    review_item_identity_contract_draft,
)


class CoreReviewQueueReadinessReportTests(unittest.TestCase):
    def test_report_keeps_review_queue_readiness_conservative(self) -> None:
        report = build_core_review_queue_readiness_report()

        self.assertEqual(
            CORE_REVIEW_QUEUE_READINESS_REPORT_SCHEMA_VERSION,
            report["schema_version"],
        )
        self.assertEqual("partial", report["status"])
        self.assertIn(
            "review_queue_persistence_schema_not_defined",
            report["missing_evidence"],
        )
        self.assertIn(
            "stable_review_item_identity_not_persisted",
            report["missing_evidence"],
        )
        self.assertNotIn(
            "stable_review_item_identity_not_defined",
            report["missing_evidence"],
        )
        self.assertIn(
            "treating_display_counts_as_persisted_queue",
            report["blocked_surfaces"],
        )
        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["adds_review_queue_schema"])
        self.assertFalse(report["safety"]["writes_review_queue_records"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_report_separates_display_payloads_from_durable_queue(self) -> None:
        report = build_core_review_queue_readiness_report()
        display_payloads = report["existing_evidence"]["display_payloads"]
        volatile_surfaces = report["existing_evidence"]["volatile_review_surfaces"]

        self.assertIn(
            "review_required",
            display_payloads["plan_outcome_review_buckets"],
        )
        self.assertGreaterEqual(display_payloads["content_review_bucket_count"], 3)
        self.assertIn("plan_outcome_review_required_count", volatile_surfaces)
        self.assertIn("review_queue_repository_read_write_not_defined", report["missing_evidence"])

    def test_report_uses_existing_review_required_report_bridge(self) -> None:
        report = build_core_review_queue_readiness_report()
        review_required = report["existing_evidence"]["review_required_report"]

        self.assertEqual("core_review_required_report.v1", review_required["schema_version"])
        self.assertEqual("partial", review_required["status"])
        self.assertGreaterEqual(review_required["review_required_surface_count"], 1)
        self.assertIn("visual_skin_asset_review_required", report["review_required_surfaces"])

    def test_review_item_identity_contract_is_contract_only(self) -> None:
        report = build_core_review_queue_readiness_report()
        contract = report["existing_evidence"]["review_item_identity_contract_draft"]

        self.assertEqual(
            "core_review_item_identity_contract_draft.v1",
            contract["schema_version"],
        )
        self.assertEqual("contract_only", contract["status"])
        self.assertEqual("stable_identity_shape_only", contract["scope"])
        self.assertEqual(
            ["review_item_id", "source_surface", "source_reference"],
            contract["identity_fields"],
        )

        fields = {field["field_id"]: field for field in contract["fields"]}
        for required_field in (
            "review_item_id",
            "source_surface",
            "source_reference",
            "review_bucket",
            "next_action",
        ):
            self.assertIn(required_field, fields)
            self.assertTrue(fields[required_field]["required"])

        safety = contract["safety"]
        self.assertFalse(safety["adds_review_queue_schema"])
        self.assertFalse(safety["writes_review_queue_records"])
        self.assertFalse(safety["defines_review_resolution_statuses"])
        self.assertFalse(safety["changes_lifecycle_schema"])
        self.assertFalse(safety["promotes_review_required_to_ready"])
        self.assertFalse(safety["cross_repo_implementation"])

    def test_review_item_identity_contract_function_has_no_runtime_side_effect_flags(self) -> None:
        contract = review_item_identity_contract_draft()
        safety = contract["safety"]

        self.assertFalse(safety["imports_renderer_projects"])
        self.assertFalse(safety["imports_compressor_projects"])
        self.assertFalse(safety["reads_renderer_payloads"])
        self.assertFalse(safety["reads_npz"])

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-review-queue-readiness-json"])
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
                    "--core-review-queue-readiness-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(
            CORE_REVIEW_QUEUE_READINESS_REPORT_SCHEMA_VERSION,
            payload["schema_version"],
        )
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
