from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from api_launcher.visual_asset_contracts import (
    VISUAL_ASSET_REGISTRY_TABLE_NAME,
    visual_asset_registry_persistence_schema,
)
from api_launcher.visual_asset_registry_persistence import (
    OWNED_TEST_DATABASE_MARKER_TABLE,
    create_visual_asset_registry_table_for_owned_test_database,
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


if __name__ == "__main__":
    unittest.main()
