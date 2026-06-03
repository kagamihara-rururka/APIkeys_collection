# Core Control-Plane Responsibility Audit

Updated: 2026-06-03 21:55 +08:00

Purpose: define the RRKAL Core control-plane responsibility map, align the
current evidence ledger, and keep future Core work inside the registry /
lifecycle / manifest / review_required / job-status / asset-lineage boundary.

This is a docs-only audit. It does not authorize renderer, compressor,
SkinAsset, RendererSkinAsset, `.npz`, payload reading, lifecycle schema/status
changes, or cross-repo implementation.

## Baseline

| Item | Evidence |
| --- | --- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| Latest accepted evidence before this audit | `3c45496` / `docs: refresh core readiness evidence packet` |
| Latest accepted CI | GitHub Actions run `26875337280` / PASS / head SHA `3c45496e4c8a6cc54e0bef71764719f9889b26b4` |
| Core readiness gate | `partial` |
| Core readiness schema | `core_readiness_report.v1` |
| Core JSON diagnostics | 8/8 parse with explicit local temp DB; all remain conservative |
| OpenSpec validate | PASS, 3 specs |
| Focused tests | PASS, 22 tests: `tests.test_core_readiness_report`, `tests.test_core_json_diagnostic_sweep_plan`, `tests.test_core_json_diagnostics_catalog` |
| Pre-push smoke | PASS, 1161 tests, skipped 4, MVP demo `download_import_completed`, row_count 3 |
| Known environment residue | L-drive cloud sync can cause transient stale permission / SQLite warnings. Treat as environment residue unless tracked Git / CI / JSON validation fails. |

## Boundary Statement

RRKAL Core manages asset lifecycle evidence, manifests, registry references,
job status, review-required surfaces, and lineage references. It does not draw,
compress, render, read renderer payloads, import downstream repos, or decide
that integration is ready.

## Responsibility Map

