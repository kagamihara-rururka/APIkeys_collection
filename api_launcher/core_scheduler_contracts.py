from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION = "core_scheduler_job_contract_draft.v1"

SCHEDULER_JOB_STATUS_VALUES: tuple[str, ...] = (
    "queued",
    "running",
    "completed",
    "failed",
    "blocked",
    "review_required",
    "cancelled",
    "timed_out",
)


@dataclass(frozen=True)
class SchedulerContractField:
    """One field in the future Core scheduler job contract.

    This is a planning contract, not a queue table schema. Keeping it as
    field metadata lets reports and tests reason about the scheduler boundary
    without creating durable queue state or lifecycle events.
    """

    field_id: str
    category: str
    required: bool
    description: str
    allowed_values: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "category": self.category,
            "required": self.required,
            "description": self.description,
            "allowed_values": list(self.allowed_values),
        }


def scheduler_job_contract_fields() -> tuple[SchedulerContractField, ...]:
    return (
        SchedulerContractField(
            "job_id",
            "identity",
            True,
            "Stable scheduler job id generated at submit time.",
        ),
        SchedulerContractField(
            "owner",
            "identity",
            True,
            "Core service or UI lane that owns the job request.",
        ),
        SchedulerContractField(
            "stage",
            "state",
            True,
            "Human and agent readable job stage, separate from lifecycle status.",
        ),
        SchedulerContractField(
            "status",
            "state",
            True,
            "Scheduler-only status value; not a Visual/Skin lifecycle status.",
            SCHEDULER_JOB_STATUS_VALUES,
        ),
        SchedulerContractField(
            "concurrency_policy",
            "policy",
            True,
            "Lane cap, single-flight key, and queue admission rule.",
        ),
        SchedulerContractField(
            "timeout_policy",
            "policy",
            True,
            "Maximum runtime or idle timeout rule for the job.",
        ),
        SchedulerContractField(
            "retry_policy",
            "policy",
            True,
            "Retry count and retryable failure classes.",
        ),
        SchedulerContractField(
            "cancellation_policy",
            "policy",
            True,
            "Cancellation source, propagation rule, and cleanup expectation.",
        ),
        SchedulerContractField(
            "write_policy",
            "policy",
            True,
            "SQLite path ownership, write gate, and user DB write boundary.",
        ),
        SchedulerContractField(
            "review_policy",
            "policy",
            True,
            "How blocked, review-required, and unsupported payload outcomes stay reviewable.",
        ),
        SchedulerContractField(
            "evidence_source",
            "audit",
            True,
            "Test, CLI JSON, smoke, event, or repository evidence backing the status.",
        ),
        SchedulerContractField(
            "next_action",
            "display",
            True,
            "Backend-provided next safe action for Tk/Web/future Qt rendering.",
        ),
    )


def scheduler_job_contract_draft() -> dict[str, Any]:
    return {
        "schema_version": CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION,
        "status": "contract_only",
        "runtime_status": "not_implemented",
        "persistence_status": "not_implemented",
        "field_count": len(scheduler_job_contract_fields()),
        "fields": [field.to_dict() for field in scheduler_job_contract_fields()],
        "status_values": list(SCHEDULER_JOB_STATUS_VALUES),
        "status_scope": "scheduler_only_not_lifecycle",
        "safety": {
            "implements_scheduler_runtime": False,
            "defines_durable_queue_schema": False,
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


__all__ = [
    "CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION",
    "SCHEDULER_JOB_STATUS_VALUES",
    "SchedulerContractField",
    "scheduler_job_contract_draft",
    "scheduler_job_contract_fields",
]
