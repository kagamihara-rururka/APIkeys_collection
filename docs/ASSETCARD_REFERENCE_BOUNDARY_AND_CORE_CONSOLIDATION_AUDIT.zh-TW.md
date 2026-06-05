# AssetCard Reference Boundary and Core Consolidation Audit

Updated: 2026-06-06

Scope: RRKAL Core / registry / lifecycle / manifest / evidence only.

This document is an evidence audit. It does not authorize an AssetCard export API, Odoriba integration, renderer integration, compressor integration, lifecycle schema change, database migration, or readiness promotion.

## TL;DR

RRKAL Core already has enough manifest, crawler asset, visual asset reference, review-required, lifecycle, and evidence-report structures to draft an AssetCard reference boundary. It does not yet have a verified AssetCard export interface, durable review queue, unified scheduler runtime, or cross-repo consumer contract.

The safe near-term position is:

- Core may describe asset references.
- Core may identify which fields are evidence-backed, docs-only, derived, missing, or unsafe.
- Core must not expose raw payloads, renderer buffers, compressor payloads, `.npz`, secrets, or local private paths as product-facing AssetCard data.
- Core gate remains `partial`.

## Baseline

| Item | Value |
| ---- | ----- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| HEAD at audit start | `9866780 docs: index core evidence and capability patterns` |
| Mode | L2 docs-evidence-only, commit allowed, no push |
| Gate | `partial` |
| Cross-repo integration | Not authorized |

## Branch A: Evidence-Backed AssetCard Reference Fields

These fields exist in current Core code or accepted Core evidence reports. They can be used as candidates for a future AssetCard reference, after a dedicated export contract is reviewed.

| Candidate field | Current source | Evidence status | AssetCard use | Notes |
| --------------- | -------------- | --------------- | ------------- | ----- |
| `asset_id` | `api_launcher/crawler_assets.py` `CrawlerAsset` | available | stable source/crawler asset identity | Good card key for crawler assets. |
| `display_name` | `api_launcher/crawler_assets.py` `CrawlerAsset` | available | user-facing label | Some labels should be checked for mojibake before UI reuse. |
| `provider_id` | `CrawlerAsset`, `AssetManifest` | available | provider grouping | Safe if treated as identifier, not credential. |
| `source_type` | `CrawlerAsset` | available | source pattern/category | Should map through registry/profile, not UI if/else. |
| `source_surface` | `CrawlerAsset` | available | source entry surface | Useful for provenance and review routing. |
| `access_requirement` | `CrawlerAsset` | available | credential/review hint | Do not expose secret values. |
| `endpoint_url` / `docs_url` | `CrawlerAsset` | available | public source reference | Must avoid signed URLs or token-bearing URLs. |
| `categories` | `CrawlerAsset` | available | filter tags | Safe as display metadata. |
| `geographic_scope` | `CrawlerAsset` | available | region hint | Should not replace verified bounds. |
| `maturity` / `risk_tier` / `trust_score` | `CrawlerAsset` | available | readiness/risk display | Display-only summary; not an integration gate by itself. |
| `seed_count` / `seed_summary` / `current_seed_scope` | `CrawlerAsset` | available | seed listing context | Good for source cards, not data payload cards. |
| `next_action` | `CrawlerAsset`, review reports | available | user guidance | Should come from Core/service payload, not UI inference. |
| `enabled` / `archived` / `profile_state` | `CrawlerAsset` | available | availability display | Safe if described as Core state, not source truth. |
| `dataset_uid` | `AssetManifest`, visual asset refs | available | dataset identity | Strong candidate for data/visual lineage. |
| `dataset_id` / `version` | `AssetManifest` | available | dataset versioning | Version may be absent for some sources. |
| `source_url` | `AssetManifest` | available with caution | provenance link | Unsafe if signed/tokenized; requires redaction policy. |
| `sha256` | `AssetManifest`, visual references | available | integrity evidence | Strong AssetCard evidence field. |
| `size_bytes` | `AssetManifest`, visual references | available | artifact summary | Safe as metadata. |
| `schema_fingerprint` | `AssetManifest` | available | import/schema evidence | Useful for table/manifest cards. |
| `manifest_path` | `RendererSkinAssetReference`, registry entry | available with caution | manifest reference | Should be normalized or redacted before external UI. |
| `lifecycle_status` | visual asset contracts | available as contract | state display | Contract evidence only; not runtime integration proof. |
| `lifecycle_status_display_profile` | visual registry entry | available as contract | label/tone/next_action source | Good precedent for UI-neutral payload. |
| `review_required` | visual registry entry, review reports | available | review gate display | Strong evidence for safe default behavior. |
| `renderer_targets` | visual references | available as hint | declared consumer hint | Must not be worded as verified integration support. |
| `asset_format` | visual references | available | format hint | Safe as declared format only. |
| `generated_by` / `created_at` | manifests and visual references | available | provenance timing/tool hint | Tool names are metadata, not readiness proof. |
| `source_request_id` / `source_curated_asset_id` | visual references | available as lineage | lineage connection | Contract/reference only. |
| `control_plane_only` / `payload_loading` flags | visual registry entry output | available | safety declaration | Important guardrail for future UI/API surfaces. |

