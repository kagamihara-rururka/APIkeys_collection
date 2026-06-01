from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from api_launcher.visual_asset_contracts import (
    RendererSkinAssetReference,
    RendererSkinAssetRegistryEntry,
    SkinAssetLifecycleStatus,
    VISUAL_ASSET_REGISTRY_TABLE_NAME,
    visual_asset_registry_persistence_schema,
)
from api_launcher.visual_asset_registry_persistence import (
    OWNED_TEST_DATABASE_MARKER_TABLE,
    create_visual_asset_registry_table_for_owned_test_database,
    list_visual_asset_registry_entry_payloads_for_owned_test_database,
    read_visual_asset_registry_entry_payload_for_owned_test_database,
    visual_asset_registry_owned_test_drop_preview,
    write_visual_asset_registry_entry_for_owned_test_database,
)


class VisualAssetRegistryPersistenceTests(unittest.TestCase):
    def test_owned_test_table_creation_requires_explicit_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"

            with self.assertRaisesRegex(ValueError, "allow_owned_test_database=True"):
                create_visual_asset_registry_table_for_owned_test_database(db_path)

            self.assertFalse(db_path.exists())

    def test_owned_test_table_creation_materializes_schema_and_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"

            result = create_visual_asset_registry_table_for_owned_test_database(
                db_path,
                allow_owned_test_database=True,
            )

            self.assertTrue(result["creates_database_state"])
            self.assertFalse(result["dry_run"])
            self.assertEqual("owned_test_database_only", result["scope"])
            self.assertTrue(result["owned_test_database"])
            self.assertTrue(result["table_exists"])
            self.assertTrue(result["marker_table_exists"])
            self.assertFalse(result["auto_event_emission"])
            self.assertTrue(result["control_plane_only"])
            self.assertFalse(result["payload_loading"])

            schema = visual_asset_registry_persistence_schema()
            expected_columns = [column["name"] for column in schema["columns"]]
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                table_names = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }
                columns = [row["name"] for row in conn.execute(f'PRAGMA table_info("{VISUAL_ASSET_REGISTRY_TABLE_NAME}")')]
                indexes = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }

            self.assertIn(VISUAL_ASSET_REGISTRY_TABLE_NAME, table_names)
            self.assertIn(OWNED_TEST_DATABASE_MARKER_TABLE, table_names)
            self.assertEqual(expected_columns, columns)
            self.assertIn("idx_visual_skin_asset_registry_status", indexes)
            self.assertIn("idx_visual_skin_asset_registry_dataset", indexes)
            self.assertNotIn("payload_bytes", columns)
            self.assertNotIn("npz_payload", columns)

    def test_owned_test_table_creation_rejects_existing_unowned_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "user.sqlite"
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("CREATE TABLE user_data (id INTEGER PRIMARY KEY)")
                conn.commit()

            with self.assertRaisesRegex(ValueError, "unowned existing SQLite database"):
                create_visual_asset_registry_table_for_owned_test_database(
                    db_path,
                    allow_owned_test_database=True,
                )

            with closing(sqlite3.connect(db_path)) as conn:
                table_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }

            self.assertEqual({"user_data"}, table_names)

    def test_owned_test_entry_write_requires_explicit_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"
            entry = _registry_entry("entry-ready", "skin-ready")

            with self.assertRaisesRegex(ValueError, "allow_owned_test_database=True"):
                write_visual_asset_registry_entry_for_owned_test_database(db_path, entry)

            self.assertFalse(db_path.exists())

    def test_owned_test_entry_write_read_and_list_round_trip_control_plane_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"
            entry = _registry_entry(
                "entry-ready",
                "skin-ready",
                metadata={
                    "note": "safe metadata",
                    "tags": ("terrain", "preview"),
                    "payload_bytes": "do-not-store",
                    "token": "do-not-store",
                },
            )

            write_result = write_visual_asset_registry_entry_for_owned_test_database(
                db_path,
                entry,
                allow_owned_test_database=True,
            )
            read_payload = read_visual_asset_registry_entry_payload_for_owned_test_database(
                db_path,
                "entry-ready",
                allow_owned_test_database=True,
            )
            listed_payloads = list_visual_asset_registry_entry_payloads_for_owned_test_database(
                db_path,
                allow_owned_test_database=True,
            )

            self.assertEqual("write_visual_asset_registry_entry_for_owned_test_database", write_result["operation"])
            self.assertEqual("entry-ready", write_result["registry_entry_id"])
            self.assertEqual("owned_test_database_only", write_result["scope"])
            self.assertFalse(write_result["auto_event_emission"])
            self.assertTrue(write_result["control_plane_only"])
            self.assertFalse(write_result["payload_loading"])

            self.assertIsNotNone(read_payload)
            assert read_payload is not None
            self.assertEqual("entry-ready", read_payload["registry_entry_id"])
            self.assertEqual("skin-ready", read_payload["skin_asset"]["skin_asset_id"])
            self.assertEqual("ready", read_payload["lifecycle_status"])
            self.assertEqual(["displaytools", "qt_preview"], read_payload["renderer_targets"])
            self.assertEqual({"note": "safe metadata", "tags": ["terrain", "preview"]}, read_payload["metadata"])
            self.assertFalse(read_payload["auto_event_emission"])
            self.assertTrue(read_payload["control_plane_only"])
            self.assertFalse(read_payload["payload_loading"])
            self.assertNotIn("payload_bytes", str(read_payload))
            self.assertNotIn("do-not-store", str(read_payload))
            self.assertEqual([read_payload], listed_payloads)

            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    f'SELECT * FROM "{VISUAL_ASSET_REGISTRY_TABLE_NAME}" WHERE registry_entry_id = ?',
                    ("entry-ready",),
                ).fetchone()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual("entry-ready", row["registry_entry_id"])
            self.assertEqual("ready", row["lifecycle_status"])
            self.assertNotIn("payload_bytes", row["metadata_json"])
            self.assertNotIn("token", row["metadata_json"])

    def test_owned_test_entry_write_upserts_without_duplicate_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"
            first = _registry_entry("entry-ready", "skin-ready", checksum="abc")
            second = _registry_entry("entry-ready", "skin-ready", checksum="def")

            write_visual_asset_registry_entry_for_owned_test_database(
                db_path,
                first,
                allow_owned_test_database=True,
            )
            write_visual_asset_registry_entry_for_owned_test_database(
                db_path,
                second,
                allow_owned_test_database=True,
            )

            payloads = list_visual_asset_registry_entry_payloads_for_owned_test_database(
                db_path,
                allow_owned_test_database=True,
            )

            self.assertEqual(1, len(payloads))
            self.assertEqual("def", payloads[0]["skin_asset"]["checksum"])

    def test_owned_test_read_rejects_existing_unowned_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "user.sqlite"
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("CREATE TABLE user_data (id INTEGER PRIMARY KEY)")
                conn.commit()

            with self.assertRaisesRegex(ValueError, "unowned SQLite database"):
                read_visual_asset_registry_entry_payload_for_owned_test_database(
                    db_path,
                    "entry-ready",
                    allow_owned_test_database=True,
                )

    def test_owned_test_drop_preview_requires_explicit_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"

            with self.assertRaisesRegex(ValueError, "allow_owned_test_database=True"):
                visual_asset_registry_owned_test_drop_preview(db_path)

            self.assertFalse(db_path.exists())

    def test_owned_test_drop_preview_is_dry_run_and_keeps_database_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "visual-registry.sqlite"
            write_visual_asset_registry_entry_for_owned_test_database(
                db_path,
                _registry_entry("entry-ready", "skin-ready"),
                allow_owned_test_database=True,
            )

            preview = visual_asset_registry_owned_test_drop_preview(
                db_path,
                allow_owned_test_database=True,
            )

            self.assertTrue(preview["dry_run"])
            self.assertFalse(preview["destructive_execution_enabled"])
            self.assertFalse(preview["mutates_database_state"])
            self.assertTrue(preview["owned_test_database"])
            self.assertTrue(preview["table_exists"])
            self.assertTrue(preview["marker_table_exists"])
            self.assertIn('DROP TABLE IF EXISTS "visual_skin_asset_registry";', preview["statements"])
            self.assertIn(
                f'DROP TABLE IF EXISTS "{OWNED_TEST_DATABASE_MARKER_TABLE}";',
                preview["statements"],
            )
            self.assertIn(
                'DROP INDEX IF EXISTS "idx_visual_skin_asset_registry_status";',
                preview["statements"],
            )
            self.assertFalse(preview["auto_event_emission"])
            self.assertTrue(preview["control_plane_only"])
            self.assertFalse(preview["payload_loading"])

            with closing(sqlite3.connect(db_path)) as conn:
                table_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }

            self.assertIn(VISUAL_ASSET_REGISTRY_TABLE_NAME, table_names)
            self.assertIn(OWNED_TEST_DATABASE_MARKER_TABLE, table_names)

    def test_owned_test_drop_preview_rejects_existing_unowned_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "user.sqlite"
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("CREATE TABLE user_data (id INTEGER PRIMARY KEY)")
                conn.commit()

            with self.assertRaisesRegex(ValueError, "unowned SQLite database"):
                visual_asset_registry_owned_test_drop_preview(
                    db_path,
                    allow_owned_test_database=True,
                )


def _registry_entry(
    registry_entry_id: str,
    skin_asset_id: str,
    *,
    checksum: str = "abc123",
    metadata: dict[str, object] | None = None,
) -> RendererSkinAssetRegistryEntry:
    skin_asset = RendererSkinAssetReference(
        skin_asset_id=skin_asset_id,
        source_request_id="request-ready",
        source_curated_asset_id="curated-ready",
        dataset_uid="dataset-ready",
        manifest_path="state/visual_assets/ready.manifest.json",
        lifecycle_status=SkinAssetLifecycleStatus.READY,
        renderer_targets=("displaytools", "qt_preview"),
        checksum=checksum,
        size_bytes=4096,
        created_at="2026-06-02T00:00:00Z",
    )
    return RendererSkinAssetRegistryEntry(
        registry_entry_id=registry_entry_id,
        skin_asset=skin_asset,
        review_required=True,
        registered_at="2026-06-02T00:01:00Z",
        updated_at="2026-06-02T00:02:00Z",
        metadata=dict(metadata or {}),
    )


if __name__ == "__main__":
    unittest.main()
