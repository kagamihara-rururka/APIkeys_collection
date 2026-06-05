# AssetCard Export / Query Touchpoint and Negative Test Matrix

Updated: 2026-06-06

Status: docs-only audit / non-implementation.

Purpose: identify the RRKAL Core touchpoints that a future AssetCard export/query implementation would affect, and define the negative test matrix that must exist before implementation is accepted.

This document does not add an export API, query API, database schema, lifecycle status, readiness change, renderer integration, compressor integration, Odoriba integration, or cross-repo implementation.

## TL;DR

Future AssetCard export/query work must be treated as a Core projection boundary, not as a data access shortcut.

The likely implementation touchpoints are:

- source/crawler asset projection;
- manifest reference projection;
- visual manifest reference projection;
- evidence reference projection;
- redaction and allowlist rules;
- bounded query and pagination;
- CLI/JSON routing only if explicitly authorized.

The first implementation slice must fail closed: no raw paths, no secrets, no payload bytes, no renderer/compressor artifacts, no cross-repo imports, no lifecycle promotion, and no requester-consumption claim.

Core gate remains `partial`.

## Current Baseline

| Item | Value |
| ---- | ----- |
| Repo | `L:\RRKAL_project` |
| Branch | `rrkal-32e215c-recovery` |
| Baseline HEAD | `5d11203 docs: define asset card export query gate` |
| Prior ADR | `c8f3999 docs: draft asset card export query contract` |
| Current document mode | L2 docs-evidence-only |
| Implementation authorized | No |
| Core readiness gate | `partial` |

## Core Touchpoint Map

| Touchpoint | Existing file | Why it matters | Implementation risk | Required guard |
| ---------- | ------------- | -------------- | ------------------- | -------------- |
| CLI argument registration | `api_launcher/core.py` and future `cli_*` helper | A future JSON diagnostic/export command would need argparse wiring. | JSON stdout could mix with logs or banners. | Pure JSON parse test and empty stderr expectation. |
| Command detection | `api_launcher/cli_flags.py` | JSON commands need early command detection. | Missing detection may trigger default side effects. | `command_requested()` test for any future flag. |
| Crawler asset source projection | `api_launcher/crawler_assets.py` | Current `CrawlerAsset.to_dict()` has source-card fields. | May expose credential hints or local UI paths. | Redaction/allowlist before export. |
| Asset manifest projection | `api_launcher/manifests.py` | `AssetManifest` has dataset identity, source URL, checksum, size, schema fingerprint. | Raw `path` and signed `source_url` can leak private data. | Path/URL redaction tests. |
| Visual manifest reference projection | `api_launcher/visual_asset_contracts.py` | `RendererSkinAssetReference` and registry entries already model manifest references. | `manifest_path` and `renderer_targets` can be misread as runnable integration. | Rename as reference labels and declared target hints. |
| Visual registry persistence contract | `api_launcher/visual_asset_registry_persistence.py` | Owned-test persistence shape exists. | Future work might mistake it for product DB schema. | Contract-only wording and no migration in first slice. |
| Readiness evidence | `api_launcher/core_readiness_report.py` and `api_launcher/core_readiness_sections.py` | Cards should cite evidence refs and gate state. | Hiding `partial` makes cards overclaim. | Every card or result includes evidence refs and safety flags. |
| Manifest reference evidence | `api_launcher/core_manifest_reference_report.py` | Existing report keeps manifest references control-plane-only. | Future export may skip blocked surfaces. | Reference the report in fixture cards. |
| Review-required evidence | `api_launcher/core_review_required_report.py` and `api_launcher/core_review_item_contracts.py` | Review status must remain visible. | UI may promote review items to ready. | Negative test for review preservation. |
| Job/status evidence | `api_launcher/core_job_status_report.py` | Future cards may show job state. | Scheduler runtime may be implied before it exists. | Label as evidence/status, not runtime completion. |
| Tests | `tests/test_core_readiness_report.py`, `tests/test_visual_asset_contracts.py`, future AssetCard tests | Existing tests guard Core safety patterns. | New projection without tests can leak fields. | Add focused projection/redaction tests before implementation. |

## Draft Function Signatures

These are candidate signatures only. They are not implemented by this slice.

```python
def build_asset_card_reference_projection(
    *,
    card_kind: str,
    source: object,
    evidence_refs: tuple[dict[str, object], ...],
) -> dict[str, object]:
    """Draft only: project a Core reference object into a redacted AssetCard."""
```

```python
def redact_asset_card_reference_fields(
    raw: dict[str, object],
    *,
    allow_private_paths: bool = False,
) -> dict[str, object]:
    """Draft only: remove private paths, credential hints, signed URLs, and unsafe metadata."""
```

```python
def query_asset_card_reference_projections(
    *,
    card_kinds: tuple[str, ...],
    limit: int,
    cursor: str = "",
) -> dict[str, object]:
    """Draft only: bounded query envelope; no DB/API behavior exists yet."""
```

If these functions are ever implemented, they should live behind a reviewed Core helper/CLI boundary and must not import or call renderer/compressor/Odoriba code.

## Negative Test Matrix

