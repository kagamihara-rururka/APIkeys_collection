# AssetCard Governance Checkpoint Index

Updated: 2026-06-06

Status: docs-only checkpoint index / non-implementation.

Purpose: provide one quick index for RRKAL Core AssetCard export/query/redaction governance docs, current evidence command, and current boundaries.

This document does not add a JSON fixture driver, export/query API, database schema, lifecycle status, readiness change, renderer integration, compressor integration, Odoriba integration, or cross-repo implementation.

## TL;DR

AssetCard governance is currently a documentation and evidence track only.

Current state:

- Core readiness gate remains `partial`.
- AssetCard export/query is not implemented.
- Redaction fixture packet design is drafted, not executable.
- No requester is authorized to treat Core cards as an integration surface.
- GitHub commits, tests, smoke, CLI JSON, UI behavior, and diffs remain product evidence.

## Current Evidence Command

Run this from `L:\RRKAL_project`:

```powershell
py -3 -B APIkeys_collection.py --core-readiness-report-json
```

Expected current evidence:

```text
core_readiness_report.v1
partial
```

If this command emits a different schema version or gate status, stop and review before changing AssetCard docs or implementation scope.

## AssetCard Governance Docs

| Checkpoint | File | Role | Current meaning |
| ---------- | ---- | ---- | --------------- |
| Reference boundary audit | `ASSETCARD_REFERENCE_BOUNDARY_AND_CORE_CONSOLIDATION_AUDIT.zh-TW.md` | Classifies which Core fields are candidate AssetCard references, unsafe, missing, or not exported. | Field mapping and boundary audit only. |
| Export/query ADR draft | `ASSETCARD_EXPORT_QUERY_CONTRACT_ADR_DRAFT.zh-TW.md` | Drafts future export/query contract language and neutral requester wording. | Contract draft only; no API. |
| Preimplementation gate | `ASSETCARD_EXPORT_QUERY_PREIMPLEMENTATION_GATE.zh-TW.md` | Defines acceptance checklist, redaction requirements, negative-test plan, and stop conditions before implementation. | Gate definition only; implementation not authorized. |
| Touchpoint negative test matrix | `ASSETCARD_EXPORT_QUERY_TOUCHPOINT_NEGATIVE_TEST_MATRIX.zh-TW.md` | Maps Core touchpoints and future negative tests for projection/query behavior. | Test planning only; no code path. |
| Redaction fixture matrix | `ASSETCARD_EXPORT_QUERY_REDACTION_FIXTURE_MATRIX.zh-TW.md` | Lists future positive/negative redaction fixture cases. | Fixture matrix only; no fixture driver. |
| Redaction fixture packet design | `ASSETCARD_REDACTION_FIXTURE_PACKET_DESIGN.zh-TW.md` | Defines future fixture packet fields and diagnostics vocabulary. | Packet design only; examples remain unverified. |

## Governance Chain

The current intended reading order is:

1. read the reference boundary audit to understand safe and unsafe field families;
2. read the ADR draft for neutral contract language;
3. read the preimplementation gate for authorization and stop conditions;
4. read the touchpoint negative test matrix for likely Core code surfaces;
5. read the redaction fixture matrix for future fixture cases;
6. read the fixture packet design for future packet shape.

This chain is deliberately documentation-first. It prevents accidental implementation before the redaction and evidence boundaries are clear.

## What May Be Said

Allowed wording:

- Core AssetCard governance docs are clearer.
- AssetCard export/query remains draft-only.
- Redaction fixture matrix and packet shape are documented.
- Core gate remains `partial`.
- Future implementation must pass redaction, evidence, and negative tests before any public surface is authorized.

## What Must Not Be Said

Do not claim:

- an AssetCard export/query surface has already been implemented;
- Core is mature enough for product integration;
- a requester may use Core cards as an active integration surface;
- renderer/compressor/Odoriba integration is authorized;
- payload/private paths are safe to expose;
- redaction fixtures have executed as tests.

## Evidence Boundaries

| Evidence item | Current source | Boundary |
| ------------- | -------------- | -------- |
| Core readiness gate | `--core-readiness-report-json` | Must remain `partial` unless separately reviewed. |
| AssetCard field safety | Boundary audit and gate docs | Docs evidence only; not exported behavior. |
| Redaction policy | Redaction matrix and packet design | Design only; no driver/helper/API. |
| Fixture verification | Future tests | No fixture packet in these docs is currently verified by code. |
| Consumer wording | ADR/gate/index docs | Neutral requester language only. |

## Future Safe Slices

| Slice | Why useful | Risk | Required validation |
| ----- | ---------- | ---- | ------------------- |
| AssetCard docs registry row | Makes these docs easier to discover in a docs registry. | Registry drift if not maintained. | Docs-only diff, UTF-8 checks. |
| Redaction fixture JSON draft examples | Gives future tests concrete examples. | Can be mistaken for executable fixtures. | Keep under docs or fixtures-draft folder with non-executable label. |
| Internal projection helper proposal | Prepares implementation review. | May drift into code before authorization. | Requires `o_1` / Owner scope approval first. |
| OpenSpec proposal for implementation | Converts docs into reviewed tasks. | Too much scope if bundled with UI/API. | Must keep API, DB, lifecycle, and consumer claims separate. |

## Stop Conditions

Stop and request review if a future change needs:

- JSON fixture driver;
- export/query API;
- Core code change;
- DB/schema/lifecycle/readiness change;
- payload/private path exposure;
- c_2/c_3/c_4 import;
- renderer/compressor/Odoriba implementation;
- requester-consumption claim;
- readiness gate change away from `partial`.

## Readability Guard

For every docs-touching task:

1. do not trust PowerShell/Git terminal Chinese rendering alone;
2. run UTF-8 strict decode;
3. run U+FFFD scan;
4. run mojibake marker scan by Unicode codepoint;
5. run private-use-area marker scan;
6. perform changed-hunk human spot check;
7. run `git diff --check`.

If terminal output looks garbled, verify actual UTF-8 file text before deciding the file is broken. If new mojibake markers or private-use-area markers increase, stop and report.

## Final Classification

`c1_assetcard_governance_checkpoint_index_complete_l2_no_push`
