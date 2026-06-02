from __future__ import annotations

import sqlite3
import json
from contextlib import closing
from pathlib import Path
from typing import Any

from api_launcher.sqlite_write_gate import sqlite_write_gate
from api_launcher.visual_asset_contracts import (
    RendererSkinAssetReference,
    RendererSkinAssetRegistryEntry,
    VISUAL_ASSET_REGISTRY_TABLE_NAME,
    visual_asset_registry_entry_persistence_record,
    visual_asset_registry_persistence_schema,
    visual_asset_registry_sqlite_ddl_preview,
    visual_asset_registry_summary,
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
            _create_registry_table_in_owned_connection(conn, preview)
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


def write_visual_asset_registry_entry_for_owned_test_database(
    sqlite_path: str | Path,
    entry: RendererSkinAssetRegistryEntry,
    *,
    allow_owned_test_database: bool = False,
) -> dict[str, Any]:
    """Upsert one registry entry only inside an explicitly owned test DB.

    This is not the product repository path. The helper exists to prove that
    the schema and row projection can round-trip through SQLite while keeping
    event emission and renderer payload loading outside the persistence write.
    """

    if not allow_owned_test_database:
        raise ValueError(
            "Refusing to write visual asset registry entry without allow_owned_test_database=True"
        )

    path = Path(sqlite_path).expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = visual_asset_registry_entry_persistence_record(entry)
    _validate_record_matches_schema(record)

    with sqlite_write_gate(path):
        with closing(sqlite3.connect(path, timeout=30)) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_owned_test_database(conn)
            _create_registry_table_in_owned_connection(conn)
            cursor = conn.execute(_upsert_registry_record_sql(), _record_values(record))
            conn.commit()
            persisted = _fetch_registry_record(conn, entry.registry_entry_id)

    return {
        "operation": "write_visual_asset_registry_entry_for_owned_test_database",
        "database_path": str(path),
        "table_name": VISUAL_ASSET_REGISTRY_TABLE_NAME,
        "registry_entry_id": entry.registry_entry_id,
        "owned_test_database": True,
        "scope": "owned_test_database_only",
        "rows_written": cursor.rowcount,
        "persistence_record": persisted,
        "entry_payload": _entry_payload_from_persistence_record(persisted) if persisted else None,
        "auto_event_emission": False,
        "control_plane_only": True,
        "payload_loading": False,
    }


def read_visual_asset_registry_entry_payload_for_owned_test_database(
    sqlite_path: str | Path,
    registry_entry_id: str,
    *,
    allow_owned_test_database: bool = False,
) -> dict[str, Any] | None:
    """Read one persisted visual registry entry from an owned test DB only."""

    record = _read_visual_asset_registry_record_for_owned_test_database(
        sqlite_path,
        registry_entry_id,
        allow_owned_test_database=allow_owned_test_database,
    )
    return _entry_payload_from_persistence_record(record) if record else None


def _read_visual_asset_registry_record_for_owned_test_database(
    sqlite_path: str | Path,
    registry_entry_id: str,
    *,
    allow_owned_test_database: bool = False,
) -> dict[str, Any] | None:
    if not allow_owned_test_database:
        raise ValueError(
            "Refusing to read visual asset registry entry without allow_owned_test_database=True"
        )

    path = Path(sqlite_path).expanduser().resolve(strict=False)
    if not path.exists():
        return None

    with sqlite_write_gate(path):
        with closing(sqlite3.connect(path, timeout=30)) as conn:
            conn.row_factory = sqlite3.Row
            _require_owned_test_database(conn)
            return _fetch_registry_record(conn, registry_entry_id)

def read_visual_asset_registry_entry_for_owned_test_database(
    sqlite_path: str | Path,
    registry_entry_id: str,
    *,
    allow_owned_test_database: bool = False,
) -> RendererSkinAssetRegistryEntry | None:
    """Read one registry entry object from an owned test DB only.

    This object-returning helper is intentionally separate from write/upsert so
    explicit event workflows can opt into emission without making persistence
    itself know about event logging.
    """

    record = _read_visual_asset_registry_record_for_owned_test_database(
        sqlite_path,
        registry_entry_id,
        allow_owned_test_database=allow_owned_test_database,
    )
    return _entry_from_persistence_record(record) if record else None


def list_visual_asset_registry_entry_payloads_for_owned_test_database(
    sqlite_path: str | Path,
    *,
    allow_owned_test_database: bool = False,
) -> list[dict[str, Any]]:
    """List persisted visual registry entries from an owned test DB only."""

    if not allow_owned_test_database:
        raise ValueError(
            "Refusing to list visual asset registry entries without allow_owned_test_database=True"
        )

    path = Path(sqlite_path).expanduser().resolve(strict=False)
    if not path.exists():
        return []

    with sqlite_write_gate(path):
        with closing(sqlite3.connect(path, timeout=30)) as conn:
            conn.row_factory = sqlite3.Row
            _require_owned_test_database(conn)
            if VISUAL_ASSET_REGISTRY_TABLE_NAME not in _sqlite_table_names(conn):
                return []
            records = [
                _record_from_row(row)
                for row in conn.execute(
                    f"SELECT * FROM {_sqlite_identifier(VISUAL_ASSET_REGISTRY_TABLE_NAME)} "
                    "ORDER BY registry_entry_id"
                ).fetchall()
            ]

    return [_entry_payload_from_persistence_record(record) for record in records]


def visual_asset_registry_summary_for_owned_test_database(
    sqlite_path: str | Path,
    *,
    allow_owned_test_database: bool = False,
) -> dict[str, Any]:
    """Summarize persisted visual registry rows from an owned test DB only."""

    if not allow_owned_test_database:
        raise ValueError(
            "Refusing to summarize visual asset registry entries without allow_owned_test_database=True"
        )

    path = Path(sqlite_path).expanduser().resolve(strict=False)
    if not path.exists():
        return _summary_payload(
            path,
            database_exists=False,
            owned_test_database=False,
            table_exists=False,
            entries=(),
        )

    with sqlite_write_gate(path):
        with closing(sqlite3.connect(path, timeout=30)) as conn:
            conn.row_factory = sqlite3.Row
            _require_owned_test_database(conn)
            table_names = _sqlite_table_names(conn)
            if VISUAL_ASSET_REGISTRY_TABLE_NAME in table_names:
                records = [
                    _record_from_row(row)
                    for row in conn.execute(
                        f"SELECT * FROM {_sqlite_identifier(VISUAL_ASSET_REGISTRY_TABLE_NAME)} "
                        "ORDER BY registry_entry_id"
                    ).fetchall()
                ]
            else:
                records = []

    entries = tuple(_entry_from_persistence_record(record) for record in records)
    return _summary_payload(
        path,
        database_exists=True,
        owned_test_database=True,
        table_exists=VISUAL_ASSET_REGISTRY_TABLE_NAME in table_names,
        entries=entries,
    )


def visual_asset_registry_owned_test_drop_preview(
    sqlite_path: str | Path,
    *,
    allow_owned_test_database: bool = False,
) -> dict[str, Any]:
    """Render reviewable rollback SQL for an owned test DB without executing it."""

    if not allow_owned_test_database:
        raise ValueError(
            "Refusing to preview visual asset registry rollback without allow_owned_test_database=True"
        )

    path = Path(sqlite_path).expanduser().resolve(strict=False)
    if not path.exists():
        return _drop_preview_payload(path, database_exists=False, owned_test_database=False)

    with sqlite_write_gate(path):
        with closing(sqlite3.connect(path, timeout=30)) as conn:
            conn.row_factory = sqlite3.Row
            _require_owned_test_database(conn)
            table_names = _sqlite_table_names(conn)
            index_names = _sqlite_index_names(conn)

    return _drop_preview_payload(
        path,
        database_exists=True,
        owned_test_database=True,
        table_names=table_names,
        index_names=index_names,
    )


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


def _require_owned_test_database(conn: sqlite3.Connection) -> None:
    if OWNED_TEST_DATABASE_MARKER_TABLE not in _sqlite_table_names(conn):
        raise ValueError(
            "Refusing to read visual asset registry entries from an unowned SQLite database"
        )


def _create_registry_table_in_owned_connection(
    conn: sqlite3.Connection,
    preview: dict[str, Any] | None = None,
) -> None:
    ddl_preview = preview or visual_asset_registry_sqlite_ddl_preview()
    for statement in ddl_preview["statements"]:
        conn.execute(statement)


def _validate_record_matches_schema(record: dict[str, Any]) -> None:
    expected = set(_registry_column_names())
    if set(record) != expected:
        missing = sorted(expected - set(record))
        unexpected = sorted(set(record) - expected)
        raise ValueError(
            "Visual asset registry persistence record does not match schema "
            f"(missing={missing}, unexpected={unexpected})"
        )


def _registry_column_names() -> tuple[str, ...]:
    schema = visual_asset_registry_persistence_schema()
    return tuple(str(column["name"]) for column in schema["columns"])


def _record_values(record: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record[column] for column in _registry_column_names())


def _upsert_registry_record_sql() -> str:
    columns = _registry_column_names()
    primary_key = "registry_entry_id"
    column_sql = ", ".join(_sqlite_identifier(column) for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    update_columns = tuple(column for column in columns if column != primary_key)
    update_sql = ", ".join(
        f"{_sqlite_identifier(column)} = excluded.{_sqlite_identifier(column)}"
        for column in update_columns
    )
    return (
        f"INSERT INTO {_sqlite_identifier(VISUAL_ASSET_REGISTRY_TABLE_NAME)} ({column_sql}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT({_sqlite_identifier(primary_key)}) DO UPDATE SET {update_sql}"
    )


def _fetch_registry_record(conn: sqlite3.Connection, registry_entry_id: str) -> dict[str, Any] | None:
    if VISUAL_ASSET_REGISTRY_TABLE_NAME not in _sqlite_table_names(conn):
        return None
    row = conn.execute(
        f"SELECT * FROM {_sqlite_identifier(VISUAL_ASSET_REGISTRY_TABLE_NAME)} "
        f"WHERE {_sqlite_identifier('registry_entry_id')} = ?",
        (registry_entry_id,),
    ).fetchone()
    if row is None:
        return None
    return _record_from_row(row)


def _record_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {column: row[column] for column in _registry_column_names()}


def _entry_payload_from_persistence_record(record: dict[str, Any]) -> dict[str, Any]:
    entry = _entry_from_persistence_record(record)
    return _entry_payload_from_persistence_entry(entry, persistence_record=record)


def _entry_payload_from_persistence_entry(
    entry: RendererSkinAssetRegistryEntry,
    *,
    persistence_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = entry.to_dict()
    if persistence_record is not None:
        payload["persistence_record"] = dict(persistence_record)
    payload["owned_test_database"] = True
    payload["auto_event_emission"] = False
    payload["control_plane_only"] = True
    payload["payload_loading"] = False
    return payload


def _entry_from_persistence_record(record: dict[str, Any]) -> RendererSkinAssetRegistryEntry:
    renderer_targets = _json_load_tuple(record.get("renderer_targets_json"))
    metadata = _json_load_dict(record.get("metadata_json"))
    registered_at = str(record.get("registered_at") or "")
    skin_asset = RendererSkinAssetReference(
        skin_asset_id=str(record.get("skin_asset_id") or ""),
        source_request_id=str(record.get("source_request_id") or ""),
        source_curated_asset_id=str(record.get("source_curated_asset_id") or ""),
        dataset_uid=str(record.get("dataset_uid") or ""),
        manifest_path=str(record.get("manifest_path") or ""),
        lifecycle_status=str(record.get("lifecycle_status") or ""),
        renderer_targets=renderer_targets,
        checksum=str(record.get("checksum") or ""),
        size_bytes=int(record.get("size_bytes") or 0),
        created_at=registered_at,
    )
    return RendererSkinAssetRegistryEntry(
        registry_entry_id=str(record.get("registry_entry_id") or ""),
        skin_asset=skin_asset,
        review_required=bool(record.get("review_required")),
        registered_at=registered_at,
        updated_at=str(record.get("updated_at") or ""),
        metadata=metadata,
    )


def _json_load_tuple(value: object) -> tuple[str, ...]:
    decoded = json.loads(str(value or "[]"))
    if not isinstance(decoded, list):
        raise ValueError("Visual asset registry renderer_targets_json must decode to a list")
    return tuple(str(item) for item in decoded)


def _json_load_dict(value: object) -> dict[str, Any]:
    decoded = json.loads(str(value or "{}"))
    if not isinstance(decoded, dict):
        raise ValueError("Visual asset registry metadata_json must decode to an object")
    return dict(decoded)


def _sqlite_identifier(value: str) -> str:
    if not value or not all(char.isalnum() or char == "_" for char in value):
        raise ValueError(f"Unsafe SQLite identifier in visual asset registry persistence: {value!r}")
    return f'"{value}"'


def _drop_preview_payload(
    path: Path,
    *,
    database_exists: bool,
    owned_test_database: bool,
    table_names: set[str] | None = None,
    index_names: set[str] | None = None,
) -> dict[str, Any]:
    preview = visual_asset_registry_sqlite_ddl_preview()
    index_drop_statements = [
        f"DROP INDEX IF EXISTS {_sqlite_identifier(index_name)};"
        for index_name in reversed([_index_name(statement) for statement in preview["index_sql"]])
        if index_name
    ]
    statements = [
        *index_drop_statements,
        f"DROP TABLE IF EXISTS {_sqlite_identifier(VISUAL_ASSET_REGISTRY_TABLE_NAME)};",
        f"DROP TABLE IF EXISTS {_sqlite_identifier(OWNED_TEST_DATABASE_MARKER_TABLE)};",
    ]
    return {
        "operation": "visual_asset_registry_owned_test_drop_preview",
        "database_path": str(path),
        "database_exists": database_exists,
        "owned_test_database": owned_test_database,
        "scope": "owned_test_database_only",
        "dry_run": True,
        "destructive_execution_enabled": False,
        "creates_database_state": False,
        "mutates_database_state": False,
        "statements": statements,
        "statement_count": len(statements),
        "table_exists": VISUAL_ASSET_REGISTRY_TABLE_NAME in (table_names or set()),
        "marker_table_exists": OWNED_TEST_DATABASE_MARKER_TABLE in (table_names or set()),
        "index_names": sorted(index_names or ()),
        "auto_event_emission": False,
        "control_plane_only": True,
        "payload_loading": False,
    }


def _summary_payload(
    path: Path,
    *,
    database_exists: bool,
    owned_test_database: bool,
    table_exists: bool,
    entries: tuple[RendererSkinAssetRegistryEntry, ...],
) -> dict[str, Any]:
    summary = visual_asset_registry_summary(entries)
    summary.update(
        {
            "operation": "visual_asset_registry_summary_for_owned_test_database",
            "database_path": str(path),
            "database_exists": database_exists,
            "owned_test_database": owned_test_database,
            "table_exists": table_exists,
            "scope": "owned_test_database_only",
            "auto_event_emission": False,
            "control_plane_only": True,
            "payload_loading": False,
            "safety": {
                "control_plane_only": True,
                "payload_loading": False,
                "imports_renderer_projects": False,
                "reads_renderer_payloads": False,
                "auto_event_emission": False,
            },
        }
    )
    return summary


def _index_name(index_statement: str) -> str:
    parts = index_statement.split('"')
    if len(parts) < 2:
        return ""
    return parts[1]


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
    "read_visual_asset_registry_entry_for_owned_test_database",
    "list_visual_asset_registry_entry_payloads_for_owned_test_database",
    "read_visual_asset_registry_entry_payload_for_owned_test_database",
    "visual_asset_registry_owned_test_drop_preview",
    "visual_asset_registry_summary_for_owned_test_database",
    "write_visual_asset_registry_entry_for_owned_test_database",
]
