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


@dataclass(frozen=True)
class SchedulerNextActionPayload:
    """One UI-neutral next-action payload for a scheduler outcome.

    These examples define the report vocabulary only.  They are not runtime
    transitions and do not enqueue, cancel, retry, or complete jobs.
    """

    scenario: str
    scheduler_status: str
    outcome_bucket: str
    next_action: str
    display_tone: str
    user_action_required: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "scheduler_status": self.scheduler_status,
            "outcome_bucket": self.outcome_bucket,
            "next_action": self.next_action,
            "display_tone": self.display_tone,
            "user_action_required": self.user_action_required,
            "description": self.description,
        }


@dataclass(frozen=True)
class SchedulerO1ReviewGate:
    """One future scheduler change that requires explicit `o_1` review."""

    gate_id: str
    blocked_change: str
    required_before: str
    rationale: str
    safe_without_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "blocked_change": self.blocked_change,
            "required_before": self.required_before,
            "rationale": self.rationale,
            "safe_without_review": self.safe_without_review,
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


def scheduler_o1_review_gates() -> tuple[SchedulerO1ReviewGate, ...]:
    return (
        SchedulerO1ReviewGate(
            gate_id="durable_queue_schema",
            blocked_change="creating_or_migrating_core_scheduler_job_queue_in_user_databases",
            required_before="any_durable_queue_schema_or_migration",
            rationale="Queue persistence can affect user data and rollback guarantees.",
        ),
        SchedulerO1ReviewGate(
            gate_id="lifecycle_event_emission_change",
            blocked_change="automatic_visual_lifecycle_event_emission_from_scheduler_jobs",
            required_before="any_scheduler_to_visual_lifecycle_event_binding",
            rationale="Scheduler status is not a Visual/Skin lifecycle transition.",
        ),
        SchedulerO1ReviewGate(
            gate_id="cross_repo_job_adapter",
            blocked_change="renderer_or_compressor_job_adapter_contract",
            required_before="any_cross_repo_scheduler_or_builder_job_adapter",
            rationale="Core must not absorb displaytools or compressor runtime responsibilities.",
        ),
        SchedulerO1ReviewGate(
            gate_id="asyncio_runtime_migration",
            blocked_change="asyncio_or_runtime_scheduler_rewrite",
            required_before="any_asyncio_runtime_migration_or_worker_pool_replacement",
            rationale="Runtime scheduler changes can affect Tk/Web behavior, SQLite locks, and cancellation semantics.",
        ),
    )


