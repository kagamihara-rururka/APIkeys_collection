# Core Readiness Evidence Packet

Updated: 2026-06-03 17:15 +08:00

Purpose: repo-side evidence packet for `n_1` / Notion alignment. This packet
summarizes verified RRKAL Core control-plane readiness evidence. It is not a
product integration authorization and must not be read as renderer,
compressor, SkinAsset, RendererSkinAsset, or cross-repo implementation.

Notion is a coordination dashboard. GitHub commits, CI, smoke, OpenSpec
validation, and CLI JSON diagnostics remain the evidence layer.

## Evidence Packet v1

| Item | Evidence |
| --- | --- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| Current evidence HEAD | `7731ef0` / `docs: register core readiness evidence docs` |
| Latest Core behavior checkpoint | `030a986` / `feat(core): expose diagnostic sweep plan json` |
| Latest docs checkpoint | `7731ef0` / `docs: register core readiness evidence docs` |
| Latest accepted CI | GitHub Actions run `26874252703` / PASS / head SHA `7731ef03426a876f134124f0d617533db64fe1c5` |
| Core readiness schema | `core_readiness_report.v1` |
| Integration planning gate | `partial` |
| OpenSpec validate | PASS, 3 specs: `bounded-scheduler-core-contract`, `development-workflow`, `visual-asset-registry-persistence` |
| Core JSON diagnostics sweep | PASS with explicit local temp DB (`--db %TEMP%\...sqlite`), 8 JSON entrypoints parsed through downstream `json.load(sys.stdin)` |
| Core JSON sweep plan | `--core-json-diagnostic-sweep-plan-json` emits `core_json_diagnostic_sweep_plan.v1`; status `planned`; command count 8; `executes_commands=false`; `creates_sqlite=false` |
| Boundary | Core readiness evidence alignment only; no product behavior change, no cross-repo implementation, no renderer/compressor import, no `.npz` or renderer payload read |

## Core Evidence Summary

| Evidence area | Existing evidence | Still missing / blocked | Gate impact |
| --- | --- | --- | --- |
| Registry | 14 crawler source types in crawler registry; content registry report; dataset adapter report with provider-specific adapter inventory. | Deep adapter coverage still does not match all supported source crawler types. | `partial` |
| Lifecycle | Visual/Skin lifecycle vocabulary, display profiles, ready-event guard, lifecycle audit JSON. | No unified runtime lifecycle state machine. | `partial` |
| Manifest reference | Visual/Skin manifest reference schema contract, registry projection, manifest-reference diagnostic. | Formal user DB persistence and payload health checks remain controlled future work. | `partial` |
| Review required | Content review rules, visual `review_required` lifecycle surface, review-required report, review queue readiness report, review item identity contract draft. | Review queue persistence, persisted review item identity, resolution state, migration/rollback guard. | `partial` |
| Job status | Core job-status report, bounded scheduler plan report, scheduler job contract draft, queue DDL preview, owned-test queue helper, next-action payload, lifecycle event guard, `o_1` review gate. | No scheduler runtime, durable user DB queue, cancellation/retry runtime, or cross-repo job adapter. | `partial` |
| Asset lineage | Visual/Skin lineage fields, registry projection, manifest reference, ready event projection. | Cross-project consumption contract is not authorized or implemented. | `partial` |

## JSON Diagnostics Sweep

Verified with an explicit local temp DB and downstream JSON parse:

- `--core-readiness-report-json` -> `core_readiness_report.v1`
- `--core-review-required-report-json` -> `core_review_required_report.v1`
- `--core-review-queue-readiness-json` -> `core_review_queue_readiness_report.v1`
- `--core-job-status-report-json` -> `core_job_status_report.v1`
- `--core-manifest-reference-report-json` -> `core_manifest_reference_report.v1`
- `--core-lifecycle-audit-json` -> `core_lifecycle_audit_report.v1`
- `--core-deep-adapter-coverage-json` -> `core_deep_adapter_coverage_report.v1`
- `--core-bounded-scheduler-plan-json` -> `core_bounded_scheduler_plan_report.v1`

Use explicit local temp DB for automation / smoke / agent-readable JSON sweeps:

```powershell
$tmp = Join-Path $env:TEMP ('rrkal_core_json_sweep_' + [guid]::NewGuid().ToString() + '.sqlite')
py -3 -B APIkeys_collection.py --db $tmp --core-readiness-report-json |
  py -3 -B -c "import sys,json; json.load(sys.stdin)"
```

