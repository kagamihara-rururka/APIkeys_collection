## Context

RRKAL Core currently has several scheduler-adjacent safeguards:

- Tk background job policy registry with bounded worker counts.
- `TkBackgroundJobStartResult` / single-flight start result contracts.
- process-local SQLite write gate.
- Core job-status and bounded-scheduler planning JSON diagnostics.

These are useful hardening surfaces, but they are not a unified scheduler runtime. The next design step is to define the Core contract that future scheduler work must satisfy before any runtime, durable queue, lifecycle emission, or UI integration is attempted.

## Goals / Non-Goals

**Goals:**

- Define Core-owned scheduler planning contract fields and evidence surfaces.
- Keep scheduler readiness conservative and agent-readable.
- Require bounded concurrency, cancellation, timeout, retry, review-required, and SQLite write policy to be explicit.
- Make future implementation testable through dry-run or owned-test evidence before user DB persistence.
- Preserve RRKAL Core as a control plane.

**Non-Goals:**

- No scheduler runtime implementation in this proposal.
- No asyncio migration.
- No durable queue schema or user DB migration.
- No lifecycle status/schema changes.
- No automatic lifecycle event emission.
- No renderer/compressor/visual payload integration.
- No imports from `RRKAL_displaytools`, `rrkal-visual-compressor`, `vis_2_dis`, or renderer payload formats.

## Decisions

### Decision 1: Contract first, runtime later

The scheduler must start as a reportable contract, not a worker runtime. Existing Tk policies and SQLite gates are input evidence. They do not become the scheduler implementation by naming alone.

Alternative considered: immediately add a global async scheduler. Rejected because it would mix UI, import, DB, crawler, and future renderer concerns before the contract is stable.

### Decision 2: Preserve lifecycle emission as explicit-only

The scheduler contract may describe lifecycle-related jobs, but it must not emit lifecycle events automatically. Any future event emission must remain an explicit workflow with review gates and tests.

Alternative considered: emit lifecycle events from job completion. Rejected until `o_1` approves status/schema and event boundary changes.

### Decision 3: Use owned-test or dry-run persistence first

If future work needs queue storage, it must begin with owned-test SQLite or dry-run DDL preview. User DB writes require a later approved migration slice.

Alternative considered: add queue tables directly to the user DB. Rejected because queue ownership, rollback, retention, and lock behavior are not yet agreed.

### Decision 4: Keep cross-repo work out of Core

Core may describe future job adapter boundaries, but this change does not add renderer/compressor job adapters or downstream imports.

Alternative considered: include displaytools/compressor job types now. Rejected because integration planning is not authorized and downstream projects are separate products.

## Risks / Trade-offs

- Fragmented evidence may be mistaken for readiness -> The contract must keep status `partial` until scheduler runtime, persistence, cancellation/retry, and status stream evidence exist.
- Local Tk policy registry may drift from future scheduler rules -> Future implementation must include a report that compares policy registry entries to scheduler contract entries.
- SQLite process-local gate does not protect cross-process writes -> The contract must call this out and require explicit cross-process strategy before durable queue writes.
- Too much contract can become another source of drift -> Keep this spec focused on fields, evidence, and safety gates; implementation details remain in bounded tasks.

## Migration Plan

1. Land this OpenSpec proposal and validate it.
2. Implement only an owned-test or dry-run scheduler status/report PoC in a later slice.
3. Add durable queue schema only after `o_1` review and migration guard approval.
4. Keep existing Tk policies and SQLite write gate behavior unchanged until a tested bridge exists.

Rollback for this proposal is simple: remove the OpenSpec change before implementation. It changes no runtime behavior.

## Open Questions

- Should the future queue use SQLite only, or remain pluggable behind a repository interface?
- What is the minimum stable job identity: source request id, asset id, plan id, route key, or a generated scheduler job id?
- Which status stream should be authoritative for UI: event log, job summary JSON, repository view, or a computed report?
- What retention policy should apply to completed/failed scheduler records?
