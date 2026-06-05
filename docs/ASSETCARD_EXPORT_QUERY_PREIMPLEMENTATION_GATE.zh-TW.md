# AssetCard Export / Query Preimplementation Gate

Updated: 2026-06-06

Status: Gate draft / docs-evidence-only / non-implementation.

Purpose: define the evidence, review, redaction, and negative-test gates that must pass before any RRKAL Core AssetCard export/query implementation begins.

This document converts `c8f3999 docs: draft asset card export query contract` into a preimplementation gate. It does not add an export API, query API, database schema, lifecycle status, renderer integration, compressor integration, Odoriba integration, or readiness promotion.

## TL;DR

Before implementing AssetCard export/query, RRKAL Core must prove that it can project reference cards without exposing payloads, private paths, secrets, renderer buffers, compressor artifacts, or downstream integration claims.

Current result:

- gate status: `draft_gate_defined`
- Core readiness gate: `partial`
- implementation authorized: no
- downstream consumer ready: no

## Gate Inputs

| Input | Required status before implementation | Current classification |
| ----- | ------------------------------------- | ---------------------- |
| AssetCard reference boundary audit | Exists and classifies safe/unsafe fields | satisfied as docs evidence |
| AssetCard export/query ADR draft | Exists and marks contract as draft/non-implementation | satisfied as docs evidence |
| Core readiness JSON | Parses as JSON and reports `partial` | required each checkpoint |
| Redaction policy | Must be explicit and testable | not implemented |
| Export/query API | Must be separately authorized | not implemented |
| Consumer contract | Must be separately reviewed | not authorized |
| Payload boundary | Must be protected by tests | not implemented |

## Preimplementation Acceptance Checklist

Do not start code implementation until every required item is either complete or explicitly accepted by `o_1` / Owner as deferred.

| Check | Requirement | Evidence needed | Current status |
| ----- | ----------- | --------------- | -------------- |
| Review authorization | Implementation scope approved by Owner and, if semantics affect cross-project consumers, `o_1` | Notion decision or repo-side OpenSpec / dispatch packet | missing |
| OpenSpec or equivalent task card | Scope, tasks, risks, acceptance criteria, and forbidden scope recorded | OpenSpec proposal or explicit L2/L3 task authorization | missing |
| Schema version | Draft schema version chosen for export payload | fixture and doc reference | draft only |
| Card kinds | `crawler_asset`, `data_manifest`, and `visual_manifest_reference` behavior decided | fixtures for each kind | missing |
| Pagination contract | Limit/cursor behavior is bounded and deterministic | tests for limit, cursor, empty result | missing |
| Evidence refs | Every card carries evidence references | fixture tests | missing |
| Redaction policy | Paths, signed URLs, credentials, and metadata are redacted by allowlist | redaction tests | missing |
| Safety flags | Cards include `control_plane_only=true`, `payload_loading=false`, and no cross-repo imports | tests and payload assertions | missing |
| Readiness gate | `--core-readiness-report-json` remains `partial` unless separately promoted | JSON parse check | required |
| No consumer claim | Docs and JSON do not imply Odoriba/displaytools/compressor can consume cards yet | forbidden wording scan | required |

## Redaction Requirements

Any future implementation must apply redaction before a card leaves Core.