def scheduler_o1_review_gate_contract() -> dict[str, Any]:
    gates = scheduler_o1_review_gates()
    return {
        "schema_version": "core_scheduler_o1_review_gate_contract.v1",
        "status": "contract_only",
        "gate_status": "required_before_future_runtime_work",
        "gate_count": len(gates),
        "required_gate_ids": [gate.gate_id for gate in gates],
        "gates": [gate.to_dict() for gate in gates],
        "safety": {
            "implements_scheduler_runtime": False,
            "changes_scheduler_schema": False,
            "changes_lifecycle_schema": False,
            "changes_lifecycle_statuses": False,
            "emits_lifecycle_events": False,
            "enables_auto_lifecycle_events": False,
            "adds_cross_repo_job_adapter": False,
            "starts_asyncio_runtime_migration": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


def scheduler_next_action_payloads() -> tuple[SchedulerNextActionPayload, ...]:
    return (
        SchedulerNextActionPayload(
            scenario="cancelled_job",
            scheduler_status="cancelled",
            outcome_bucket="cancelled",
            next_action="inspect_cancellation_reason_or_requeue",
            display_tone="muted",
            user_action_required=False,
            description="Job was cancelled explicitly; keep reason visible before any requeue.",
        ),
        SchedulerNextActionPayload(
            scenario="retryable_failure",
            scheduler_status="failed",
            outcome_bucket="retryable",
            next_action="retry_when_policy_allows",
            display_tone="warning",
            user_action_required=False,
            description="Failure is retryable only when the retry policy still allows another attempt.",
        ),
        SchedulerNextActionPayload(
            scenario="timed_out_job",
            scheduler_status="timed_out",
            outcome_bucket="timeout",
            next_action="review_timeout_policy_or_retry",
            display_tone="warning",
            user_action_required=True,
            description="Timeout requires policy review before requeueing or widening the timeout.",
        ),
        SchedulerNextActionPayload(
            scenario="review_required_job",
            scheduler_status="review_required",
            outcome_bucket="review_required",
            next_action="open_review_queue_before_continuing",
            display_tone="review",
            user_action_required=True,
            description="Review-required jobs must stay reviewable and cannot be promoted to ready implicitly.",
        ),
        SchedulerNextActionPayload(
            scenario="blocked_job",
            scheduler_status="blocked",
            outcome_bucket="blocked",
            next_action="review_blocked_job_reason_before_retry",
            display_tone="blocked",
            user_action_required=True,
            description="Blocked jobs need an explicit reason and user/agent decision before retry.",
        ),
    )


def scheduler_next_action_payload_contract() -> dict[str, Any]:
    payloads = scheduler_next_action_payloads()
    return {
        "schema_version": "core_scheduler_next_action_payload_contract.v1",
        "status": "contract_only",
        "payload_count": len(payloads),
        "payloads": [payload.to_dict() for payload in payloads],
        "required_scenarios": [payload.scenario for payload in payloads],
        "safety": {
            "implements_scheduler_runtime": False,
            "changes_scheduler_schema": False,
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


def scheduler_lifecycle_event_emission_guard_contract(
    *,
    explicit_event_writer: str = "log_visual_asset_ready_registry_entry",
) -> dict[str, Any]:
    """Describe the scheduler-to-lifecycle event boundary without emitting events.

    A future scheduler may mark its own jobs completed, failed, or blocked, but
    those scheduler statuses are not Visual/Skin lifecycle transitions.  This
    guard keeps lifecycle event emission as a separate explicit workflow until
    an `o_1` review authorizes any tighter coupling.
    """

    return {
        "schema_version": "core_scheduler_lifecycle_event_emission_guard.v1",
        "status": "contract_only",
        "scope": "scheduler_completion_does_not_emit_visual_lifecycle_events",
        "scheduler_status_scope": "scheduler_only_not_lifecycle",
        "guarded_scheduler_statuses": (
            "completed",
            "failed",
            "blocked",
            "review_required",
            "cancelled",
            "timed_out",
        ),
        "completed_job_policy": {
            "scheduler_status": "completed",
            "auto_emit_lifecycle_event": False,
            "requires_explicit_event_writer": True,
            "explicit_event_writer": explicit_event_writer,
            "next_action": "call_explicit_visual_ready_event_writer_only_after_review",
        },
        "forbidden_implicit_call_sites": (
            "scheduler_runtime_completion",
            "queue_status_update",
            "owned_test_queue_helper",
            "download_import_completion",
        ),
        "o1_review_required_for": (
            "automatic_lifecycle_event_emission",
            "scheduler_status_to_visual_lifecycle_transition_binding",
            "cross_repo_builder_job_adapter",
        ),
        "safety": {
            "implements_scheduler_runtime": False,
            "changes_scheduler_schema": False,
            "changes_lifecycle_schema": False,
            "changes_lifecycle_statuses": False,
            "emits_lifecycle_events": False,
            "enables_auto_lifecycle_events": False,
            "calls_visual_asset_ready_writer": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


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
    "SchedulerNextActionPayload",
    "SchedulerO1ReviewGate",
    "scheduler_job_contract_draft",
    "scheduler_job_contract_fields",
    "scheduler_lifecycle_event_emission_guard_contract",
    "scheduler_next_action_payload_contract",
    "scheduler_next_action_payloads",
    "scheduler_o1_review_gate_contract",
    "scheduler_o1_review_gates",
]
