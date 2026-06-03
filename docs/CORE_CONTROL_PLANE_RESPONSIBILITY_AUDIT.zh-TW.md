# Core Control-Plane Responsibility Audit

最後更新：2026-06-03 16:26 +08:00

這份文件盤點 RRKAL Core control plane 目前負責什麼、不負責什麼，以及哪些證據足以支持下一步 review。它是 docs-only audit，不新增 Core 功能，不授權 renderer、compressor、SkinAsset、RendererSkinAsset 或 cross-repo integration。

一句話邊界：

> RRKAL Core 管資產生命週期、manifest reference、registry、job status、review_required 與 lineage 的控制面證據；它不讀 renderer payload，也不決定資產怎麼畫、怎麼壓縮或由哪個 renderer 消費。

## Baseline

| 欄位 | 目前證據 |
| --- | --- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| Baseline before audit | `09f8775` / `docs: align core readiness evidence summary` |
| Latest Core evidence checkpoint | `030a986` / `feat(core): expose diagnostic sweep plan json` |
| Latest accepted CI | GitHub Actions run `26872795697` / PASS |
| Core readiness gate | `partial` |
| Core JSON diagnostics | 8/8 parse with explicit local temp DB; all catalog live payload tests PASS; all remain conservative |
| OpenSpec validate | PASS, 3 specs |
| Known environment residue | `git status` may warn about archived OpenSpec path permission on L-drive; treat as cloud-drive residue unless tracked state validation fails |

## Responsibility Map

| Zone | Current files / functions | Responsibility | Inputs | Outputs | Evidence | Risk if changed | Suggested handling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CLI / entrypoints | `api_launcher/core.py`, `api_launcher/cli_flags.py`, `api_launcher/cli_core_*.py`, `api_launcher/cli_json.py` | Route Core diagnostic flags and keep JSON stdout parseable. | `argparse` flags, repository, explicit `--db`. | Pure JSON stdout for agent-readable commands. | CI `26872795697`; 8 JSON diagnostics parse via `json.load(sys.stdin)`; sweep-plan CLI parse sample PASS. | Extra banners/logs break downstream agents; direct `print(json.dumps(...))` can regress Windows encoding behavior. | `test hardening candidate`; keep helper routing thin. |
| Core JSON diagnostics | `core_readiness_report.py`, `core_json_diagnostics_catalog.py`, `core_json_diagnostic_sweep_plan.py`, `core_review_required_report.py`, `core_review_queue_readiness_report.py`, `core_job_status_report.py`, `core_manifest_reference_report.py`, `core_lifecycle_audit_report.py`, `core_deep_adapter_coverage_report.py`, `core_bounded_scheduler_plan_report.py` | Expose conservative machine-readable evidence for Core readiness areas and provide non-executing sweep metadata. | Registry reports, maturity payload, Visual/Skin contracts, scheduler/review contracts, explicit local temp DB path. | `schema_version` payloads with `status` / gate `partial`; `core_json_diagnostic_sweep_plan.v1` command plan. | `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md`; local temp DB catalog live payload tests 5/5 PASS; latest CI `26872795697` PASS. | Report text can overclaim readiness or hide missing evidence; sweep plan must not execute diagnostics or create DB state. | `docs-only clarification` plus `test hardening candidate`. |
| Readiness report generation | `build_core_readiness_report()`, `build_core_readiness_sections()` | Aggregate registry, lifecycle, manifest, review, job-status and lineage evidence into the Integration Planning Gate. | Crawler/content/dataset adapter reports, project maturity, Visual/Skin schema, scheduler/review contract drafts. | `core_readiness_report.v1`; `integration_planning_gate.status=partial`; safety flags; section builder parity test. | `26e7d63`, `feb183a`, CI `26847859365`, `26849126467`; local section-builder tests in this checkpoint. | Circular imports or missing-evidence removal can make Core look ready when it is not. | `helper extraction completed`; no gate promotion without `o_1`. |
| Scheduler evidence | `core_scheduler_contracts.py`, `core_scheduler_persistence_contract.py`, `core_bounded_scheduler_plan_report.py`, `core_job_status_report.py`, `sqlite_write_gate.py`, `frontends/tk/background_job_policies.py` | Keep scheduler planning evidence visible while proving runtime scheduler is not implemented. | Tk background policy registry, SQLite write gate profile, scheduler contract drafts, owned-test DDL preview. | `core_bounded_scheduler_plan_report.v1`, `core_job_status_report.v1`; contract-only scheduler evidence. | `b1b241d` through `26e7d63`; OpenSpec archive `e49d82b`; CI through `26847859365`. | Treating Tk thread policy or process-local SQLite gate as full scheduler; enabling auto lifecycle event. | `evidence/reporting helper candidate`; runtime scheduler, durable queue, lifecycle event emission require `o_1 review`. |
| Review item identity evidence | `core_review_item_contracts.py`, `core_review_queue_readiness_report.py`, `core_review_required_report.py` | Define a stable review item identity draft without creating a persisted review queue. | Content review rules, unknown fallback, visual `review_required` lifecycle, readiness review evidence. | `core_review_item_identity_contract_draft.v1`; queue readiness remains `partial`. | `9327669`, `feb183a`, CI `26848479833`, `26849126467`. | Confusing identity draft with queue persistence or resolution workflow. | `safe_docs_first`; persisted queue schema / resolution statuses require `o_1 review`. |
| Lifecycle / status / review semantics | `visual_asset_contracts.py`, `core_lifecycle_audit_report.py`, `core_review_required_report.py` | Preserve lifecycle vocabulary, display profiles, ready-event guards, review-required classification. | `SKIN_ASSET_LIFECYCLE_STATUSES`, display profiles, persistence schema guards. | Lifecycle audit JSON, display-safe status profiles, review-required surfaces. | `--core-lifecycle-audit-json`, `--core-review-required-report-json`; all `partial`. | Adding/renaming status or auto transition can silently change product semantics. | `requires o_1 review` for status/schema/runtime transition changes. |
| Manifest reference / lineage | `visual_asset_contracts.py`, `core_manifest_reference_report.py`, `visual_asset_event_logging.py` | Describe manifest reference, registry projection, ready-event context and lineage without reading payloads. | Download sidecar manifest contract, Visual/Skin manifest reference schema, registry entry projection. | `core_manifest_reference_report.v1`; control-plane manifest / lineage evidence. | `--core-manifest-reference-report-json`; evidence packet notes no payload reads. | Reading `.npz` or renderer payload would cross the Core boundary. | `do not touch without integration gate`; health checks must avoid payload reads. |
| OpenSpec archive / validation evidence | `api_launcher/core_openspec_evidence.py`, `openspec/specs/bounded-scheduler-core-contract/spec.md`, `openspec/specs/development-workflow/spec.md`, `openspec/specs/visual-asset-registry-persistence/spec.md` | Keep planning contracts inventoried and separate from runtime implementation. | OpenSpec specs and archived changes. | `core_openspec_evidence.v1` inventory; explicit `openspec validate --all` remains checkpoint command. | OpenSpec validate PASS in evidence packet; readiness report inventory is not validation. | Archived change paths on L-drive can produce stale permission warnings; active specs still validate. | `evidence/reporting helper completed`; use GitHub/validate evidence over cloud-drive warning. |
| Local temp DB usage | CLI `--db`, repository initialization, Core JSON sweep commands, `core_json_diagnostic_sweep_plan.py` | Keep agent-readable JSON sweeps off the cloud-drive default SQLite path. | Explicit temp SQLite path under `%TEMP%`. | Deterministic JSON parse sweep and non-executing sweep command plan. | Handoff 05:39 note; 8/8 Core JSON diagnostics pass with temp DB; `030a986` exposes `--core-json-diagnostic-sweep-plan-json`. | Default L-drive SQLite can produce transient `disk I/O error`, causing false failures. | `completed_non_executing_plan_cli`; future runtime execution remains separate. |
| Notion / GitHub evidence alignment | `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md`, `AGENT_HANDOFF`, `PROJECT_GTD`, GitHub Actions | Separate coordination dashboard from product evidence. | Notion relay requests, commits, CI, CLI JSON, OpenSpec validate. | Repo-side evidence packet for `n_1`; no Notion write by `c_1`. | Commit `09f8775`, CI `26852115783`. | Treating Notion text as source of truth can overrule verified behavior incorrectly. | `docs-only clarification`; Notion should summarize verified repo evidence only. |

