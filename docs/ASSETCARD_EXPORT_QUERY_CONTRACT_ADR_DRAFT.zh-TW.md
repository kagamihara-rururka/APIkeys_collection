# AssetCard Export / Query Contract ADR Draft

Updated: 2026-06-06

Status: Draft / non-implementation / evidence-only.

Scope: RRKAL Core registry, manifest reference, lifecycle, review-required, and evidence references.

This ADR draft proposes a future Core export/query contract shape for AssetCard references. It does not add an export API, query API, database schema, lifecycle status, renderer integration, compressor integration, Odoriba integration, or readiness promotion.

## TL;DR

RRKAL Core can already describe several asset-reference surfaces, but it should not expose them directly as product-facing cards until a reviewed export/query contract exists.

The future contract should:

- expose small reference cards, not payloads;
- distinguish crawler asset cards, manifest cards, and visual manifest reference cards;
- carry review and lifecycle evidence from Core;
- redact private paths, signed URLs, secrets, local-only UI paths, and arbitrary metadata;
- keep `control_plane_only=true` and `payload_loading=false`;
- keep the Core readiness gate at `partial` until separate evidence proves otherwise.

## Decision Context

Previous evidence:

- `docs/ASSETCARD_REFERENCE_BOUNDARY_AND_CORE_CONSOLIDATION_AUDIT.zh-TW.md`
- `docs/CORE_EVIDENCE_AND_PATTERN_INDEX.zh-TW.md`
- `api_launcher/crawler_assets.py`
- `api_launcher/manifests.py`
- `api_launcher/visual_asset_contracts.py`
- Core readiness diagnostics through `--core-readiness-report-json`

Problem:

Odoriba and future UI surfaces should not read RRKAL Core databases or payload directories directly. They need a narrow, reviewed, evidence-backed card surface. Core currently has enough evidence to draft that boundary, but not enough to claim an implemented export/query interface.

## ADR Position

RRKAL Core should eventually expose AssetCard data through a dedicated export/query contract.

The contract should be:

- reference-only;
- schema-versioned;
- explicit about card kind;
- conservative about lifecycle and review status;
- backed by Core evidence reports;
- redaction-first for paths, URLs, credentials, and metadata;
- independent of renderer/compressor implementation details.

The contract must not:

- read payload bytes;
- read `.npz`;
- import displaytools, visual-compressor, Odoriba, or renderer code;
- expose raw local paths or private credentials;
- promote lifecycle or readiness status;
- imply downstream consumption is already possible.

## Branch Scan A: Crawler Asset Reference Fields

| Field | Current source | Contract role | Export status |
| ----- | -------------- | ------------- | ------------- |
| `asset_id` | `CrawlerAsset.asset_id` | Card id for crawler/source assets | evidence-backed |
| `display_name` | `CrawlerAsset.display_name` | Human label | evidence-backed, label cleanup may be needed |
| `provider_id` | `CrawlerAsset.provider_id` | Provider grouping | evidence-backed |
| `source_type` | `CrawlerAsset.source_type` | Source-pattern category | evidence-backed |
| `source_surface` | `CrawlerAsset.source_surface` | Entry surface class | evidence-backed |
| `access_requirement` | `CrawlerAsset.access_requirement` | Credential/review hint | evidence-backed, do not expose secret values |
| `endpoint_url` | `CrawlerAsset.endpoint_url` | Public source reference | evidence-backed with URL redaction guard |
| `docs_url` | `CrawlerAsset.docs_url` | Documentation reference | evidence-backed |
| `categories` | `CrawlerAsset.categories` | Filter/display tags | evidence-backed |
| `geographic_scope` | `CrawlerAsset.geographic_scope` | Region hint | evidence-backed, not verified bounds |
| `maturity` | `CrawlerAsset.maturity` | Core maturity label | evidence-backed, not readiness gate |
| `risk_tier` | `CrawlerAsset.risk_tier` | Risk hint | evidence-backed |
| `trust_score` | `CrawlerAsset.trust_score` | Relative UI score | evidence-backed, display only |
| `seed_count` | `CrawlerAsset.seed_count` | Seed inventory count | evidence-backed |
| `seed_summary` | `CrawlerAsset.seed_summary` | Seed summary | evidence-backed |
| `current_seed_scope` | `CrawlerAsset.current_seed_scope` | Seed coverage scope | evidence-backed |
| `next_action` | `CrawlerAsset.next_action` | Backend action hint | evidence-backed |
| `enabled` / `archived` | `CrawlerAsset` | Availability state | evidence-backed |
| `profile_state` | `CrawlerAsset.profile_state` | Profile governance state | evidence-backed |