| Field family | Rule | Required negative test |
| ------------ | ---- | ---------------------- |
| Local paths | Raw absolute paths must not be exported. | `C:\`, `L:\`, `K:\`, `/home/...`, and temp paths become redacted labels or are omitted. |
| Manifest paths | Treat as references, not files consumers may open directly. | `manifest_path` does not become a direct payload read instruction. |
| Signed URLs | Token-bearing query params must be stripped or classified private. | `token=`, `api_key=`, `signature=`, `X-Amz-` style values are not emitted. |
| Credential hints | Secret names and values must not be broad card data. | `api_key_env_var`, credential ids, and account hints are omitted or summarized. |
| Metadata | Use an allowlist, not pass-through. | keys containing `payload`, `secret`, `token`, `password`, `npz`, `gpu`, `buffer`, `private_path` are dropped. |
| Renderer/compressor payload | Never emit payload bytes or payload file paths. | `.npz`, tile, GPU buffer, compressor payload, and renderer project paths are absent. |
| Lifecycle labels | Do not convert `ready` into downstream consumption claims. | cards with `ready` still include evidence refs and safety flags. |

## Negative Test Plan

The first implementation slice must include these tests before being considered complete.

| Test area | Required test | Failure meaning |
| --------- | ------------- | --------------- |
| JSON mode | Export/query stdout is pure JSON. | Agent consumers cannot safely parse output. |
| Schema keys | `schema_version`, `card_kind`, `identity`, `evidence_refs`, and `safety` exist. | Contract is ambiguous. |
| Card kind coverage | Fixtures cover crawler asset, data manifest, and visual manifest reference. | One branch is unverified. |
| Bounded query | `limit` and cursor behavior are enforced. | Query can become unbounded or unstable. |
| Empty result | Empty query returns valid JSON with no fake cards. | UI/agents may hallucinate assets. |
| Redaction | Private paths, signed URLs, credential hints, and dangerous metadata are removed. | Privacy/security boundary failed. |
| Payload guard | No payload bytes, `.npz`, renderer buffers, or compressor artifacts are read or emitted. | Core boundary failed. |
| Review gate | `review_required` is preserved and never promoted to ready. | Governance boundary failed. |
| Evidence refs | Cards include current Core evidence refs. | Card can be mistaken for unsupported truth. |
| Forbidden wording | Output/docs avoid production/downstream/integration readiness claims. | Readiness overclaim. |
| Cross-repo guard | No imports from displaytools, visual-compressor, Odoriba, or other consumer repos. | Integration boundary failed. |

## Required Implementation Slice Boundaries

If implementation is later authorized, the first slice should still be narrow:

1. define an internal projection helper;
2. add fixtures for card kinds;
3. add redaction helper and tests;
4. expose one JSON diagnostic or dry-run command only if explicitly authorized;
5. keep all consumer wording neutral.

Do not combine first implementation with:

- web UI changes;
- Tk UI changes;
- database migration;
- Odoriba integration;
- renderer/compressor integration;
- lifecycle status changes;
- readiness gate promotion.

## Stop Conditions

Stop and request review if any implementation proposal requires:

- new lifecycle status or lifecycle semantics;
- new database table or migration;
- cross-repo import;
- reading payload files;
- exposing raw paths;
- asserting downstream consumer support;
- changing the Core readiness gate from `partial`;
- adding Odoriba/displaytools/compressor wording beyond neutral requester language.

## Evidence Commands For Future Implementation

Minimum checks before and after any future implementation:

```powershell
git status --short --branch
git diff --check
$db = Join-Path $env:TEMP ('rrkal_core_readiness_' + [guid]::NewGuid().ToString('N') + '.sqlite')
py -3 -B APIkeys_collection.py --db $db --core-readiness-report-json |
  py -3 -B -c "import sys,json; data=json.load(sys.stdin); print(data['schema_version']); print(data['integration_planning_gate']['status'])"
Remove-Item -LiteralPath $db -ErrorAction SilentlyContinue
```

Expected readiness output until separately reviewed:

```text
core_readiness_report.v1
partial
```

## Wording Boundary

Allowed wording:

- AssetCard export/query contract is drafted.
- Preimplementation gate is defined.
- Core may later project reference cards after review.
- Core gate remains `partial`.
- No downstream consumer is authorized yet.

Forbidden wording:

- Core is production ready.
- Core is downstream ready.
- Core is integration ready.
- Odoriba can consume Core cards now.
- AssetCard export/query API exists.
- Renderer/compressor integration is authorized.
- Payload paths are safe to expose.

## Final Classification

`c1_assetcard_export_query_preimplementation_gate_complete_l2_no_push`