## Readiness Gate Boundary Audit

Current audit result:

- Gate remains `partial`.
- No reviewed Core report or docs wording should be read as `ready_for_planning` or production-ready.
- Scheduler evidence is contract/report evidence, not runtime scheduler implementation.
- Review item identity evidence is a stable draft shape, not persisted review queue readiness.
- Visual/Skin lifecycle and manifest contracts are Core control-plane references, not renderer/compressor implementation.
- Notion is a coordination dashboard; GitHub commits, CI, CLI JSON, smoke and OpenSpec validate are product evidence.
- The L-drive archived OpenSpec permission warning is environment residue unless tracked state validation fails.

Stop and ask Owner / `o_1` before any future work that needs:

- readiness gate promotion away from `partial`
- lifecycle status / lifecycle schema change
- persisted review queue schema or resolution workflow
- durable scheduler runtime or user DB queue migration
- automatic lifecycle event emission
- cross-repo job adapter or downstream manifest consumer contract
- RendererSkinAsset / SkinAsset implementation
- `.npz` or renderer payload reads in Core

## Evidence Ledger

| Evidence | Commit / run | Meaning |
| --- | --- | --- |
| Core readiness JSON diagnostic baseline | `0ead886` / CI `26825598254` | Initial `core_readiness_report.v1`, conservative gate. |
| Bounded scheduler OpenSpec archive | `e49d82b` / CI `26847210237` | Scheduler contract moved to formal spec/archive; no runtime implementation. |
| Scheduler evidence in readiness | `26e7d63` / CI `26847859365` | Readiness report now exposes scheduler contract evidence. |
| Review item identity draft | `9327669` / CI `26848479833` | Review-required item identity draft exposed through queue readiness report. |
| Review identity in readiness | `feb183a` / CI `26849126467` | Readiness report exposes shared review identity evidence without circular import. |
| Temp DB operation note | `a2a937b` / CI `26849553709` | Handoff documents local temp DB requirement for Core JSON sweeps. |
| Evidence packet | `09f8775` / CI `26852115783` | Repo-side `n_1` packet records JSON sweep, OpenSpec validate, L-drive residue and `partial` gate. |
| Readiness section builder extraction | `1a13d21` / CI `26866374226` | `core_readiness_report.py` delegates evidence section assembly to `core_readiness_sections.py`; payload semantics and gate remain unchanged. |
| Core JSON diagnostics catalog | `d5310ad` / local + later CI coverage | `core_json_diagnostics_catalog.py` records the existing 8 diagnostic flags, schema versions and status paths as static evidence metadata. |
| Core JSON diagnostic sweep plan helper | `0605552` / local + later CI coverage | `core_json_diagnostic_sweep_plan.py` generates explicit `--db` command plans and classifies sweep DB paths. |
| Core JSON sweep path classifier CI fix | `3cb4526` / CI `26867841240` | GitHub Actions run `26867270368` exposed that POSIX `pathlib` does not infer Windows `L:` / `K:` drives; the classifier now checks raw drive strings before platform-native normalization. |
| Core readiness OpenSpec inventory | `0ff67b6` / CI `26869976989` | Readiness report now includes `openspec_evidence` inventory while still treating validation as external checkpoint evidence. |
| Core readiness gate aggregation guard | `49ef4e5` / CI `26870562033` | Tests require incomplete surfaces to keep Integration Planning Gate `partial`. |
| Core readiness downstream safety guard | `cafd631` / CI `26871002397` | Tests guard nested payload safety flags against renderer/compressor import, `.npz` read, schema/status change, scheduler runtime change and product behavior change. |
| Core JSON diagnostics stderr guard | `bad262a` / CI `26871594516` | Cataloged Core JSON diagnostics must emit parseable stdout JSON and empty stderr with explicit local temp `--db`. |
| Core JSON sweep repository requirement metadata | `e17edd1` / CI `26872104289` | Sweep plans preserve each diagnostic's repository requirement; non-repository diagnostics stay identifiable. |
| Core JSON diagnostic sweep plan CLI | `030a986` / CI `26872795697` | `--core-json-diagnostic-sweep-plan-json` emits `core_json_diagnostic_sweep_plan.v1` without executing diagnostics or creating DB state. |

