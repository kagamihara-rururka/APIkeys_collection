from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_manifest_reference_report import (
    CORE_MANIFEST_REFERENCE_REPORT_SCHEMA_VERSION,
    build_core_manifest_reference_report,
)


class CoreManifestReferenceReportTests(unittest.TestCase):
    def test_report_summarizes_manifest_evidence_without_payload_reads(self) -> None:
        report = build_core_manifest_reference_report()

        self.assertEqual(CORE_MANIFEST_REFERENCE_REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("partial", report["status"])
        self.assertIn(
            "formal_user_database_manifest_reference_persistence_not_unified",
            report["missing_evidence"],
        )
        self.assertIn("renderer_payload_loading_disabled", report["blocked_surfaces"])
        self.assertIn("visual_skin_asset_registry_table", report["contract_only_surfaces"])
        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["reads_renderer_payloads"])
        self.assertFalse(report["safety"]["reads_npz"])
        self.assertFalse(report["safety"]["imports_renderer_projects"])
        self.assertFalse(report["safety"]["imports_compressor_projects"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_download_sidecar_manifest_contract_keeps_source_and_checksum_fields(self) -> None:
        report = build_core_manifest_reference_report()
        sidecar = report["existing_evidence"]["download_sidecar_manifest_contract"]

        self.assertEqual("AssetManifest", sidecar["contract"])
        self.assertIn("source_url", sidecar["present_required_fields"])
        self.assertIn("sha256", sidecar["present_required_fields"])
        self.assertIn("size_bytes", sidecar["present_required_fields"])
        self.assertEqual("sha256", sidecar["hash_algorithm"])
        self.assertGreater(sidecar["hash_chunk_size_bytes"], 0)
        self.assertEqual("utf-8", sidecar["sidecar_json_encoding"])

    def test_visual_manifest_reference_stays_control_plane_only(self) -> None:
        report = build_core_manifest_reference_report()
        visual = report["existing_evidence"]["visual_skin_manifest_reference_contract"]
        registry = report["existing_evidence"]["registry_persistence_projection"]
        event_context = report["existing_evidence"]["ready_event_manifest_context"]

        self.assertEqual(
            "renderer_skin_asset_manifest_projection",
            visual["projection_contract"],
        )
        self.assertIn("manifest_path", visual["present_required_fields"])
        self.assertIn("checksum", visual["present_required_fields"])
        self.assertFalse(visual["payload_columns_allowed"])
        self.assertFalse(visual["payload_loading"])
        self.assertTrue(registry["requires_explicit_migration"])
        self.assertFalse(registry["create_table_automatically"])
        self.assertFalse(registry["auto_event_emission"])
        self.assertTrue(event_context["carries_manifest_path"])
        self.assertTrue(event_context["carries_lineage"])
        self.assertFalse(event_context["automatic_event_emission"])

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-manifest-reference-report-json"])
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
                    "--core-manifest-reference-report-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_MANIFEST_REFERENCE_REPORT_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)


if __name__ == "__main__":
    unittest.main()