| Zone | Current files / functions | Responsibility | Inputs | Outputs | Evidence | Risk if changed | Suggested handling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CLI / entrypoints | `api_launcher/core.py`, `api_launcher/cli_flags.py`, `api_launcher/cli_core_*.py`, `api_launcher/cli_json.py` | Route Core diagnostic flags and keep agent-readable JSON stdout pure. | `argparse` flags, repository context, explicit `--db` path. | Parseable JSON stdout for Core diagnostic commands. | CI `26875337280`; focused tests 22 PASS; JSON parse checks PASS. | Extra banners, stderr noise, or direct ad-hoc JSON printing can break downstream agents and Windows pipelines. | `test hardening candidate`; keep routing helpers thin. |
| Core JSON diagnostics | `core_readiness_report.py`, `core_readiness_sections.py`, `core_json_diagnostics_catalog.py`, `core_json_diagnostic_sweep_plan.py`, Core report modules | Expose conservative machine-readable evidence for Core readiness areas and provide a non-executing sweep plan. | Registry reports, maturity payload, lifecycle contracts, scheduler/review contracts, explicit local temp DB path. | `schema_version` payloads; gate/status remains `partial`; `core_json_diagnostic_sweep_plan.v1` status `planned`. | 8/8 diagnostics parse with explicit temp DB; `--core-json-diagnostic-sweep-plan-json` reports `executes_commands=false` and `creates_sqlite=false`. | A report can overclaim readiness or accidentally become an executing runner. | `test hardening candidate`; no behavior change without review. |
| Readiness report generation | `build_core_readiness_report()`, `build_core_readiness_sections()`, `_integration_planning_gate()` | Aggregate registry, lifecycle, manifest, review, job-status, and lineage evidence into one gate. | Section payloads and safety flags from Core-only evidence helpers. | `core_readiness_report.v1`; `integration_planning_gate.status=partial`; missing evidence is visible. | `3c45496` packet; focused readiness tests PASS. | Removing missing / blocked / contract-only evidence can fake readiness. | `pure helper extraction candidate` only when tests preserve payload semantics. |
| `CORE_READINESS_EVIDENCE_PACKET` | `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md`, `docs/DOCS_REGISTRY.csv`, `docs/DOCS_INDEX.zh-TW.md` | Provide the repo-side packet that `n_1` can summarize in Notion. | Git commits, CI run IDs, CLI JSON parse results, OpenSpec validate, smoke. | Notion-safe summary packet with clear `partial` gate and boundary text. | `3c45496`; CI `26875337280` PASS. | Stale packet evidence or mojibake can mislead cross-agent summary. | `docs-only clarification`. |
| Scheduler evidence | `core_scheduler_contracts.py`, `core_scheduler_persistence_contract.py`, `core_bounded_scheduler_plan_report.py`, `core_job_status_report.py`, `sqlite_write_gate.py`, `frontends/tk/background_job_policies.py` | Show scheduler planning evidence without claiming a runtime scheduler exists. | Tk background policy registry, SQLite write gate profile, scheduler contract drafts, owned-test DDL preview. | `core_bounded_scheduler_plan_report.v1`; `core_job_status_report.v1`; contract-only scheduler evidence. | Scheduler OpenSpec archived; readiness report contains scheduler evidence; gate still `partial`. | Mistaking Tk threads or process-local SQLite gate for a durable scheduler. | Runtime scheduler, durable queue, cancellation/retry policy, and lifecycle event emission require `requires_o_1_review`. |
| Review item identity evidence | `core_review_item_contracts.py`, `core_review_queue_readiness_report.py`, `core_review_required_report.py` | Define a stable review item identity draft without implementing a persisted review queue. | Content review rules, unknown fallback, visual `review_required` surface. | `core_review_item_identity_contract_draft.v1`; review queue readiness remains `partial`. | Review queue readiness JSON parse PASS; readiness report includes review identity evidence. | Treating identity draft as queue persistence or launch readiness. | `safe_docs_first`; persisted queue schema and resolution states require `requires_o_1_review`. |
| OpenSpec archive / validation evidence | `core_openspec_evidence.py`, `openspec/specs/*`, archived OpenSpec changes | Keep planning contracts inventoried while validation stays an explicit checkpoint command. | Active specs and archived changes on disk. | `core_openspec_evidence.v1`; OpenSpec validate command evidence. | `npx.cmd -y @fission-ai/openspec@latest validate --all --no-interactive` PASS, 3 specs. | Treating inventory as validation, or L-drive archive warning as product failure. | `evidence/reporting helper candidate`; use CI/validate over cloud-drive residue. |
| Local temp DB requirement | CLI `--db`, repository initialization, Core JSON sweep commands, `core_json_diagnostic_sweep_plan.py` | Keep automated Core JSON sweeps off the cloud-drive default SQLite path. | Explicit temp SQLite path under `%TEMP%`. | Deterministic JSON parse sweep; non-executing command plan. | 8/8 diagnostics parse with temp DB; packet and handoff record this requirement. | Default L-drive SQLite can produce transient `disk I/O error` and false failures. | `docs-only clarification`; runtime execution helper would need tests first. |
| Lifecycle / status / `review_required` semantics | `visual_asset_contracts.py`, `core_lifecycle_audit_report.py`, `core_review_required_report.py`, display profile helpers | Preserve vocabulary, status display profiles, review-required classification, and ready-event guard. | Lifecycle constants, display profiles, review rules, explicit event writer contract. | Lifecycle audit JSON and review-required JSON surfaces. | `core_lifecycle_audit_report.v1`; `core_review_required_report.v1`; gate `partial`. | Adding or renaming status, changing schema, or adding auto transitions changes product semantics. | `requires_o_1_review`. |
| Manifest reference / asset lineage | `visual_asset_contracts.py`, `core_manifest_reference_report.py`, `visual_asset_event_logging.py` | Describe manifest references, registry projection, ready-event context, and lineage without reading payloads. | Download sidecar manifest contract, Visual/Skin manifest reference schema, registry projection. | `core_manifest_reference_report.v1`; control-plane lineage evidence. | Manifest reference report JSON parse PASS; boundary tests ensure no payload read claims. | Reading `.npz`, renderer payloads, or downstream repo objects crosses the Core boundary. | `do_not_touch_without_integration_gate`. |
| GitHub / CI evidence references | GitHub Actions, pre-push smoke logs, `git status`, `git log` | Keep product evidence tied to commits, tests, smoke, and CI. | Commits, run IDs, local validation logs. | Evidence ledger rows and n_1 packet. | Latest CI `26875337280` PASS; pre-push smoke PASS. | Treating local notes or Notion text as product evidence. | `docs-only clarification`. |
| Notion handoff / dashboard references | `AGENT_HANDOFF`, `PROJECT_GTD`, Notion Agents dashboard policy | Let Notion summarize verified repo evidence without becoming source of truth. | Repo-side packet, owner routing, accepted decisions. | Notion-safe summary guidance. | Packet says what Notion should and must not say. | Notion wording can overclaim readiness if not grounded in repo evidence. | `docs-only clarification`; no Notion write by `c_1` unless requested. |
| L-drive stale permission warning classification | Git status / OpenSpec archive path / default SQLite path | Classify cloud-drive residue separately from tracked repo evidence. | L-drive cloud sync behavior, Git/CI/JSON validation results. | Environment-residue note in packet and audit. | Current `git status` clean; CI and JSON evidence pass. | Overreacting to cloud-drive residue can derail repo work; ignoring tracked failures would be unsafe. | `docs-only clarification`; stop only if tracked validation is blocked. |