Crawler asset cards are the safest first card kind because they describe source access surfaces rather than downloaded payloads.

## Branch Scan B: Manifest Reference Fields

| Field | Current source | Contract role | Export status |
| ----- | -------------- | ------------- | ------------- |
| `provider_id` | `AssetManifest.provider_id` | Provider lineage | evidence-backed |
| `dataset_uid` | `AssetManifest.dataset_uid` | Dataset identity | evidence-backed |
| `dataset_id` | `AssetManifest.dataset_id` | Dataset source id | evidence-backed |
| `version` | `AssetManifest.version` | Dataset version | evidence-backed |
| `source_url` | `AssetManifest.source_url` | Provenance URL | requires signed/private URL redaction |
| `path` | `AssetManifest.path` | Local artifact path | unsafe as raw export |
| `size_bytes` | `AssetManifest.size_bytes` | Artifact size | evidence-backed |
| `sha256` | `AssetManifest.sha256` | Integrity evidence | evidence-backed |
| `schema_fingerprint` | `AssetManifest.schema_fingerprint` | Import/schema evidence | evidence-backed |
| `created_at` | `AssetManifest.created_at` | Timestamp | evidence-backed |
| `metadata` | `AssetManifest.metadata` | Extra metadata | requires allowlist/redaction |

Manifest cards should expose checksums, size, schema fingerprint, and normalized manifest reference labels. They should not expose raw local paths by default.

## Branch Scan C: Visual Manifest Reference Fields

| Field | Current source | Contract role | Export status |
| ----- | -------------- | ------------- | ------------- |
| `registry_entry_id` | `RendererSkinAssetRegistryEntry` | Visual registry row id | contract evidence |
| `skin_asset_id` | `RendererSkinAssetReference` | External skin reference id | contract evidence |
| `source_request_id` | `RendererSkinAssetReference` | Build request lineage | contract evidence |
| `source_curated_asset_id` | `RendererSkinAssetReference` | Curated source lineage | contract evidence |
| `dataset_uid` | `RendererSkinAssetReference` | Dataset lineage | contract evidence |
| `manifest_path` | `RendererSkinAssetReference` | Manifest reference | requires normalization/redaction |
| `lifecycle_status` | `RendererSkinAssetReference` | Lifecycle display/filter | contract evidence |
| `lifecycle_status_display_profile` | `RendererSkinAssetReference.to_dict()` | UI-neutral label/tone/action | contract evidence |
| `renderer_targets` | `RendererSkinAssetReference` | Declared target hints | contract evidence, not verified integration |
| `asset_format` | `RendererSkinAssetReference` | Format hint | contract evidence |
| `checksum` | `RendererSkinAssetReference` | Integrity evidence | contract evidence |
| `size_bytes` | `RendererSkinAssetReference` | Size metadata | contract evidence |
| `generated_by` | `RendererSkinAssetReference` | Builder/tool provenance | contract evidence |
| `review_required` | `RendererSkinAssetRegistryEntry` | Review gate | contract evidence |
| `control_plane_only` | `RendererSkinAssetRegistryEntry.to_dict()` | Safety flag | evidence-backed |
| `payload_loading` | `RendererSkinAssetRegistryEntry.to_dict()` | Safety flag | evidence-backed false |

Visual manifest reference cards are useful only as Core control-plane references. They do not prove that any renderer can consume the referenced asset.

## Branch Scan D: Readiness / Evidence References

| Evidence ref | Source | Contract use | Current status |
| ------------ | ------ | ------------ | -------------- |
| `core_readiness_report.v1` | `--core-readiness-report-json` | Global gate and safety flags | `partial` |
| `core_manifest_reference_report.v1` | `--core-manifest-reference-report-json` | Manifest reference evidence | `partial` |
| `core_lifecycle_audit_report.v1` | `--core-lifecycle-audit-report-json` | Lifecycle vocabulary evidence | `partial` |
| `core_review_required_report.v1` | `--core-review-required-report-json` | Review-required evidence | `partial` |
| `core_job_status_report.v1` | `--core-job-status-report-json` | Job-status evidence | `partial` |
| `core_review_queue_readiness_report.v1` | `--core-review-queue-readiness-json` | Review queue gap evidence | `partial` |

AssetCard export/query should include evidence references, not just display fields. A card without evidence references is easier to misread as a raw data object or completed integration surface.

## Branch Scan E: Unsafe Payload / Private-Path Fields

