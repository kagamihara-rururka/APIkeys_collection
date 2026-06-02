from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.visual_asset_contracts import (
    RendererSkinAssetReference,
    RendererSkinAssetRegistryEntry,
    SkinAssetLifecycleStatus,
)
from api_launcher.visual_asset_registry_persistence import (
    write_visual_asset_registry_entry_for_owned_test_database,
)


class VisualAssetRegistryCliTests(unittest.TestCase):
    def test_visual_registry_summary_json_reads_owned_test_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path.cwd()
            launcher_db = Path(tmpdir) / "launcher.sqlite"
            visual_db = Path(tmpdir) / "visual-registry.sqlite"
            write_visual_asset_registry_entry_for_owned_test_database(
                visual_db,
                _registry_entry("entry-ready", "skin-ready"),
                allow_owned_test_database=True,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "APIkeys_collection.py",
                    "--db",
                    str(launcher_db),
                    "--visual-registry-summary-db",
                    str(visual_db),
                    "--visual-registry-owned-test-db",
                    "--visual-registry-summary-json",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual("visual_asset_registry_summary_for_owned_test_database", payload["operation"])
            self.assertEqual(1, payload["registry_entry_count"])
            self.assertEqual(1, payload["ready_count"])
            self.assertEqual(1, payload["renderer_target_counts"]["displaytools"])
            self.assertTrue(payload["safety"]["control_plane_only"])
            self.assertFalse(payload["safety"]["payload_loading"])
            self.assertEqual("", completed.stderr)

    def test_visual_registry_summary_json_missing_db_does_not_create_visual_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path.cwd()
            launcher_db = Path(tmpdir) / "launcher.sqlite"
            visual_db = Path(tmpdir) / "missing-visual-registry.sqlite"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "APIkeys_collection.py",
                    "--db",
                    str(launcher_db),
                    "--visual-registry-summary-db",
                    str(visual_db),
                    "--visual-registry-owned-test-db",
                    "--visual-registry-summary-json",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertFalse(visual_db.exists())
            self.assertFalse(payload["database_exists"])
            self.assertEqual(0, payload["registry_entry_count"])
            self.assertTrue(payload["control_plane_only"])
            self.assertFalse(payload["payload_loading"])

    def test_visual_registry_emit_ready_event_json_is_explicit_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path.cwd()
            launcher_db = Path(tmpdir) / "launcher.sqlite"
            visual_db = Path(tmpdir) / "visual-registry.sqlite"
            event_log = Path(tmpdir) / "events.jsonl"
            write_visual_asset_registry_entry_for_owned_test_database(
                visual_db,
                _registry_entry("entry-ready", "skin-ready"),
                allow_owned_test_database=True,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "APIkeys_collection.py",
                    "--db",
                    str(launcher_db),
                    "--visual-registry-db",
                    str(visual_db),
                    "--visual-registry-owned-test-db",
                    "--visual-registry-entry-id",
                    "entry-ready",
                    "--visual-registry-event-log",
                    str(event_log),
                    "--visual-registry-emit-ready-event-json",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual("visual_asset_ready", payload["event"])
            self.assertEqual("visual_asset", payload["component"])
            self.assertEqual("entry-ready", payload["context"]["metadata"]["registry_entry_id"])
            self.assertEqual("skin-ready", payload["context"]["skin_asset_id"])
            self.assertTrue(payload["context"]["safety"]["control_plane_only"])
            self.assertFalse(payload["context"]["safety"]["payload_loading"])
            self.assertTrue(event_log.exists())
            self.assertEqual("", completed.stderr)

    def test_visual_registry_emit_ready_event_json_rejects_duplicate_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path.cwd()
            launcher_db = Path(tmpdir) / "launcher.sqlite"
            visual_db = Path(tmpdir) / "visual-registry.sqlite"
            event_log = Path(tmpdir) / "events.jsonl"
            write_visual_asset_registry_entry_for_owned_test_database(
                visual_db,
                _registry_entry("entry-ready", "skin-ready"),
                allow_owned_test_database=True,
            )
            command = [
                sys.executable,
                "-B",
                "APIkeys_collection.py",
                "--db",
                str(launcher_db),
                "--visual-registry-db",
                str(visual_db),
                "--visual-registry-owned-test-db",
                "--visual-registry-entry-id",
                "entry-ready",
                "--visual-registry-event-log",
                str(event_log),
                "--visual-registry-emit-ready-event-json",
            ]
            subprocess.run(
                command,
                cwd=root,
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

            duplicate = subprocess.run(
                command,
                cwd=root,
                check=False,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

            self.assertNotEqual(0, duplicate.returncode)
            self.assertIn("already exists", duplicate.stderr)


def _registry_entry(registry_entry_id: str, skin_asset_id: str) -> RendererSkinAssetRegistryEntry:
    skin_asset = RendererSkinAssetReference(
        skin_asset_id=skin_asset_id,
        source_request_id="request-ready",
        source_curated_asset_id="curated-ready",
        dataset_uid="dataset-ready",
        manifest_path="state/visual_assets/ready.manifest.json",
        lifecycle_status=SkinAssetLifecycleStatus.READY,
        renderer_targets=("displaytools",),
        checksum="abc123",
        size_bytes=4096,
        created_at="2026-06-02T00:00:00Z",
    )
    return RendererSkinAssetRegistryEntry(
        registry_entry_id=registry_entry_id,
        skin_asset=skin_asset,
        review_required=False,
        registered_at="2026-06-02T00:01:00Z",
        updated_at="2026-06-02T00:02:00Z",
    )


if __name__ == "__main__":
    unittest.main()
