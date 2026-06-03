# Core Readiness Evidence Packet

最後更新：2026-06-03 16:34 +08:00

這份文件是給 `n_1` 對齊 Notion summary 使用的 repo-side evidence packet。它只整理 RRKAL Core 目前已驗證的 readiness evidence，不授權 renderer、compressor、SkinAsset、RendererSkinAsset 或 cross-repo integration。

Notion 是 coordination dashboard；GitHub commits、CI、smoke、OpenSpec validate 與 CLI JSON diagnostics 才是產品證據。

## Evidence Packet v1

| 欄位 | 目前證據 |
| --- | --- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| Baseline before packet | `a2a937b` / `docs: note temp db for core json sweeps` |
| Latest Core evidence checkpoint | `030a986` / `feat(core): expose diagnostic sweep plan json` |
| Latest docs evidence checkpoint | `f111bec` / `docs: audit core control plane responsibilities` |
| Latest accepted CI | GitHub Actions run `26873231414` / PASS |
| Core readiness schema | `core_readiness_report.v1` |
| Integration planning gate | `partial` |
| OpenSpec validate | PASS, 3 specs: `bounded-scheduler-core-contract`, `development-workflow`, `visual-asset-registry-persistence` |
| Core JSON diagnostics sweep | PASS with explicit local temp DB (`--db %TEMP%\...sqlite`), 8 JSON entrypoints parsed through downstream `json.load(sys.stdin)` |
| Core JSON sweep plan | `--core-json-diagnostic-sweep-plan-json` emits `core_json_diagnostic_sweep_plan.v1`; non-executing, no SQLite creation, command count 8 |
| L-drive residue | `git status` may warn `openspec/changes/bounded-scheduler-core-contract/specs/bounded-scheduler-core-contract/` permission denied; current evidence treats this as stale cloud-drive residue, not tracked state drift |
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

The following Core JSON entrypoints were verified with an explicit local temp DB and parse through downstream `json.load(sys.stdin)`:

- `--core-readiness-report-json`
- `--core-review-required-report-json`
- `--core-review-queue-readiness-json`
- `--core-job-status-report-json`
- `--core-manifest-reference-report-json`
- `--core-lifecycle-audit-json`
- `--core-deep-adapter-coverage-json`
- `--core-bounded-scheduler-plan-json`

Use explicit local temp DB for automation / smoke / agent-readable JSON sweeps:

```powershell
$tmp = Join-Path $env:TEMP ('rrkal_core_json_sweep_' + [guid]::NewGuid().ToString() + '.sqlite')
py -3 -B APIkeys_collection.py --db $tmp --core-readiness-report-json |
  py -3 -B -c "import sys,json; json.load(sys.stdin)"
```

Do not rely on the default L-drive SQLite path for automated JSON sweeps. L-drive cloud sync can produce transient SQLite `disk I/O error` even when the CLI JSON path itself is valid.

## Latest Accepted Checkpoints

| Checkpoint | Commit / run | Evidence |
| --- | --- | --- |
| Bounded scheduler OpenSpec archived | `e49d82b` / CI `26847210237` PASS | Scheduler contract moved from active change into formal OpenSpec spec/archive; no runtime scheduler implementation. |
| Scheduler evidence in readiness report | `26e7d63` / CI `26847859365` PASS | `--core-readiness-report-json` exposes scheduler job contract, queue DDL preview, owned-test helper, next-action payload, lifecycle event guard, and `o_1` gate evidence. |
| Review item identity contract draft | `9327669` / CI `26848479833` PASS | `--core-review-queue-readiness-json` exposes `core_review_item_identity_contract_draft.v1`. |
| Review identity evidence in readiness report | `feb183a` / CI `26849126467` PASS | `--core-readiness-report-json` exposes shared review item identity evidence without circular imports. |
| Temp DB operation note | `a2a937b` / CI `26849553709` PASS | Handoff records local temp DB requirement for Core JSON sweeps and the L-drive SQLite transient failure mode. |
| OpenSpec inventory in readiness report | `0ff67b6` / CI `26869976989` PASS | `--core-readiness-report-json` exposes OpenSpec inventory while keeping OpenSpec validation as checkpoint evidence. |
| Readiness gate aggregation guard | `49ef4e5` / CI `26870562033` PASS | Tests require incomplete surfaces to keep the Integration Planning Gate `partial`. |
| Readiness downstream safety guard | `cafd631` / CI `26871002397` PASS | Tests guard nested report safety flags against downstream imports, payload reads, lifecycle/schema/status changes and product behavior changes. |
| Core JSON diagnostics stderr guard | `bad262a` / CI `26871594516` PASS | Cataloged Core JSON diagnostics must emit parseable stdout JSON and empty stderr with explicit local temp `--db`. |
| Core JSON sweep repository requirement metadata | `e17edd1` / CI `26872104289` PASS | Sweep plans preserve whether each diagnostic requires repository/DB context. |
| Core JSON diagnostic sweep plan CLI | `030a986` / CI `26872795697` PASS | `--core-json-diagnostic-sweep-plan-json` exposes a non-executing command plan for the 8 Core JSON diagnostics. |
| Control-plane responsibility audit refresh | `f111bec` / CI `26873231414` PASS | `docs/CORE_CONTROL_PLANE_RESPONSIBILITY_AUDIT.zh-TW.md` now reflects the latest Core evidence checkpoints and keeps the gate `partial`. |

## n_1 Notion Alignment Packet

Status for Notion:

- RRKAL Core readiness gate remains `partial`.
- Latest repo-side evidence checkpoint: `f111bec`, CI `26873231414` PASS.
- Core JSON diagnostics: 8/8 parse with explicit local temp DB.
- Core JSON sweep plan CLI: `030a986` exposes a non-executing command plan; it does not run diagnostics or create DB state.
- OpenSpec validate: PASS, 3 specs.
- Environment residue: L-drive stale permission warning on archived OpenSpec path; treat as cloud-drive residue unless tracked state validation fails.
- Boundary: Core evidence alignment only. No displaytools/compressor/SkinAsset/RendererSkinAsset integration, no `.npz` or renderer payload read, no lifecycle schema/status changes, no product readiness overclaim.

Next safe Core-only action:

- Continue evidence hardening around review queue persistence design, lifecycle audit/reporting, manifest reference persistence review, or scheduler planning diagnostics only after a bounded slice is stated clearly.
- If any next slice needs lifecycle schema/status changes, cross-repo contracts, RendererSkinAsset/SkinAsset implementation, downstream imports, or integration wording, send `o_1` review first.
