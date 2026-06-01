from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from api_launcher.sqlite_write_gate import sqlite_write_gate
from api_launcher.visual_asset_contracts import (
    VISUAL_ASSET_REGISTRY_TABLE_NAME,
    visual_asset_registry_sqlite_ddl_preview,
)


OWNED_TEST_DATABASE_MARKER_TABLE = "__rrkal_owned_test_database_marker"
VISUAL_ASSET_REGISTRY_OWNED_TEST_MARKER = "visual_asset_registry_persistence"


def create_visual_asset_registry_table_for_owned_test_database(
    sqlite_path: str | Path,
    *,
    allow_owned_test_database: bool = False,
) -> dict[str, Any]:
    """Create the visual registry table only inside an explicitly owned test DB.

    This helper is intentionally not a product migration. It exists so tests
    and future dry-run review can prove the schema can be materialized without
    granting RRKAL Core permission to mutate user databases.
    """

    if not allow_owned_test_database:
        raise ValueError(
            "Refusing to create visual asset registry table without allow_owned_test_database=True"
        )

    path = Path(sqlite_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    preview = visual_asset_registry_sqlite_ddl_preview()

    with sqlite_write_gate(path):
        with closing(sqlite3.connect(path, timeout=30)) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_owned_test_database(conn)
            for statement in preview["statements"]:
                conn.execute(statement)
            conn.commit()
            table_names = _sqlite_table_names(conn)
            index_names = _sqlite_index_names(conn)

    return {
        "operation": "create_visual_asset_registry_table_for_owned_test_database",
        "database_path": str(path),
        "table_name": VISUAL_ASSET_REGISTRY_TABLE_NAME,
        "owned_test_database": True,
        "ownership_marker": VISUAL_ASSET_REGISTRY_OWNED_TEST_MARKER,
        "creates_database_state": True,
        "dry_run": False,
        "scope": "owned_test_database_only",
        "statements_executed": len(preview["statements"]),
        "table_exists": VISUAL_ASSET_REGISTRY_TABLE_NAME in table_names,
        "marker_table_exists": OWNED_TEST_DATABASE_MARKER_TABLE in table_names,
        "index_names": sorted(index_names),
        "auto_event_emission": False,
        "control_plane_only": True,
        "payload_loading": False,
    }


def _ensure_owned_test_database(conn: sqlite3.Connection) -> None:
    table_names = _sqlite_table_names(conn)
    if table_names and OWNED_TEST_DATABASE_MARKER_TABLE not in table_names:
        raise ValueError(
            "Refusing to create visual asset registry table in an unowned existing SQLite database"
        )

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{OWNED_TEST_DATABASE_MARKER_TABLE}" (
            marker_id TEXT PRIMARY KEY,
            created_by TEXT NOT NULL
        )
        """
    )
    conn.execute(
        f"""
        INSERT OR IGNORE INTO "{OWNED_TEST_DATABASE_MARKER_TABLE}" (marker_id, created_by)
        VALUES (?, ?)
        """,
        (VISUAL_ASSET_REGISTRY_OWNED_TEST_MARKER, "RRKAL visual asset registry persistence tests"),
    )


def _sqlite_table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row["name"])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }


def _sqlite_index_names(conn: sqlite3.Connection) -> set[str]:
    return {
        str(row["name"])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }


__all__ = [
    "OWNED_TEST_DATABASE_MARKER_TABLE",
    "VISUAL_ASSET_REGISTRY_OWNED_TEST_MARKER",
    "create_visual_asset_registry_table_for_owned_test_database",
]