| Test id | Scenario | Input fixture | Expected result | Protects |
| ------- | -------- | ------------- | --------------- | -------- |
| `assetcard_json_pure_stdout` | JSON command emits no human text | future CLI flag | stdout parses as JSON; stderr is empty | agent-readable contract |
| `assetcard_schema_minimum_keys` | Card has required envelope keys | one card fixture | `schema_version`, `card_kind`, `identity`, `evidence_refs`, `safety` exist | contract clarity |
| `assetcard_empty_query_no_fake_cards` | Empty query | no matching fixtures | valid JSON with empty cards and no fabricated result | no hallucinated assets |
| `assetcard_limit_enforced` | Large result set | more fixtures than limit | result count does not exceed limit | bounded query |
| `assetcard_cursor_stable` | Paginated result | stable fixture list | next page is deterministic and no duplicates appear | pagination |
| `assetcard_local_path_redacted_windows` | Windows absolute path | `C:\`, `L:\`, `K:\` paths | raw path absent or replaced by safe label | private path boundary |
| `assetcard_local_path_redacted_posix` | POSIX absolute path | `/home/user/private/file` | raw path absent or replaced by safe label | private path boundary |
| `assetcard_manifest_path_not_instruction` | Manifest path field | visual manifest fixture | field is reference label, not instruction to open payload | control-plane boundary |
| `assetcard_signed_url_redacted` | Token-bearing URL | query with `token`, `api_key`, `signature`, `X-Amz-` | sensitive query data absent | credential safety |
| `assetcard_credential_hints_omitted` | Crawler asset has credential hints | `api_key_env_var`, credential id, account hint | broad card output omits or summarizes safely | secret-adjacent fields |
| `assetcard_metadata_allowlist` | Metadata contains unsafe keys | keys with `payload`, `secret`, `token`, `password`, `npz`, `gpu`, `buffer`, `private_path` | unsafe keys absent | metadata leakage |
| `assetcard_npz_absent` | Visual metadata references `.npz` | metadata/path contains `.npz` | `.npz` reference absent from card | renderer/compressor boundary |
| `assetcard_payload_bytes_not_read` | Payload path exists | fake payload file path | projection does not open/read file | no payload access |
| `assetcard_cross_repo_import_guard` | Runtime import check | module import graph | no imports from displaytools, visual-compressor, Odoriba, c_2/c_3/c_4 repos | repo boundary |
| `assetcard_review_required_preserved` | Review item fixture | review-required source | output remains review-required; no ready promotion | governance |
| `assetcard_ready_not_consumer_claim` | Ready lifecycle fixture | visual reference with status ready | output includes evidence/safety and no requester-consumption claim | lifecycle wording |
| `assetcard_renderer_targets_declared_hint` | Visual target fixture | renderer target list | field is named/worded as declared hint | no renderer promise |
| `assetcard_evidence_refs_required` | Any card fixture | card without evidence refs | test fails | evidence linkage |
| `assetcard_gate_partial_visible` | Core readiness fixture | current readiness report | `partial` remains visible | readiness boundary |
| `assetcard_no_schema_or_lifecycle_change` | Implementation diff review | future code diff | no DB/schema/lifecycle/status files changed without review | scope control |

## Touchpoint-Specific Acceptance Notes

### Crawler Asset Projection

Use `CrawlerAsset` fields as source-card candidates, but do not export:

- raw `local_logo_path`;
- raw credential profile identifiers;
- actual API key values;
- account hints unless reviewed.

Preferred first card kind: `crawler_asset`, because it describes source access surfaces and seed inventory rather than downloaded artifacts.

### Manifest Projection

Use `AssetManifest` for identity and integrity evidence:

- `provider_id`;
- `dataset_uid`;
- `dataset_id`;
- `version`;
- `size_bytes`;
- `sha256`;
- `schema_fingerprint`;
- `created_at`.

Do not export raw `path` by default. Treat `source_url` as public only after URL redaction/classification.

### Visual Manifest Reference Projection

Use visual contracts only as control-plane references:

- `registry_entry_id`;
- `skin_asset_id`;
- `source_request_id`;
- `source_curated_asset_id`;
- `dataset_uid`;
- `lifecycle_status`;
- `review_required`;
- `checksum`;
- `size_bytes`;
- `control_plane_only`;
- `payload_loading=false`.

Do not expose `manifest_path` as a file-open instruction. Do not claim that declared renderer targets can consume the asset.

## Candidate First Implementation Boundary

If later approved, the first implementation should be smaller than the full ADR:

1. one internal projection helper;
2. no public route/API until tests pass;
3. fixture-only tests for three card kinds;
4. redaction helper with denylist and allowlist behavior;
5. no database migration;
6. no cross-repo imports;
7. no UI changes.

This document does not authorize that implementation.

## Stop Conditions For Future Work

Stop before implementation if any planned slice needs:

- new DB table or migration;
- lifecycle/status vocabulary change;
- payload file reads;
- `.npz` access;
- renderer/compressor/Odoriba import;
- raw path exposure;
- credential exposure;
- requester-consumption claims;
- Core gate promotion beyond `partial`.

## Evidence Commands

Run before accepting any future implementation:

```powershell
git status --short --branch
git diff --check
$db = Join-Path $env:TEMP ('rrkal_core_readiness_' + [guid]::NewGuid().ToString('N') + '.sqlite')
py -3 -B APIkeys_collection.py --db $db --core-readiness-report-json |
  py -3 -B -c "import sys,json; data=json.load(sys.stdin); print(data['schema_version']); print(data['integration_planning_gate']['status'])"
Remove-Item -LiteralPath $db -ErrorAction SilentlyContinue
```

Expected output until separately reviewed:

```text
core_readiness_report.v1
partial
```

## Final Classification

`c1_assetcard_export_query_touchpoint_negative_matrix_complete_l2_no_push`
