# Capability Addressing Pattern

Last updated: 2026-06-03

## TL;DR

RRKAL Core already uses a small capability-addressing pattern in
`api_launcher/crawlers/registry.py`: each crawler is registered through
`@crawler(...)`, preserved as a semantic `CrawlerSpec`, and also assigned a
4-bit `CrawlerCapabilityCode` so diagnostics can query broad capability slices
with `CrawlerCapabilityMask`.

This is a routing/index pattern, not a product-readiness claim and not a
universal plugin framework. `CrawlerSpec` remains the semantic source of truth.
The 4-bit code is only a compact index for asking questions such as "which
crawlers are JSON catalog-like sources?" without adding source-type branches to
UI, CLI, diagnostics, or resolver code.

Canonical rule:

> 當條件樹超過 4 層，或混入超過 4 個獨立判斷維度時，停止增加 if/else。將判斷維度抽成宣告式能力矩陣，將每個能力作為切片註冊，再由 registry / resolver 明確選擇。

## Problem: Condition Tree Depth > 4

Crawler dispatch started as a practical `source_type -> handler` problem. As the
project grew, each crawler also gained independent dimensions:

- source family: catalog search, index scan, capabilities endpoint
- transport: JSON, HTML, XML, text
- auth profile: public, optional API key, credential-required
- result shape: dataset list, file links, layer list, resource links
- seed scope: entry listing or paginated catalog

A two-way or three-way `if/else` can still be readable. Once a path mixes four or
more independent dimensions, the condition tree becomes hard to audit. It also
tempts every caller to rebuild the same private routing knowledge:

- UI asks source-type questions to choose labels.
- CLI asks source-type questions to group diagnostics.
- resolver asks source-type questions to decide review paths.
- tests need duplicated source-type fixtures.

That is where the registry should take over. The code can still use normal
Python handlers, but the dimensions must be registered once and queried through
the registry.

## Pattern: Capability Matrix Slicing

The pattern is:

```text
semantic dimensions
    -> CrawlerSpec.matrix_key
    -> CrawlerCapabilityCode
    -> CrawlerCapabilityMask query
    -> selected CrawlerSpec / handler
```

Current dimensions:

```text
source_family x transport x auth_profile x result_shape
```

`CrawlerSpec.matrix_key` keeps the full semantic tuple. The capability code
compresses that tuple into a small fixed-width address. `CrawlerCapabilityMask`
then lets diagnostics query groups without naming every source type.

The current implementation deliberately uses only four bits:

```text
CAPABILITY_CODE_WIDTH = 4
```

This keeps the address readable and prevents the first implementation from
turning into a hidden DSL.

## Implementation Anatomy From Current Crawler Registry

| Component | File | Role | Notes |
| --------- | ---- | ---- | ----- |
| `CrawlerCapabilityCode` | `api_launcher/crawlers/registry.py` | Compact 4-bit address for a crawler capability cell. | Exposes `bits`, `binary`, and `to_dict()`. It validates width but does not replace semantic metadata. |
| `CrawlerCapabilityMask` | `api_launcher/crawlers/registry.py` | Query object for matching one or more capability addresses. | Supports explicit `(bits, mask)` and `from_prefix(...)` CIDR-style prefix queries. |
| `CAPABILITY_CODE_WIDTH` | `api_launcher/crawlers/registry.py` | Fixed address width. | Currently `4`; changing this is a schema/design change and should be reviewed. |
| `capability_code_for(...)` | `api_launcher/crawlers/registry.py` | Converts semantic dimensions into the compact address. | ORs registered dimension bit maps and rejects unsupported dimension values. |
| `crawler(...)` | `api_launcher/crawlers/registry.py` | Decorator registration boundary for crawler handlers. | Normalizes fields, rejects duplicate `source_type`, validates `seed_scope`, validates shared handler signature, computes capability code, then stores `CrawlerSpec`. |
| `CrawlerSpec.matrix_key` | `api_launcher/crawlers/registry.py` | Semantic four-dimensional key. | Returns `(source_family, transport, auth_profile, result_shape)` and remains readable in reports. |
| `crawler_specs_by_capability_mask(...)` | `api_launcher/crawlers/registry.py` | Mask query read side. | Returns matching specs; callers still receive full `CrawlerSpec`, not just bits. |
| `crawler_specs_by_dims(...)` | `api_launcher/crawlers/registry.py` | Semantic partial-dimension query read side. | Preferred when the caller needs explicit dimension matching instead of bit masks. |
| Registry tests | `tests/test_dataset_discovery.py` | Regression coverage for the pattern. | Covers capability grouping, prefix mask queries, credential mask query, unknown dimension rejection, duplicate source-type rejection, seed-scope rejection, and handler signature rejection. |

## Why `CapabilityCode` Is An Index, Not Full Truth

`CrawlerCapabilityCode` is intentionally lossy. Several different semantic cells
can share the same bit pattern when the current routing question does not need
to distinguish them.

Examples from the current bit maps:

- `json` maps to `0b0000`.
- `html`, `xml`, and `text` map to `0b0100`.
- `none` and `public_or_review` both map to `0b0000`.
- `optional_api_key`, `api_key`, `oauth`, and `credential_required` map to
  `0b0010`.
- `file_links`, `layer_list`, and `resource_links` map to `0b0001`.

That is useful for coarse slicing, but it cannot answer every domain question.
If a caller needs exact semantics, it must read `CrawlerSpec`.

Rule of thumb:

- Use `CrawlerCapabilityCode` / `CrawlerCapabilityMask` for broad grouping.
- Use `CrawlerSpec` for meaning, labels, policy, reports, and user-facing
  decisions.

## Why `CrawlerSpec` Remains Semantic Source Of Truth

`CrawlerSpec` keeps the actual declared meaning:

- `source_type`
- `source_family`
- `transport`
- `auth_profile`
- `result_shape`
- `seed_scope`
- `supports_full_crawl`
- `handler`
- `matrix_key`
- `capability_code`

This prevents bit-level routing from hiding business meaning. A 4-bit address can
say "catalog-like JSON public path"; it cannot safely say "this source is
licensed, bounded, user-visible, direct-download ready, and importable."

The handler remains normal Python. The registry records what it is; it does not
turn the handler into YAML, a DSL, or cross-repo plugin magic.

## CIDR-Style Mask / Prefix Query Explanation

`CrawlerCapabilityMask` borrows the idea of CIDR/prefix matching, but only as a
small in-process dispatch metaphor.

Example from existing tests:

```python
catalog_json_mask = CrawlerCapabilityMask.from_prefix(0b0000, prefix_len=2)
```

This builds a mask that matches crawlers whose first two capability bits match
the prefix. Tests assert that this includes catalog JSON-like sources such as
`ckan_package_search` and `socrata_catalog_search`, while excluding file-index or
scan-style sources such as `html_file_index` and `erddap_all_datasets`.

Another existing test uses an explicit mask:

```python
credential_mask = CrawlerCapabilityMask(bits=0b0010, mask=0b0010)
```

That asks for the credential-aware bit regardless of other dimensions. At the
current checkpoint, the matching source set is `socrata_catalog_search`.

The important part is that mask results return `CrawlerSpec` objects. Callers do
not lose access to semantic fields.

## Decorator Registration Safety Boundary

`@crawler(...)` is allowed to do these things at import time:

- normalize declarative metadata
- reject blank or duplicate `source_type`
- reject unknown `seed_scope`
- validate that the handler accepts the shared six-argument signature
- reject unsupported capability dimension values
- compute and store the compact capability code

`@crawler(...)` must not do these things:

- perform network requests
- open databases
- write files
- import renderer, compressor, displaytools, or other product repos
- read `.npz` or renderer payloads
- create lifecycle events
- promote readiness
- hide handler behavior behind a custom runtime language

Registration is a safety boundary. It should fail fast on invalid metadata, but
it should not execute product work.

## How This Reduces Nested If/Else

Without this pattern, each caller tends to create its own branch table:

```text
if source_type == "ckan_package_search": ...
elif source_type == "socrata_catalog_search": ...
elif source_type == "html_file_index": ...
```

The registry lets callers ask higher-level questions:

```text
all catalog_search + json sources
all entry_listing sources
all sources matching credential-aware capability bit
all text/file-index-like sources
```

This keeps routing in one place:

- crawler modules declare metadata once
- registry validates and stores the declaration
- diagnostics and UI-neutral payloads query the registry
- handlers still execute as ordinary Python functions

The pattern reduces scattered branching without pretending every branch has been
deleted.

## Where This Pattern May Be Reused Later

| Future area | Possible adaptation | Maturity | Risk |
| ----------- | ------------------- | -------- | ---- |
| crawler / data acquisition | Continue using crawler family, transport, auth, result shape, seed scope, and bounded/full-crawl metadata to route discovery and diagnostics. | Implemented in Core crawler registry as first pass. | Over-encoding source-specific policy into bits instead of `CrawlerSpec` or source profiles. |
| Core readiness / evidence routing | Group report sections by evidence area, source-of-truth kind, missing/blocked/review surfaces, and gate contribution. | Candidate; not implemented as capability addresses. | Could hide conservative readiness logic if compressed too early. |
| compression contract capability | Future visual-compressor contract dimensions could describe asset kind, reconstruction mode, metrics, preview/benchmark support, and evidence outputs. | Conceptual only for RRKAL Core; no cross-repo integration authorized. | Prematurely importing or depending on visual-compressor, or treating docs draft as product schema. |
| displaytools canvas strategy | Future displaytools may classify canvas strategy by backend, interaction mode, layer type, cache mode, or low-compute profile. | Conceptual only; belongs to displaytools owner. | Core must not absorb renderer strategy or UI drawing behavior. |
| skin bridge | Future SkinBuildRequest / SkinBuildResult references may expose capability-like metadata for registry filtering. | Contract-only in Core Visual/Skin docs; no implementation integration. | Do not treat SkinAsset / RendererSkinAsset as implemented or read payloads. |
| evidence adapter | Diagnostic/evidence adapters could declare schema version, source evidence, gate contribution, and safe verification command. | Candidate for Core readiness hardening. | Avoid a universal evidence framework before repeated rules stabilize. |

## Where This Pattern Must Not Be Overused

Do not use capability addressing when a plain condition is clearer. A simple
two-way or three-way branch can be more maintainable than a matrix.

Do not use this pattern to compress truth that should remain explicit:

- user-visible lifecycle status
- review-required decisions
- security or credential storage policy
- license / rights / provenance
- destructive action authorization
- renderer/compressor payload compatibility
- database mutation ownership
- production readiness

Do not generalize it into a universal framework yet. The current pattern is a
documented crawler-registry technique and a reusable design reference. It is not
authorization to extract a global plugin system, adopt a master YAML DSL, or
integrate renderer/compressor projects.

The Core gate remains `partial`.
