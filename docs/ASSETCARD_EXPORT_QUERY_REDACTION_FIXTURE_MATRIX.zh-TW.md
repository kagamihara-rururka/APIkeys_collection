# AssetCard Export / Query Redaction Fixture Matrix

Updated: 2026-06-06

Status: docs-only fixture design / non-implementation.

Purpose: define the redaction and negative fixture matrix that a future RRKAL Core AssetCard export/query implementation must satisfy before any public query/export surface is authorized.

This document does not add an export API, query API, database schema, lifecycle status, readiness change, renderer integration, compressor integration, Odoriba integration, or cross-repo implementation.

## TL;DR

Future AssetCard export/query work must prove that Core can return a reference projection without leaking private storage, raw payload fields, credentials, renderer/compressor payload hints, or maturity overclaims.

Current boundary:

- Core readiness gate remains `partial`.
- AssetCard export/query remains draft-only.
- No requester is authorized to consume Core cards as an integration surface yet.
- The first implementation must be fixture-driven and fail closed.

## Relationship To Existing Docs

| Source doc | How this matrix uses it |
| ---------- | ----------------------- |
| `ASSETCARD_EXPORT_QUERY_PREIMPLEMENTATION_GATE.zh-TW.md` | Defines the gate and required redaction / negative-test categories before implementation. |
| `ASSETCARD_EXPORT_QUERY_TOUCHPOINT_NEGATIVE_TEST_MATRIX.zh-TW.md` | Maps likely Core touchpoints and broad negative tests. |
| `ASSETCARD_EXPORT_QUERY_CONTRACT_ADR_DRAFT.zh-TW.md` | Defines the draft card/envelope direction without implementing it. |
| `CORE_READINESS_EVIDENCE_PACKET.zh-TW.md` | Records why Core evidence is clearer but gate remains `partial`. |
| `CORE_EVIDENCE_AND_PATTERN_INDEX.zh-TW.md` | Gives `n_1` / `o_1` / Owner a fast index for current evidence and allowed wording. |

## Fixture Design Rule

Every future AssetCard projection test should start from a deliberately unsafe fixture, then prove the projection output is safe.

Do not test only a clean happy path. The first fixture set must include private paths, signed URLs, payload-like keys, review-required status, missing evidence refs, and consumer-claim traps.

## Fixture Classification

| Fixture class | Purpose | Expected output | Risk guarded |
| ------------- | ------- | --------------- | ------------ |
| allowed reference projection | Prove a minimal card can be returned with identity, evidence refs, safety flags, and no raw storage. | Redacted card with allowed identity/reference fields only. | Under-specified card envelope. |
| private path rejected/redacted | Prove local/cloud absolute paths do not leave Core as direct paths. | Omit path, replace with safe label, or mark as redacted. | User-local path leakage. |
| payload/raw field rejected | Prove payload-ish metadata is not pass-through. | Unsafe keys absent and reason recorded in test expectation. | Payload exposure and accidental renderer/compressor coupling. |
| readiness remains partial | Prove cards do not hide the current Core gate. | `partial` remains visible in evidence/safety block. | Maturity overclaim. |
| requester cannot infer raw storage | Prove returned cards do not expose enough hints to reconstruct local storage. | No raw root, filename, extension, or private path combination that identifies payload location. | Downstream requester reverse inference. |
| review-required preserved | Prove governance state is not promoted. | Review state remains visible; no ready-style consumer claim. | Governance bypass. |
| cross-repo import absent | Prove projection is Core-only. | No imports or fixture dependencies from c_2/c_3/c_4 repos. | Integration boundary drift. |

## Candidate Fixture Matrix

