# Core Evidence and Capability Pattern Index

Updated: 2026-06-03

Purpose: provide a quick repo-side index for `n_1`, `o_1`, and the Owner when
they need to cite RRKAL Core readiness evidence, control-plane boundaries, and
the capability addressing pattern without rereading every source document.

This is an index. It does not change product behavior, promote the readiness
gate, authorize integration, or replace the referenced evidence documents.

## TL;DR

- Core evidence is clearer.
- Core gate remains `partial`.
- Capability addressing is documented as a Core pattern.
- Control-plane responsibilities are mapped.
- Notion is the coordination dashboard, not product evidence.
- GitHub commits, CI, smoke, OpenSpec validation, CLI JSON diagnostics, and
  focused tests remain the evidence layer.

## Current Core Gate Summary

| Item | Current value |
| ---- | ------------- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| Latest accepted commit | `df7a0c5` / `docs: document capability addressing pattern` |
| Latest accepted CI | GitHub Actions run `26892194478` / PASS |
| Gate | `partial` |
| Scope of this index | docs/evidence-index-only |
| Authorized integration? | No |
| Source of truth | GitHub commits, CI, smoke, OpenSpec validate, CLI JSON, focused tests |
| Coordination dashboard | Notion `Agents討論區`; dashboard only, not evidence |

Gate interpretation:

- `partial` means Core has useful control-plane evidence and diagnostics.
- `partial` does not mean Core is production-ready or integration-ready.
- Any future gate promotion requires separate evidence and review.

## Evidence Source Map

| Evidence / Pattern | File | Latest commit / CI | What it proves | What it does not prove |
| ------------------ | ---- | ------------------ | -------------- | ---------------------- |
| Core readiness evidence packet | `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md` | Packet repaired at `3c45496` / CI `26875337280` PASS; indexed under current baseline `df7a0c5` / CI `26892194478` PASS | Core readiness evidence is summarized for Notion alignment; 8 Core JSON diagnostics parse with explicit local temp DB; OpenSpec validate is checkpoint evidence; gate remains `partial`. | It does not prove Core is integration-ready, production-ready, or allowed to import renderer/compressor code. |
| Control-plane responsibility audit | `docs/CORE_CONTROL_PLANE_RESPONSIBILITY_AUDIT.zh-TW.md` | Audit refreshed at `6ff7584`; current docs baseline `df7a0c5` / CI `26892194478` PASS | Core responsibility zones are mapped: CLI, JSON diagnostics, readiness gate, scheduler evidence, review identity, lifecycle, manifest reference, lineage, Notion/GitHub evidence alignment, and L-drive residue. | It does not implement scheduler runtime, durable review queue, lifecycle state machine, renderer/compressor integration, or SkinAsset / RendererSkinAsset handling. |
| Capability addressing ADR | `docs/CAPABILITY_ADDRESSING_PATTERN.zh-TW.md` | `df7a0c5` / CI `26892194478` PASS | Existing crawler registry pattern is documented: 4-bit `CrawlerCapabilityCode`, `CrawlerCapabilityMask`, CIDR-style prefix query, `@crawler(...)`, and `CrawlerSpec.matrix_key`. | It does not create a universal framework, plugin marketplace, YAML engine, product integration path, or runtime behavior change. |
| Core JSON diagnostics | `APIkeys_collection.py` Core JSON flags; `api_launcher/core_json_diagnostics_catalog.py`; `api_launcher/core_json_diagnostic_sweep_plan.py` | Validated through current baseline `df7a0c5`; previous packet records 8/8 local-temp parse evidence | Agent-readable Core diagnostics emit parseable JSON and remain conservative. | Diagnostics are not production readiness, not live integration, and not proof of complete scheduler/review persistence. |
| OpenSpec validate | `openspec/specs/*`; archived changes inventoried by Core evidence | Current validation target: 3 specs PASS | Planning contracts validate under OpenSpec and can be cited as governance evidence. | OpenSpec inventory is not execution, and validation does not implement product behavior. |
| Focused tests | `tests/test_core_readiness_report.py`, `tests/test_core_json_diagnostics_catalog.py`, `tests/test_core_json_diagnostic_sweep_plan.py`, `tests/test_dataset_discovery.py` | Current docs baseline `df7a0c5`; previous focused runs PASS | Regression tests guard readiness gate conservatism, Core JSON parse behavior, diagnostic sweep metadata, and crawler capability addressing behavior. | Focused tests do not replace full CI, smoke, user DB validation, or integration review. |
| GitHub Actions CI | GitHub Actions run `26892194478` | PASS at `df7a0c5` | The latest accepted docs/pattern checkpoint passed project CI. | CI pass does not change the Core gate from `partial` and does not authorize integration. |
| Local temp DB requirement | `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md`; Core JSON sweep guidance | Reconfirmed by evidence packet and diagnostics practice | Automated Core JSON sweeps should pass explicit local temp `--db` to avoid cloud-drive SQLite residue. | This does not mean L-drive is unusable; it means automated diagnostics should avoid default cloud SQLite paths. |
| L-drive stale warning classification | `docs/CORE_CONTROL_PLANE_RESPONSIBILITY_AUDIT.zh-TW.md`; `docs/CORE_READINESS_EVIDENCE_PACKET.zh-TW.md` | Classified as environment residue when Git/CI/JSON/OpenSpec pass | L-drive cloud sync warnings are tracked separately from product evidence. | It does not excuse tracked Git failures, CI failures, JSON parse failures, or OpenSpec validation failures. |

## Capability Addressing Pattern Summary

The current crawler registry uses a small capability addressing pattern:

```text
source_family x transport x auth_profile x result_shape
    -> CrawlerSpec.matrix_key
    -> CrawlerCapabilityCode
    -> CrawlerCapabilityMask query
    -> selected CrawlerSpec / handler
```

Important rules:

- `CrawlerCapabilityCode` is an index, not full truth.
- `CrawlerSpec` remains the semantic source of truth.
- CIDR-style masks are for broad grouping, not user-facing policy.
- `@crawler(...)` may validate metadata and register handlers at import time.
- `@crawler(...)` must not run network requests, write files, open databases,
  read renderer payloads, or promote readiness.
- The pattern reduces scattered `if/else`; it does not eliminate all ordinary
  branching.

Canonical rule:

> 當條件樹超過 4 層，或混入超過 4 個獨立判斷維度時，停止增加 if/else。將判斷維度抽成宣告式能力矩陣，將每個能力作為切片註冊，再由 registry / resolver 明確選擇。

## Control-Plane Responsibility Summary

RRKAL Core is the control plane for asset evidence and lifecycle tracking.

Core may manage:

- registry references
- manifest references
- lifecycle vocabulary and display profiles
- `review_required` evidence
- job-status diagnostics
- asset-lineage references
- evidence packets and readiness diagnostics

Core must not absorb:

- renderer implementation
- compressor implementation
- SkinAsset / RendererSkinAsset implementation
- `.npz` or renderer payload reads
- downstream repo imports
- GPU / Qt / Taichi behavior
- cross-repo integration implementation

Current state:

- Scheduler evidence is contract/report/planning evidence, not runtime.
- Review item identity is a draft/evidence surface, not a durable review queue.
- Manifest and lineage references are control-plane references, not downstream
  consumption.
- The gate remains `partial`.

## Notion Wording Boundary

Allowed wording:

- Core evidence is clearer.
- Core gate remains `partial`.
- Capability addressing is documented as a Core pattern.
- Control-plane responsibilities are mapped.

Forbidden wording:

- Core is integration-ready.
- Core is production-ready.
- scheduler runtime is fully complete.
- durable review queue is complete.
- renderer/compressor integration is authorized.
- SkinAsset / RendererSkinAsset implementation is complete.

## What n_1 May Say

- RRKAL Core has a clearer repo-side evidence index.
- Latest accepted docs/pattern baseline is `df7a0c5`.
- Latest accepted CI for the capability addressing ADR checkpoint is
  `26892194478` PASS.
- Core readiness gate remains `partial`.
- The capability addressing pattern is documented as a Core crawler registry
  pattern.
- Control-plane responsibility boundaries are mapped and should be cited before
  integration planning discussions.
- Core JSON diagnostics and OpenSpec validation remain evidence to be checked in
  repo, not inferred from Notion text.

## What n_1 Must Not Say

- Do not say Core is production-ready.
- Do not say Core is integration-ready.
- Do not say scheduler runtime is complete.
- Do not say durable review queue persistence is complete.
- Do not say renderer/compressor integration is authorized.
- Do not say SkinAsset / RendererSkinAsset implementation is complete.
- Do not treat Notion dashboard text as stronger evidence than GitHub / CI /
  smoke / OpenSpec / CLI JSON.
- Do not turn this index into product integration authorization.

## Future Safe Slices

| Slice | Why useful | Risk | Required validation | Recommendation |
| ----- | ---------- | ---- | ------------------- | -------------- |
| Core JSON diagnostics helper extraction | Reduces repeated JSON diagnostic command metadata and keeps agent-readable checks consistent. | A helper could accidentally execute diagnostics, create SQLite state, or mix logs into JSON stdout. | Pure JSON parse tests, empty stderr tests, explicit local temp `--db`, no default L-drive DB writes. | Safe only as a bounded helper / test slice. |
| Readiness evidence table helper | Keeps readiness packet, control-plane audit, and this index from drifting. | A generated table can hide missing evidence or overclaim gate status. | Snapshot/semantic tests; gate remains `partial`; missing/blocked/contract-only surfaces stay visible. | Useful consolidation slice after docs drift recurs. |
| Capability addressing test hardening | Keeps 4-bit mask behavior, duplicate registration rejection, and semantic `CrawlerSpec` boundaries stable. | Tests can overfit current source list or make bit layout look more semantic than it is. | Registry tests for mask query, semantic dimension query, invalid dimension rejection, duplicate `source_type`, and handler signature guard. | Good small hardening slice. |
| Local temp DB precheck | Prevents false failures when automation accidentally uses cloud-drive SQLite paths for Core JSON sweeps. | A precheck could mutate or delete the wrong database path. | Owned temp path tests; no destructive operations; clear warning for L/K default paths. | Useful after design review; keep it diagnostic first. |
| OpenSpec archive evidence checker | Helps distinguish active specs, archived changes, and validation evidence. | Inventory could be mistaken for OpenSpec validate execution. | Read-only inventory tests; separate `openspec validate --all --no-interactive` command remains required. | Safe as report-only / evidence-only helper. |
| Integration planning gate draft | Prepares future review vocabulary for deciding when Core can discuss integration planning. | Easy to overclaim integration readiness or introduce cross-repo contract wording too early. | `o_1` review, OpenSpec proposal, CI, Core JSON evidence, and explicit `partial` gate until complete. | Do not start without review authorization. |

## n_1 Quick Packet

Use this wording:

```text
RRKAL Core evidence is clearer. The gate remains partial. Capability addressing
is documented as a Core crawler registry pattern at df7a0c5, and CI 26892194478
passed. Control-plane responsibilities are mapped. This is not integration
authorization, not production readiness, and not SkinAsset / RendererSkinAsset
implementation.
```

Boundary statement:

Core evidence/pattern indexing only. Gate remains `partial`. No cross-repo
integration authorized.