## Future Safe Slice Candidates

| Candidate | Classification | Why / Boundary |
| --- | --- | --- |
| Readiness report section builder extraction | `completed_helper_extraction` | Implemented as `core_readiness_sections.py`; parity test preserves report payload semantics and gate stays `partial`. |
| Core JSON diagnostics evidence table helper | `completed_static_catalog` | Implemented as `core_json_diagnostics_catalog.py`; catalog-driven sweep validates the existing 8 entrypoints without adding CLI behavior. |
| Scheduler evidence aggregation helper | `needs_tests_first` | Could centralize scheduler evidence imports; must not bind to runtime scheduler or persistence. |
| Review item identity evidence helper | `needs_tests_first` | Could keep review queue/readiness reports aligned; must not create queue schema or resolution statuses. |
| Local temp DB precheck helper | `completed_non_executing_plan_cli` | Implemented as `core_json_diagnostic_sweep_plan.py` plus `--core-json-diagnostic-sweep-plan-json`; it plans explicit temp-DB sweeps and flags cloud-drive DB paths without executing or creating DBs. |
| OpenSpec archive evidence checker | `completed_inventory_helper` | Implemented as `core_openspec_evidence.py`; it inventories active specs / archived changes but does not execute validation or change OpenSpec files. |
| Lifecycle transition runtime | `requires_o_1_review` | Changes product semantics; not a docs-only slice. |
| Cross-repo SkinAsset / RendererSkinAsset integration | `do not touch without integration gate` | Outside `c_1` current authorization. |

## n_1 Summary Packet

What Notion should say:

- `c_1` completed a Core control-plane responsibility audit in repo docs.
- Current Core readiness gate remains `partial`.
- Evidence source remains GitHub/CI/Core JSON/OpenSpec, not Notion text.
- Latest accepted packet baseline before this audit: `09f8775`, CI `26852115783` PASS.
- Existing Core diagnostics cover registry, lifecycle, manifest reference, review-required, review queue, job status, deep adapter coverage and bounded scheduler planning; all remain conservative.

What Notion should not say:

- Do not say RRKAL Core is ready for cross-repo integration.
- Do not say scheduler runtime, durable review queue, lifecycle state machine or downstream renderer/compressor integration is implemented.
- Do not treat L-drive permission residue as product evidence failure unless tracked Git/CI/JSON validation fails.
