from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api_launcher.core_scheduler_contracts import (
    CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION,
    SCHEDULER_JOB_STATUS_VALUES,
)


CORE_SCHEDULER_QUEUE_SCHEMA_VERSION = "core_scheduler_queue_persistence_contract.v1"
CORE_SCHEDULER_QUEUE_TABLE_NAME = "core_scheduler_job_queue"


@dataclass(frozen=True)
class SchedulerQueueColumn:
    """One future scheduler queue column for dry-run migration review.

    This is deliberately a schema contract only. It lets tests and reports
    reason about queue persistence without granting Core a runtime queue, a
    user database migration, or lifecycle event emission.
    """

    name: str
    storage_type: str
    required: bool
    source: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "storage_type": self.storage_type,
            "required": self.required,
            "source": self.source,
            "description": self.description,
        }


SCHEDULER_QUEUE_COLUMNS: tuple[SchedulerQueueColumn, ...] = (
    SchedulerQueueColumn("job_id", "TEXT", True, "scheduler_job_contract.job_id", "Stable scheduler job id."),
    SchedulerQueueColumn("owner", "TEXT", True, "scheduler_job_contract.owner", "Core service or UI lane that owns the job."),
    SchedulerQueueColumn("stage", "TEXT", True, "scheduler_job_contract.stage", "Scheduler stage, separate from lifecycle status."),
    SchedulerQueueColumn("status", "TEXT", True, "scheduler_job_contract.status", "Scheduler-only status value."),
    SchedulerQueueColumn("concurrency_policy_json", "TEXT", True, "scheduler_job_contract.concurrency_policy", "Serialized lane cap and single-flight policy."),
    SchedulerQueueColumn("timeout_policy_json", "TEXT", True, "scheduler_job_contract.timeout_policy", "Serialized timeout policy."),
    SchedulerQueueColumn("retry_policy_json", "TEXT", True, "scheduler_job_contract.retry_policy", "Serialized retry policy."),
    SchedulerQueueColumn("cancellation_policy_json", "TEXT", True, "scheduler_job_contract.cancellation_policy", "Serialized cancellation policy."),
    SchedulerQueueColumn("write_policy_json", "TEXT", True, "scheduler_job_contract.write_policy", "Serialized SQLite ownership and write gate policy."),
    SchedulerQueueColumn("review_policy_json", "TEXT", True, "scheduler_job_contract.review_policy", "Serialized blocked/review-required policy."),
    SchedulerQueueColumn("evidence_source_json", "TEXT", True, "scheduler_job_contract.evidence_source", "Serialized test, CLI JSON, smoke, or event evidence."),
    SchedulerQueueColumn("next_action", "TEXT", True, "scheduler_job_contract.next_action", "Backend-provided next safe action."),
    SchedulerQueueColumn("submitted_at", "TEXT", True, "scheduler_queue.submitted_at", "UTC submit timestamp for future durable queues."),
    SchedulerQueueColumn("updated_at", "TEXT", True, "scheduler_queue.updated_at", "UTC update timestamp for future durable queues."),
    SchedulerQueueColumn("metadata_json", "TEXT", False, "scheduler_queue.metadata", "Bounded control-plane metadata only."),
)


SCHEDULER_QUEUE_INDEXES: tuple[dict[str, Any], ...] = (
    {"name": "idx_core_scheduler_job_queue_status", "columns": ("status",), "unique": False},
    {"name": "idx_core_scheduler_job_queue_owner", "columns": ("owner",), "unique": False},
    {"name": "idx_core_scheduler_job_queue_stage", "columns": ("stage",), "unique": False},
    {"name": "idx_core_scheduler_job_queue_updated", "columns": ("updated_at",), "unique": False},
)