## Readiness Gate Boundary Audit

Current result:

- Gate remains `partial`.
- No reviewed report or docs wording should be read as `ready_for_planning`,
  production-ready, or integration-ready.
- Cross-repo integration is not authorized.
- Scheduler evidence is contract/report/planning evidence, not runtime
  scheduler implementation.
- Review item identity evidence is a stable identity draft, not review queue
  persistence, resolution workflow, or launch readiness.
- Lifecycle and manifest contracts are Core control-plane references, not
  renderer/compressor implementation.
- Notion is a dashboard. GitHub commits, CI, smoke, OpenSpec validation, and
  CLI JSON diagnostics remain the evidence layer.

Stop and ask Owner / `o_1` before any work that needs:

- readiness gate promotion away from `partial`
- lifecycle status or lifecycle schema change
- persisted review queue schema or resolution workflow
- durable scheduler runtime or user DB queue migration
- automatic lifecycle event emission
- cross-repo job adapter or downstream manifest consumer contract
- RendererSkinAsset / SkinAsset implementation
- `.npz` or renderer payload reads in Core

## Evidence Ledger

| Evidence | Commit / run | Meaning |
| --- | --- | --- |
| Temp DB operation note | `a2a937b` / CI `26849553709` PASS | Handoff records local temp DB requirement for Core JSON sweeps and the L-drive SQLite transient failure mode. |
| OpenSpec inventory in readiness report | `0ff67b6` / CI `26869976989` PASS | Readiness report includes OpenSpec inventory while validation remains explicit checkpoint evidence. |
| Readiness gate aggregation guard | `49ef4e5` / CI `26870562033` PASS | Tests require incomplete surfaces to keep the Integration Planning Gate `partial`. |
| Readiness downstream safety guard | `cafd631` / CI `26871002397` PASS | Tests guard nested safety flags against downstream imports, payload reads, schema/status changes, and product behavior changes. |
| Core JSON diagnostics stderr guard | `bad262a` / CI `26871594516` PASS | Cataloged Core JSON diagnostics must emit parseable stdout JSON and empty stderr with explicit local temp `--db`. |
| Core JSON sweep repository requirement metadata | `e17edd1` / CI `26872104289` PASS | Sweep plans preserve each diagnostic's repository requirement. |
| Core JSON diagnostic sweep plan CLI | `030a986` / CI `26872795697` PASS | `--core-json-diagnostic-sweep-plan-json` emits a non-executing plan and does not create DB state. |
| Control-plane responsibility audit refresh | `f111bec` / CI `26873231414` PASS | Earlier audit aligned Core responsibility zones through `030a986`. |
| Evidence packet refresh | `843fada` / CI `26873487153` PASS | Repo-side Notion packet introduced. |
| Integration gate readiness refresh | `c5e4b55` / CI `26873746076` PASS | Integration gate readiness doc records sweep-plan evidence and gate boundary. |
| Docs index refresh | `96b7328` / CI `26874010810` PASS | Docs index routes `n_1` to the packet and Core JSON sweep plan. |
| Docs registry refresh | `7731ef0` / CI `26874252703` PASS | Docs registry registers the packet and gate-readiness docs. |
| Evidence packet drift repair | `3c45496` / CI `26875337280` PASS | Evidence packet was rewritten cleanly, updated to current evidence, and kept the gate `partial`. |
| Core JSON diagnostics sweep | local validation | 8/8 Core JSON diagnostics parse through downstream `json.load(sys.stdin)` with explicit temp DB. |
| Focused tests | local validation | 22 tests PASS for readiness report, sweep plan, and diagnostics catalog. |
| Pre-push smoke | local validation | 1161 tests PASS, skipped 4; MVP demo `download_import_completed`, row_count 3. |
| OpenSpec validate | local validation | 3 specs PASS. |

