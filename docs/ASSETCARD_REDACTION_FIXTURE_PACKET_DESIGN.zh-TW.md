# AssetCard Redaction Fixture Packet Design

Updated: 2026-06-06

Status: docs-only packet design / non-implementation.

Purpose: define the shape of future redaction fixture packets for RRKAL Core AssetCard export/query tests. This document turns the redaction fixture matrix into a packet format that future tests can consume after implementation is separately authorized.

This document does not add a JSON fixture driver, export/query API, database schema, lifecycle status, readiness change, renderer integration, compressor integration, Odoriba integration, or cross-repo implementation.

## TL;DR

A future AssetCard redaction fixture packet should describe:

1. an unsafe or safe input reference;
2. the candidate reference projection that Core may try to emit;
3. the fields expected to survive;
4. the fields expected to be redacted;
5. the fields expected to be rejected;
6. the required gate result, diagnostics, and verification evidence.

The packet is a test design artifact. It is not a product API and does not authorize implementation.

## Relationship To Existing Docs

| Source doc | Relationship |
| ---------- | ------------ |
| `ASSETCARD_EXPORT_QUERY_REDACTION_FIXTURE_MATRIX.zh-TW.md` | Defines fixture classes and candidate cases. This document defines the packet shape for those cases. |
| `ASSETCARD_EXPORT_QUERY_PREIMPLEMENTATION_GATE.zh-TW.md` | Defines preimplementation gate and stop conditions. |
| `ASSETCARD_EXPORT_QUERY_TOUCHPOINT_NEGATIVE_TEST_MATRIX.zh-TW.md` | Defines Core touchpoints and broader negative tests. |
| `ASSETCARD_EXPORT_QUERY_CONTRACT_ADR_DRAFT.zh-TW.md` | Defines the draft reference card direction without implementation. |

## Packet Design Goals

| Goal | Why it matters |
| ---- | -------------- |
| explicit schema | Prevents ad-hoc fixture JSON from becoming another unclear contract. |
| expected allowed fields | Makes the allowlist visible and testable. |
| expected redacted fields | Proves private paths, signed URLs, and unsafe metadata are not emitted raw. |
| expected rejected fields | Proves payload/raw fields fail closed instead of silently leaking. |
| expected gate | Keeps Core readiness conservative and visible. |
| diagnostics | Allows failing tests to explain which boundary was violated. |
| verified flag | Keeps fixture packets separate from implementation success claims. |

## Draft Packet Fields

| Field | Meaning | Required in future fixture? | Notes |
| ----- | ------- | --------------------------- | ----- |
| `schema` | Fixture packet schema id. | yes | Suggested draft value: `assetcard_redaction_fixture_packet.v1`. |
| `fixture_id` | Stable test fixture id. | yes | Should match the matrix case id where possible. |
| `fixture_class` | Positive, negative, or mixed fixture class. | yes | Examples: `allowed_reference_projection`, `private_path_redaction`, `payload_field_rejection`. |
| `input_reference` | Unsafe or safe Core-side source object sketch. | yes | Test input only; not a public export shape. |
| `candidate_projection` | Draft projection before final redaction assertion. | yes | Used to describe what a future helper would attempt to emit. |
| `expected_allowed_fields` | Field paths that may remain in output. | yes | Should be an allowlist, not a loose note. |
| `expected_redacted_fields` | Field paths or patterns that must be replaced/omitted with redaction evidence. | yes | For paths, signed URLs, credential-adjacent values. |
| `expected_rejected_fields` | Field paths or patterns that must fail closed and not appear. | yes | For payload bytes, raw buffers, private payload paths, unsafe metadata. |
| `expected_gate` | Expected Core readiness gate evidence. | yes | Must remain `partial` unless separately reviewed. |
| `diagnostics` | Human/agent-readable explanation of expected failure or redaction reasons. | yes | Should avoid product readiness overclaims. |
| `verified` | Whether the fixture has been executed by tests. | yes | For this design phase, examples use `false`. |
| `notes` | Optional extra context. | no | Use sparingly; do not put secrets or raw payload data here. |

## Draft Packet Shape

Documentation-only pseudo-JSON:

```json
{
  "schema": "assetcard_redaction_fixture_packet.v1",
  "fixture_id": "assetcard_private_windows_path",
  "fixture_class": "private_path_redaction",
  "input_reference": {
    "kind": "data_manifest_reference",
    "fields": {
      "dataset_uid": "demo-dataset",
      "manifest_path": "L:\\RRKAL_project\\state\\private\\demo.json",
      "sha256": "example-sha256"
    }
  },
  "candidate_projection": {
    "card_kind": "data_manifest",
    "identity": {
      "asset_id": "demo-dataset"
    },
    "reference": {
      "manifest_path": "L:\\RRKAL_project\\state\\private\\demo.json"
    }
  },
  "expected_allowed_fields": [
    "card_kind",
    "identity.asset_id",
    "reference.kind",
    "evidence_refs",
    "safety.control_plane_only"
  ],
  "expected_redacted_fields": [
    "reference.manifest_path"
  ],
  "expected_rejected_fields": [
    "payload",
    "raw",
    "private_path"
  ],
  "expected_gate": {
    "schema_version": "core_readiness_report.v1",
    "status": "partial"
  },
  "diagnostics": [
    {
      "code": "private_path_redacted",
      "field": "reference.manifest_path",
      "severity": "required"
    }
  ],
  "verified": false
}
```