## Branch B: Declared or Docs-Only Fields

These are useful for design, but they are not yet verified product export behavior.

| Field or surface | Source | Classification | Reason |
| ---------------- | ------ | -------------- | ------ |
| `RendererSkinAssetRegistryEntry` persistence | `api_launcher/visual_asset_registry_persistence.py` | contract / owned-test evidence | Persistence helpers target owned test DB flows, not a production registry migration. |
| `VISUAL_ASSET_REGISTRY_COLUMNS` | `api_launcher/visual_asset_registry_persistence.py` | schema contract | Useful shape, but not a production DB commitment. |
| Review item identity | `api_launcher/core_review_item_contracts.py` | `contract_only` | Defines identity shape without adding durable queue schema or resolution statuses. |
| Unified job scheduler evidence | `api_launcher/core_job_status_report.py` | partial evidence | Describes scheduler policy/need; does not prove durable unified scheduler runtime. |
| Skin build request/result | visual asset contracts/docs | control-plane contract | Core may record request/result metadata later, but must not implement builder. |
| `RendererSkinAssetReference` consumer readiness | visual asset docs/contracts | future-only | Reference fields exist; downstream consumer contract is not authorized. |
| AssetCard export interface | no implementation found | missing | This audit only maps possible fields; it does not add export API/class. |
| Odoriba card consumption | no implementation authorized | future-only | Odoriba must consume future Core card/export/query interface, not Core DB directly. |

## Branch C: Unsafe Fields or Surfaces

These must not be exposed as AssetCard data unless a future reviewed redaction/export policy explicitly allows it.

| Unsafe surface | Why unsafe | Safe alternative |
| -------------- | ---------- | ---------------- |
| Raw local absolute paths | Can leak workstation layout or cloud-drive internals. | Normalize to repository-relative or redacted manifest reference. |
| `AssetManifest.path` | Points to local artifact path. | Use checksum, size, manifest id, and redacted path label. |
| `manifest_path` for private locations | Can leak local layout. | Expose only after path classification. |
| `local_logo_path` | Local UI asset path, not product evidence. | Expose resolved display asset id or omit. |
| `api_key_env_var` | Credential hint can invite misuse if surfaced broadly. | Expose `credential_required=true` and provider setup action. |
| Credential values, tokens, API keys, private config | Secret material. | Never expose. |
| Signed or token-bearing URLs | May embed access credentials. | Strip query tokens or classify as private. |
| Raw payload, `.npz`, tiles, GPU buffers, renderer buffers | Violates Core control-plane boundary. | Expose manifest/checksum/reference only. |
| `renderer_targets` as proof of support | It is a declared target hint, not verified renderer compatibility. | Phrase as `declared_renderer_targets`. |
| `ready` without evidence context | Can overclaim renderability or integration readiness. | Pair with manifest, checksum, review state, and consumer contract status. |
| Arbitrary `metadata` keys | May contain payload, secret, or private path fragments. | Filter through an allowlist/redaction helper. |

## Branch D: Core Responsibility Concentration

These files are not dead code, but they are absorbing multiple responsibilities. They should be handled through bounded consolidation slices, not large rewrites.

| File | Current size signal | Responsibility concentration | Next safe consolidation slice |
| ---- | ------------------- | ---------------------------- | ----------------------------- |
| `api_launcher/core.py` | about 1,600 lines, high import count | CLI routing, JSON commands, startup behavior, command orchestration | Extract small CLI command handler helpers for JSON diagnostics without changing behavior. |
| `api_launcher/visual_asset_contracts.py` | about 850 lines | dataclasses, lifecycle labels, display profile, manifest projection, event/log context, safety filtering | Split only after tests: types, display profile, manifest projection, event payload helpers. |
| `api_launcher/visual_asset_registry_persistence.py` | about 560 lines | owned-test DB schema, serialization, write/read/list/summary/drop preview | Separate owned-test repository functions from row serialization/DDL preview helpers. |
| `api_launcher/core_readiness_sections.py` | about 320 lines | many evidence section builders | If more sections are added, split per evidence family while preserving report JSON. |
| `api_launcher/crawler_assets.py` | about 370 lines | asset dataclass, display labels, policy defaults, source profile assembly | Split display labels/config from asset assembly and repair any label mojibake. |
| `api_launcher/repository.py` | about 1,300 lines | broad repository/query/write behavior | Defer unless a concrete repository slice requires it; high blast radius. |
| `frontends/web/preview_api.py` | about 500 lines | route handlers and response construction | Defer for this task; relevant only after a reviewed AssetCard export interface exists. |