Do not rely on the default L-drive SQLite path for automated JSON sweeps. L-drive
cloud sync can produce transient SQLite `disk I/O error` even when the CLI JSON
path itself is valid.

## Latest Accepted Checkpoints

| Checkpoint | Commit / run | Evidence |
| --- | --- | --- |
| Temp DB operation note | `a2a937b` / CI `26849553709` PASS | Handoff records local temp DB requirement for Core JSON sweeps and the L-drive SQLite transient failure mode. |
| OpenSpec inventory in readiness report | `0ff67b6` / CI `26869976989` PASS | `--core-readiness-report-json` exposes OpenSpec inventory while keeping OpenSpec validation as checkpoint evidence. |
| Readiness gate aggregation guard | `49ef4e5` / CI `26870562033` PASS | Tests require incomplete surfaces to keep the Integration Planning Gate `partial`. |
| Readiness downstream safety guard | `cafd631` / CI `26871002397` PASS | Tests guard nested report safety flags against downstream imports, payload reads, lifecycle/schema/status changes and product behavior changes. |
| Core JSON diagnostics stderr guard | `bad262a` / CI `26871594516` PASS | Cataloged Core JSON diagnostics must emit parseable stdout JSON and empty stderr with explicit local temp `--db`. |
| Core JSON sweep repository requirement metadata | `e17edd1` / CI `26872104289` PASS | Sweep plans preserve whether each diagnostic requires repository/DB context. |
| Core JSON diagnostic sweep plan CLI | `030a986` / CI `26872795697` PASS | `--core-json-diagnostic-sweep-plan-json` exposes a non-executing command plan for the 8 Core JSON diagnostics. |
| Control-plane responsibility audit refresh | `f111bec` / CI `26873231414` PASS | `CORE_CONTROL_PLANE_RESPONSIBILITY_AUDIT.zh-TW.md` reflects the latest Core evidence checkpoints and keeps the gate `partial`. |
| Evidence packet refresh | `843fada` / CI `26873487153` PASS | `CORE_READINESS_EVIDENCE_PACKET.zh-TW.md` introduced the repo-side Notion packet. |
| Integration gate readiness refresh | `c5e4b55` / CI `26873746076` PASS | `CORE_INTEGRATION_PLANNING_GATE_READINESS.zh-TW.md` records the sweep-plan evidence and gate boundary. |
| Docs index refresh | `96b7328` / CI `26874010810` PASS | `DOCS_INDEX.zh-TW.md` routes `n_1` to this packet and the Core JSON sweep plan. |
| Docs registry refresh | `7731ef0` / CI `26874252703` PASS | `DOCS_REGISTRY.csv` registers this packet and the gate-readiness document. |

## Current Validation Snapshot

Commands verified on 2026-06-03:

- `git diff --check` -> PASS
- docs mojibake scan -> PASS after packet rewrite
- `py -3 -B -m unittest tests.test_core_readiness_report tests.test_core_json_diagnostic_sweep_plan tests.test_core_json_diagnostics_catalog` -> PASS, 22 tests
- 8 Core JSON diagnostics with explicit local temp DB -> PASS
- `npx.cmd -y @fission-ai/openspec@latest validate --all --no-interactive` -> PASS, 3 specs
- latest GitHub Actions run `26874252703` -> PASS

## n_1 Notion Alignment Packet

Status for Notion:

- RRKAL Core readiness gate remains `partial`.
- Latest repo-side evidence HEAD: `7731ef0`, CI `26874252703` PASS.
- Latest Core behavior checkpoint: `030a986`, CI `26872795697` PASS.
- Core JSON diagnostics: 8/8 parse with explicit local temp DB.
- Core JSON sweep plan CLI: `030a986` exposes a non-executing command plan; it does not run diagnostics or create DB state.
- OpenSpec validate: PASS, 3 specs.
- Boundary: Core evidence alignment only. No displaytools/compressor/SkinAsset/RendererSkinAsset integration, no `.npz` or renderer payload read, no lifecycle schema/status changes, no product readiness overclaim.

What Notion should say:

- RRKAL Core has stronger control-plane evidence and diagnostics.
- Core is still not integration-ready; the gate is `partial`.
- Future integration planning requires separate review before lifecycle schema, downstream contracts, renderer/compressor integration, or SkinAsset/RendererSkinAsset work.

What Notion should not say:

- Do not say Core is production-ready or ready for integration.
- Do not say renderer/compressor/SkinAsset work is implemented in Core.
- Do not treat the non-executing sweep plan as a live diagnostic runner.