## Positive Fixture Examples

These examples describe allowed shapes only. They do not prove implementation exists.

| Fixture id | Purpose | Required allowed fields | Expected gate |
| ---------- | ------- | ----------------------- | ------------- |
| `assetcard_allowed_crawler_asset_reference` | Minimal crawler asset reference projection. | `card_kind`, `identity.asset_id`, `identity.display_label`, `source_type_label`, `capability_summary`, `evidence_refs`, `safety.control_plane_only`. | `partial` |
| `assetcard_allowed_manifest_reference` | Minimal data manifest reference projection. | `dataset_uid`, `version`, `sha256`, `size_bytes`, `source_url_class`, `evidence_refs`, `safety.payload_loading=false`. | `partial` |
| `assetcard_allowed_visual_manifest_reference` | Minimal visual manifest reference projection. | `registry_entry_id`, `skin_asset_id`, `lifecycle_status`, `review_required`, `checksum`, `evidence_refs`, `control_plane_only`. | `partial` |

## Negative Fixture Examples

| Fixture id | Unsafe input | Expected redaction / rejection | Required diagnostic |
| ---------- | ------------ | ------------------------------ | ------------------- |
| `assetcard_private_windows_path` | `C:\`, `L:\`, or `K:\` absolute path. | Raw path absent; safe label or redaction marker present. | `private_path_redacted`. |
| `assetcard_private_posix_path` | `/home/...`, `/tmp/...`, `/mnt/...` absolute path. | Raw path absent; safe label or redaction marker present. | `private_path_redacted`. |
| `assetcard_signed_url` | URL query contains `token`, `api_key`, `signature`, or `X-Amz-`. | Sensitive query absent; host/class may remain if safe. | `signed_url_redacted`. |
| `assetcard_payload_metadata_keys` | Metadata contains `payload`, `raw`, `npz`, `gpu`, `buffer`, `private_path`. | Unsafe keys absent from output. | `unsafe_metadata_rejected`. |
| `assetcard_payload_file_trap` | Input includes path to payload-like file. | No file read; no content/extension leak if private. | `payload_access_rejected`. |
| `assetcard_missing_evidence_refs` | Candidate lacks evidence refs. | No valid card or explicit invalid fixture result. | `missing_evidence_refs`. |
| `assetcard_consumer_claim_trap` | Input hints at Odoriba/displaytools/compressor consumption. | Output uses neutral requester wording only. | `consumer_claim_rejected`. |

## Verification Semantics

`verified` must remain `false` in documentation examples. A future test runner may set or assert verification only after:

1. the fixture driver exists under reviewed scope;
2. the projection helper exists under reviewed scope;
3. redaction assertions execute;
4. Core readiness JSON still returns `core_readiness_report.v1` and `partial`;
5. no export/query API or downstream consumption claim is implied by the fixture packet itself.

## Diagnostics Vocabulary Draft

| Diagnostic code | Meaning |
| --------------- | ------- |
| `private_path_redacted` | A local or cloud-drive path was removed or replaced. |
| `signed_url_redacted` | Token-bearing URL content was stripped. |
| `credential_hint_redacted` | Credential-adjacent fields were omitted or summarized. |
| `unsafe_metadata_rejected` | Unsafe metadata keys were rejected. |
| `payload_access_rejected` | Payload-like file access was not allowed. |
| `missing_evidence_refs` | Fixture cannot produce a valid card without evidence references. |
| `review_required_preserved` | Review state remains visible and unpromoted. |
| `consumer_claim_rejected` | Downstream consumption wording was removed or rejected. |
| `gate_partial_preserved` | Core readiness gate remains `partial`. |

## Stop Conditions For Future Implementation

Stop and request review before code if fixture packet work requires:

- a JSON fixture driver;
- an export/query API;
- a DB table, migration, or schema change;
- lifecycle/status vocabulary changes;
- reading payload files;
- exposing private paths;
- importing c_2/c_3/c_4 repos;
- claiming Odoriba or another requester can consume Core cards;
- changing the Core readiness gate from `partial`.

## Readability Guard

For docs-touching tasks, do not trust PowerShell/Git terminal Chinese rendering alone. Validate actual file bytes/text with:

1. UTF-8 strict decode;
2. U+FFFD scan;
3. mojibake marker scan;
4. private-use-area marker scan;
5. changed-hunk human spot check;
6. `git diff --check`.

If terminal output looks garbled, verify the actual UTF-8 text before deciding a file is broken. If new mojibake markers or private-use-area markers increase, stop and report.

## Final Classification

`c1_assetcard_redaction_fixture_packet_design_complete_l2_no_push`