## Proposed Minimal AssetCard Reference Shape

This is a reference boundary, not an implementation request.

```json
{
  "schema_version": "asset_card_reference.v0.draft",
  "card_kind": "crawler_asset | data_manifest | visual_manifest_reference",
  "asset_id": "string",
  "display_name": "string",
  "provider_id": "string",
  "source_type": "string",
  "dataset_uid": "string",
  "manifest_ref": {
    "manifest_path_label": "redacted-or-normalized-string",
    "sha256": "string",
    "size_bytes": 0,
    "schema_fingerprint": "string"
  },
  "lifecycle": {
    "status": "planned | building | ready | failed | review_required | rejected | consumed_by_renderer",
    "display_profile": {},
    "review_required": true
  },
  "lineage": {
    "source_url": "public-or-redacted-url",
    "source_request_id": "string",
    "source_curated_asset_id": "string",
    "generated_by": "string",
    "created_at": "string"
  },
  "evidence_refs": [
    "core_readiness_report",
    "manifest_reference_report",
    "review_required_report"
  ],
  "safety": {
    "control_plane_only": true,
    "payload_loading": false,
    "cross_repo_integration_authorized": false
  }
}
```

## Odoriba Boundary

Odoriba must not read RRKAL Core databases or payload directories directly. If Odoriba later needs asset cards, the safe path is:

1. Core defines a reviewed AssetCard export/query contract.
2. Core filters/redacts unsafe fields.
3. Core exposes only manifest references and evidence summaries.
4. Odoriba consumes the card/export interface.

This audit does not authorize that interface.

## Next Safe Consolidation Slices

| Slice | Why useful | Risk | Required validation | Recommendation |
| ----- | ---------- | ---- | ------------------- | -------------- |
| AssetCard reference contract ADR | Turns this audit into a formal contract proposal. | Could overclaim export readiness. | docs drift check, o_1 review if interface semantics are proposed. | Backlog as docs/OpenSpec only. |
| Redaction allowlist helper design | Prevents accidental exposure of paths/secrets/metadata. | Behavior change if implemented too early. | unit tests for path/secret redaction. | Design first, implement in a later approved slice. |
| Visual asset contract file split plan | Reduces monolith risk. | Import churn around contract types. | focused tests for JSON payload shape. | Prepare plan before code movement. |
| Core JSON command routing extraction | Reduces `core.py` growth. | CLI compatibility risk. | CLI JSON parse tests and existing CLI flags tests. | Good small consolidation slice. |
| Review item identity evidence hardening | Clarifies review_required surfaces. | May drift into durable queue implementation. | contract-only tests; no DB migration. | Keep as evidence/contract until authorized. |
| Local temp DB precheck | Reduces L-drive SQLite lock/permission noise. | Environment-specific branching. | smoke with temp DB and docs note. | Useful if JSON sweeps remain common. |
| Crawler asset label cleanup | Removes UI/doc mojibake risk. | Touches user-facing labels. | mojibake scan and UI snapshot if needed. | Small, isolated cleanup slice. |

## Evidence References

| Evidence | File | What it proves | What it does not prove |
| -------- | ---- | -------------- | ---------------------- |
| Asset manifest contract | `api_launcher/manifests.py` | Core can represent downloaded artifact metadata and integrity. | No AssetCard export API. |
| Crawler asset model | `api_launcher/crawler_assets.py` | Core has source/seed/profile metadata suitable for card candidates. | No final UI card contract. |
| Visual asset control-plane contracts | `api_launcher/visual_asset_contracts.py` | Core has manifest-reference and lifecycle contract shapes. | No renderer/compressor integration. |
| Visual registry persistence helpers | `api_launcher/visual_asset_registry_persistence.py` | Owned-test persistence shape exists. | No production registry migration. |
| Manifest reference report | `api_launcher/core_manifest_reference_report.py` | Core explicitly reports manifest-reference readiness as partial. | No payload health or downstream consumer contract. |
| Lifecycle audit report | `api_launcher/core_lifecycle_audit_report.py` | Lifecycle vocabulary/display evidence exists. | No runtime state machine completion. |
| Review-required report | `api_launcher/core_review_required_report.py` | Review-required fallback surfaces are tracked. | No durable review queue. |
| Job status report | `api_launcher/core_job_status_report.py` | Job-status evidence is documented as partial. | No unified scheduler runtime completion. |
| Core evidence index | `docs/CORE_EVIDENCE_AND_PATTERN_INDEX.zh-TW.md` | Current reporting boundary and Notion wording guard. | No readiness upgrade. |

## Final Classification

`c1_assetcard_reference_boundary_and_core_consolidation_audit_complete_l2_no_push`