## Future Safe Slice Candidates

| Candidate slice | Why useful | Risk | Required validation | Classification |
| --- | --- | --- | --- | --- |
| Readiness report section builder extraction | Keeps `core_readiness_report.py` smaller and makes sections independently testable. | Payload drift could change gate semantics. | Snapshot / semantic tests for `core_readiness_report.v1`; gate remains `partial`. | `candidate_only` because helper extraction already exists; repeat only if new sections grow. |
| Core JSON diagnostics evidence table helper | Keeps CLI flag/schema/status metadata centralized. | A helper could accidentally execute commands or create DB state. | Tests proving non-executing behavior, parseable JSON, and `creates_sqlite=false`. | `needs_tests_first`. |
| Scheduler evidence aggregation helper | Reduces duplicated scheduler contract evidence across readiness/job/scheduler reports. | Could look like runtime scheduler implementation. | Report parity tests; explicit missing durable queue/runtime evidence. | `needs_tests_first`. |
| Review item identity evidence helper | Keeps review queue and readiness reports aligned. | Could be mistaken for persisted review queue readiness. | Identity shape tests; missing persistence/resolution evidence remains visible. | `safe_docs_first`. |
| Local temp DB precheck helper | Reduces false failures from L-drive SQLite during agent-readable sweeps. | Could become an executing runner or delete the wrong path. | Owned temp-path tests; no default L-drive writes; cleanup guard. | `needs_tests_first`. |
| OpenSpec archive evidence checker | Could identify archive/spec drift without using Notion as evidence. | Could treat inventory as validation. | OpenSpec validate remains separate; checker is read-only. | `safe_docs_first`. |
| Capability addressing pattern documentation | Documents future declarative/profile routing without changing handlers. | Could be mistaken for implementation plan. | Docs-only review; no product claims. | `candidate_only`. |
| Lifecycle transition runtime | Would eventually make lifecycle state changes explicit. | Changes product semantics and persistence model. | OpenSpec, o_1 review, schema migration tests. | `requires_o_1_review`. |
| Cross-repo SkinAsset / RendererSkinAsset integration | Future integration planning target. | Crosses current Core boundary. | Separate Integration Planning Gate and downstream repo review. | `not_now`. |

## n_1 Packet

What changed:

- This audit document was refreshed to clean, readable Markdown and aligned to
  the current evidence baseline through `3c45496` and CI `26875337280`.
- It maps Core control-plane responsibilities by zone and records the evidence
  ledger, readiness boundary, and future safe slices.

Evidence links:

- Latest accepted evidence packet: `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md`
- Latest CI: `26875337280` PASS
- Core JSON diagnostics: 8/8 parse with explicit temp DB
- OpenSpec validate: 3 specs PASS
- Focused tests: 22 PASS
- Pre-push smoke: 1161 tests PASS, skipped 4

What Notion should say:

- RRKAL Core has a clearer control-plane responsibility map and evidence
  ledger.
- The Core readiness gate remains `partial`.
- GitHub/CI/Core JSON/OpenSpec are evidence; Notion summarizes only verified
  repo evidence.

What Notion must not say:

- Do not say RRKAL Core is integration-ready or production-ready.
- Do not say scheduler runtime, durable review queue, lifecycle state machine,
  renderer/compressor integration, or SkinAsset/RendererSkinAsset
  implementation exists in Core.
- Do not treat L-drive residue or Notion text as stronger evidence than Git,
  CI, smoke, OpenSpec validation, or CLI JSON diagnostics.
