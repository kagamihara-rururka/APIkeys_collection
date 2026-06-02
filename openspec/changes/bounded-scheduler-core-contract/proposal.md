## Why

RRKAL Core now has evidence for Tk background job caps, process-local SQLite write gating, job-status diagnostics, and a bounded scheduler planning report. Those pieces are useful but still fragmented, so future work could accidentally treat local hardening as a unified scheduler runtime.

This change defines the bounded scheduler Core contract before implementation. It keeps the work in RRKAL Core, preserves current lifecycle/schema boundaries, and gives future slices a safe acceptance target for job status, concurrency limits, cancellation/retry policy, durable queue decisions, and review-required fallbacks.

## What Changes

- Add a new OpenSpec capability for RRKAL Core bounded scheduler contract planning.
- Define the allowed scheduler contract surfaces: job identity, job status, queue limits, retry/cancel/timeout policy, SQLite write serialization, and agent-readable report payloads.
- Define what remains out of scope: scheduler runtime implementation, asyncio migration, durable queue persistence, automatic lifecycle event emission, cross-repo job adapters, renderer/compressor imports, and payload reads.
- Require conservative readiness reporting: existing local Tk guards and SQLite write gates are evidence, not proof that unified scheduler runtime is ready.
- Require future implementation slices to start with owned-test or dry-run evidence before user DB persistence or UI flows.

## Capabilities

### New Capabilities

- `bounded-scheduler-core-contract`: Defines how RRKAL Core may plan and later implement a bounded job scheduler contract without changing lifecycle schema, importing downstream repos, or treating local hardening as production scheduler runtime.

### Modified Capabilities

- None.

## Impact

- Affected code areas for future implementation:
  - `api_launcher/core_bounded_scheduler_plan_report.py`
  - `api_launcher/core_job_status_report.py`
  - `api_launcher/sqlite_write_gate.py`
  - `frontends/tk/background_job_policies.py`
  - future Core scheduler contract modules, if approved
- Affected docs:
  - `docs/CORE_INTEGRATION_PLANNING_GATE_READINESS.zh-TW.md`
  - `docs/PROJECT_GTD.md`
  - `docs/AGENT_HANDOFF.zh-TW.md`
  - `docs/DEVELOPMENT_LOG.zh-TW.md`
- No new runtime dependency is expected for this proposal.
- No UI behavior, renderer/compressor integration, or lifecycle status/schema change is included in this change.