| Fixture id | Input shape | Must allow | Must redact / reject | Expected gate evidence |
| ---------- | ----------- | ---------- | -------------------- | ---------------------- |
| `assetcard_allowed_crawler_asset_reference` | crawler asset with public source label, source type, capability summary, and evidence refs | source id, source type label, capability profile summary, evidence refs, `control_plane_only=true` | local icon path, credential profile internals, raw account hints | Core gate remains `partial`; no consumer claim. |
| `assetcard_allowed_manifest_reference` | data manifest with dataset id, version, checksum, size, source URL classification | dataset uid, version, checksum, size, safe source URL class | local manifest path, signed URL query, raw cache path | Card is a manifest reference, not a payload-open instruction. |
| `assetcard_allowed_visual_manifest_reference` | visual registry reference with lifecycle status and review flag | registry id, skin asset id/reference id, lifecycle status, review flag, checksum, evidence refs | manifest path, renderer project path, `.npz`, tile path, GPU buffer hint | Declared renderer target remains a hint, not integration proof. |
| `assetcard_private_windows_path` | fields containing `C:\Users\...`, `L:\RRKAL_project\state\...`, `K:\...` | redaction marker or safe storage class | full path, username, drive-root path, filename if private | Requester cannot infer raw storage. |
| `assetcard_private_posix_path` | fields containing `/home/user/...`, `/tmp/...`, `/mnt/...` | redaction marker or safe storage class | absolute path and private filename | Requester cannot infer raw storage. |
| `assetcard_signed_url` | URL with `token=`, `api_key=`, `signature=`, `X-Amz-` | host / endpoint class if safe | sensitive query params and full signed URL | Credential leakage blocked. |
| `assetcard_payload_metadata_keys` | metadata with `payload`, `raw`, `secret`, `token`, `password`, `npz`, `gpu`, `buffer`, `private_path` keys | explicitly allowlisted non-sensitive keys only | unsafe keys and nested unsafe values | No pass-through metadata. |
| `assetcard_payload_file_trap` | fixture includes path to an existing or fake payload file | identity/evidence only | file contents, file size from opening payload, file extension if private | Projection must not open payload files. |
| `assetcard_review_required_source` | card candidate has review-required status | review status, reason, evidence refs, next safe action | any ready-style consumer wording | Governance state preserved. |
| `assetcard_missing_evidence_refs` | candidate omits evidence refs | no valid card, or explicit invalid fixture result | fabricated evidence refs | Evidence linkage required. |
| `assetcard_empty_result` | query has no matching safe cards | valid empty result envelope | fabricated placeholder card | No hallucinated assets. |
| `assetcard_large_result_limit` | more candidates than requested limit | deterministic first page and cursor | unbounded output | Query remains bounded. |
| `assetcard_readiness_partial_visible` | current Core readiness JSON fixture | `core_readiness_report.v1`, gate `partial` in evidence block | wording that implies full maturity | Gate stays conservative. |
| `assetcard_consumer_claim_trap` | fixture contains consumer names or target hints | neutral requester/result wording | claims that Odoriba/displaytools/compressor can consume now | Cross-project boundary protected. |

## Minimal Expected Output Shape For Fixture Tests

Draft only. This is not an implementation contract.

```json
{
  "schema_version": "assetcard_reference_projection.fixture.v1",
  "card_kind": "crawler_asset | data_manifest | visual_manifest_reference",
  "identity": {
    "asset_id": "safe-reference-id",
    "display_label": "safe display label"
  },
  "reference": {
    "kind": "control_plane_reference",
    "payload_loading": false
  },
  "evidence_refs": [
    {
      "kind": "core_readiness_report",
      "schema_version": "core_readiness_report.v1",
      "gate_status": "partial"
    }
  ],
  "safety": {
    "control_plane_only": true,
    "private_paths_redacted": true,
    "payload_fields_removed": true,
    "cross_repo_imports": false
  }
}
```

## Redaction Assertions

| Assertion | Why it matters | Example failure |
| --------- | -------------- | --------------- |
| no absolute private paths | Prevents local/cloud workspace disclosure. | Output contains `C:\Users\...`, `L:\...`, `K:\...`, `/home/...`, or `/tmp/...`. |
| no signed URL secrets | Prevents token leakage. | Output contains `token=`, `api_key=`, `signature=`, or `X-Amz-`. |
| no payload-like keys | Prevents pass-through raw data exposure. | Output contains unsafe metadata keys such as `payload`, `raw`, `npz`, `gpu`, or `buffer`. |
| no file open side effect | Keeps Core as control plane. | Fixture test observes file reads from payload path. |
| no maturity overclaim | Keeps planning gate honest. | Output hides `partial` or implies integration authorization. |
| no consumer-specific promise | Keeps requester neutral. | Output claims a specific downstream product can use cards now. |

## Negative Fixture Acceptance Checklist

Before implementation is accepted, test coverage should prove:

1. safe reference cards can be built from allowlisted fields;
2. private path fixtures are redacted or rejected;
3. payload/raw fields are removed by policy;
4. signed URLs and credential hints are not emitted;
5. review-required state remains visible;
6. missing evidence refs fail closed;
7. empty queries do not fabricate cards;
8. bounded query limits are enforced;
9. Core readiness evidence still reports `partial`;
10. no c_2/c_3/c_4 repo import is needed.

## What This Does Not Authorize

- No export/query API.
- No DB migration or schema change.
- No lifecycle/status vocabulary change.
- No renderer/compressor/Odoriba implementation.
- No payload or private path exposure.
- No requester-consumption claim.
- No readiness promotion.

## Future Safe Slice

If Owner / `o_1` later approves implementation, the smallest safe first slice is:

1. fixture-only redaction helper tests;
2. internal projection helper behind no public route;
3. one card kind at a time;
4. strict JSON parse tests;
5. forbidden-field assertions;
6. Core readiness gate check remains `partial`.

Anything beyond that should go through a separate reviewed task card.

## Final Classification

`c1_assetcard_export_query_redaction_fixture_matrix_complete_l2_no_push`