| Unsafe field or surface | Rule |
| ----------------------- | ---- |
| Raw local path fields | Do not expose as external card data. Use normalized labels or omit. |
| `AssetManifest.path` | Treat as private unless explicitly classified safe. |
| `manifest_path` | Treat as a manifest reference, not a file that consumers may open directly. |
| `local_logo_path` | Local UI-only field; omit from external card data. |
| `api_key_env_var` / `credential_profile_id` / `account_hint` | Do not expose as broad UI/API card data. Use credential-required boolean and setup action. |
| Signed URLs or token-bearing URLs | Strip sensitive query values or mark private. |
| `metadata` | Use an allowlist. Drop keys that imply payload, secret, token, password, private path, renderer buffer, or compressor payload. |
| `.npz`, tiles, renderer buffers, GPU buffers | Never expose through Core AssetCard contract. |
| `renderer_targets` | Phrase as declared target hints only. |
| `ready` lifecycle status | Display with evidence context; do not imply downstream consumption. |

## Branch Scan F: Future Odoriba Query Path

Future path, boundary wording only:

```text
Odoriba request
  -> reviewed Core AssetCard query/export endpoint
  -> Core redaction and evidence projection
  -> AssetCard reference projection
  -> downstream requester consumes returned Card
```

This path is not implemented and is not authorized by this ADR draft.

Odoriba must not:

- query Core SQLite tables directly;
- read Core payload directories;
- read `.npz`;
- infer renderer readiness from Core lifecycle labels alone;
- bypass Core redaction rules.

## Draft Contract Shape

This shape is a draft reference contract. It is intentionally not code.

```json
{
  "schema_version": "asset_card_export_query_contract.v0.draft",
  "query": {
    "card_kinds": ["crawler_asset", "data_manifest", "visual_manifest_reference"],
    "filters": {
      "provider_id": "optional",
      "dataset_uid": "optional",
      "source_type": "optional",
      "lifecycle_status": "optional",
      "review_required": "optional"
    },
    "pagination": {
      "limit": 50,
      "cursor": "optional"
    }
  },
  "card": {
    "card_id": "string",
    "card_kind": "crawler_asset | data_manifest | visual_manifest_reference",
    "display": {
      "title": "string",
      "subtitle": "string",
      "tone": "neutral | ready | review | blocked | planned"
    },
    "identity": {
      "asset_id": "string",
      "provider_id": "string",
      "dataset_uid": "string",
      "source_type": "string"
    },
    "manifest_ref": {
      "manifest_ref_id": "string",
      "manifest_path_label": "redacted-or-normalized-string",
      "sha256": "string",
      "size_bytes": 0,
      "schema_fingerprint": "string"
    },
    "lifecycle": {
      "status": "string",
      "review_required": true,
      "next_action": "string",
      "display_profile": {}
    },
    "lineage": {
      "source_url_label": "public-or-redacted-url",
      "source_request_id": "string",
      "source_curated_asset_id": "string",
      "generated_by": "string",
      "created_at": "string"
    },
    "evidence_refs": [
      {
        "schema_version": "core_readiness_report.v1",
        "status": "partial"
      }
    ],
    "safety": {
      "control_plane_only": true,
      "payload_loading": false,
      "private_paths_redacted": true,
      "secrets_redacted": true,
      "cross_repo_imports": false
    }
  }
}
```

## Contract Rules

1. Query results must be paginated and bounded.
2. Cards must be display/reference objects, not payload objects.
3. Every card must carry `schema_version`, `card_kind`, `evidence_refs`, and `safety`.
4. Raw paths and credentials must be removed or redacted before export.
5. `review_required` must not be promoted to ready by display code.
6. `renderer_targets` must remain declared hints until a separate consumer contract exists.
7. Core evidence status must remain visible; do not hide `partial` evidence behind card labels.
8. UI consumers must not reconstruct business rules from field names; they should render backend display/profile fields.

## Minimal Future Validation Before Implementation

Before any code slice implements this ADR, require:

- o_1 review;
- OpenSpec proposal or explicit owner authorization;
- fixture cards for all three card kinds;
- redaction tests for paths, signed URLs, credential fields, and metadata;
- JSON parse tests for export/query mode;
- pagination/limit tests;
- evidence ref presence tests;
- negative tests proving no payload reads and no cross-repo imports.

## Non-Goals

- No export API in this slice.
- No query API in this slice.
- No database migration.
- No lifecycle/status change.
- No renderer/compressor/Odoriba import.
- No payload read.
- No readiness gate promotion.
- No downstream consumption claim.

## Final Boundary

This ADR draft documents a future Core AssetCard export/query contract boundary. It is a planning artifact backed by current Core evidence. The Core gate remains `partial`.

Final classification for this slice:

`c1_assetcard_export_query_contract_adr_draft_complete_l2_no_push`