def scheduler_queue_persistence_schema() -> dict[str, Any]:
    """Return the future scheduler queue schema contract without storage I/O."""

    return {
        "schema_version": CORE_SCHEDULER_QUEUE_SCHEMA_VERSION,
        "job_contract_schema_version": CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION,
        "table_name": CORE_SCHEDULER_QUEUE_TABLE_NAME,
        "persistence_status": "schema_contract_only",
        "primary_key": "job_id",
        "columns": [column.to_dict() for column in SCHEDULER_QUEUE_COLUMNS],
        "indexes": [
            {**index, "columns": list(index["columns"])}
            for index in SCHEDULER_QUEUE_INDEXES
        ],
        "allowed_scheduler_statuses": list(SCHEDULER_JOB_STATUS_VALUES),
        "migration_guards": {
            "create_table_automatically": False,
            "requires_explicit_owned_test_or_migration_guard": True,
            "user_database_write_allowed": False,
            "payload_columns_allowed": False,
            "auto_lifecycle_event_emission": False,
        },
        "safety": {
            "control_plane_only": True,
            "implements_scheduler_runtime": False,
            "creates_database_state": False,
            "connects_to_database": False,
            "defines_runtime_queue": False,
            "changes_lifecycle_schema": False,
            "changes_lifecycle_statuses": False,
            "enables_auto_lifecycle_events": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def scheduler_queue_sqlite_ddl_preview() -> dict[str, Any]:
    """Render reviewable SQLite DDL without connecting to SQLite or writing files."""

    schema = scheduler_queue_persistence_schema()
    table_name = str(schema["table_name"])
    primary_key = str(schema["primary_key"])
    columns = tuple(schema["columns"])
    column_lines: list[str] = []
    for column in columns:
        name = str(column["name"])
        storage_type = _sqlite_storage_type(str(column["storage_type"]))
        clauses = [_sqlite_identifier(name), storage_type]
        if name == primary_key:
            clauses.append("PRIMARY KEY")
        if bool(column["required"]):
            clauses.append("NOT NULL")
        column_lines.append(" ".join(clauses))

    table_sql = (
        f"CREATE TABLE IF NOT EXISTS {_sqlite_identifier(table_name)} (\n"
        + ",\n".join(f"    {line}" for line in column_lines)
        + "\n);"
    )
    index_sql = tuple(_sqlite_index_statement(table_name, index) for index in schema["indexes"])
    statements = (table_sql, *index_sql)

    return {
        "schema_version": schema["schema_version"],
        "preview_type": "sqlite_ddl_dry_run",
        "table_name": table_name,
        "dry_run": True,
        "persistence_status": "not_materialized",
        "creates_database_state": False,
        "connects_to_database": False,
        "requires_explicit_owned_test_or_migration_guard": True,
        "auto_lifecycle_event_emission": False,
        "table_sql": table_sql,
        "index_sql": list(index_sql),
        "statements": list(statements),
        "statement_count": len(statements),
        "column_count": len(columns),
        "index_count": len(index_sql),
        "safety": {
            **schema["safety"],
            "payload_columns_allowed": schema["migration_guards"]["payload_columns_allowed"],
            "user_database_write_allowed": schema["migration_guards"]["user_database_write_allowed"],
            "auto_lifecycle_event_emission": schema["migration_guards"]["auto_lifecycle_event_emission"],
        },
    }


def _sqlite_storage_type(storage_type: str) -> str:
    normalized = storage_type.upper()
    allowed = {"TEXT", "INTEGER", "REAL", "BLOB"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported SQLite storage type: {storage_type}")
    return normalized


def _sqlite_identifier(identifier: str) -> str:
    if not identifier or "\x00" in identifier:
        raise ValueError("Invalid SQLite identifier")
    return '"' + identifier.replace('"', '""') + '"'


def _sqlite_index_statement(table_name: str, index: dict[str, Any]) -> str:
    name = _sqlite_identifier(str(index["name"]))
    unique = "UNIQUE " if bool(index.get("unique")) else ""
    columns = ", ".join(_sqlite_identifier(str(column)) for column in index["columns"])
    return f"CREATE {unique}INDEX IF NOT EXISTS {name} ON {_sqlite_identifier(table_name)} ({columns});"


__all__ = [
    "CORE_SCHEDULER_QUEUE_SCHEMA_VERSION",
    "CORE_SCHEDULER_QUEUE_TABLE_NAME",
    "SchedulerQueueColumn",
    "SCHEDULER_QUEUE_COLUMNS",
    "SCHEDULER_QUEUE_INDEXES",
    "scheduler_queue_persistence_schema",
    "scheduler_queue_sqlite_ddl_preview",
]
