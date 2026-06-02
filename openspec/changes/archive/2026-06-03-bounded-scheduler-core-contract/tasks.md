## 1. Contract Foundation

- [x] 1.1 Add a typed Core scheduler job contract draft that describes job identity, owner, stage, status, concurrency policy, timeout policy, retry policy, cancellation policy, write policy, review policy, evidence source, and next action.
- [x] 1.2 Add tests proving the contract has no downstream imports and does not read renderer/compressor payloads.
- [x] 1.3 Expose the contract through a JSON diagnostic or project maturity row without changing scheduler runtime behavior.

## 2. Owned-Test Or Dry-Run Persistence

- [x] 2.1 Add a dry-run queue DDL preview or owned-test-only queue table helper with explicit ownership guard.
- [x] 2.2 Add tests proving user databases are not modified unless an owned-test flag or explicit migration guard is present.
- [x] 2.3 Add tests proving process-local SQLite write gate evidence is reported as process-local, not cross-process.

## 3. Status And Policy Bridge

- [x] 3.1 Add a report that compares existing Tk background policy registry entries against scheduler contract entries.
- [x] 3.2 Add tests for cancellation, retry, timeout, review-required, and blocked-job next-action payloads.
- [x] 3.3 Keep lifecycle event emission explicit-only; add tests proving job completion does not automatically call visual lifecycle event writers.

## 4. Integration Planning Evidence

- [x] 4.1 Update `--core-bounded-scheduler-plan-json` or a successor report to include contract coverage and remaining missing evidence.
- [x] 4.2 Keep readiness conservative: do not report scheduler runtime readiness until runtime, persistence, cancellation/retry, status stream, and cross-process write evidence exists.
- [x] 4.3 Add a future `o_1` review gate before any durable queue schema, lifecycle emission change, cross-repo job adapter, or asyncio/runtime migration.

## 5. Documentation And Verification

- [x] 5.1 Update `docs/CORE_INTEGRATION_PLANNING_GATE_READINESS.zh-TW.md`, `docs/PROJECT_GTD.md`, `docs/AGENT_HANDOFF.zh-TW.md`, and `docs/DEVELOPMENT_LOG.zh-TW.md` after each implemented slice.
- [x] 5.2 Run OpenSpec validation, focused tests, changed-doc mojibake scan, `git diff --check`, pre-push smoke, and GitHub Actions before marking the change ready to archive.
- [x] 5.3 Archive the OpenSpec change only after implementation evidence and CI are complete.
