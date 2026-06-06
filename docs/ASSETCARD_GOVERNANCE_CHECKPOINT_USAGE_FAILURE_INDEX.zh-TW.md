# AssetCard Governance Checkpoint Usage / Failure Index

Updated: 2026-06-07

Status: docs-only usage and failure guide / non-implementation.

Purpose: explain how agents should run, read, and stop on the AssetCard governance checkpoint wrapper and validator without adding any AssetCard export/query behavior.

This document does not add Core code, database schema, lifecycle status, readiness change, fixture driver, downstream repo import, payload exposure, or requester-consumption claim.

## TL;DR

Use these commands from `L:\RRKAL_project`:

```powershell
py -3 -B APIkeys_collection.py --core-readiness-report-json
py -3 -B scripts\assetcard_governance_checkpoint.py
py -3 -B scripts\validate_assetcard_governance_checkpoint.py
py -3 -B scripts\validate_assetcard_governance_checkpoint.py --self-test-negative
```

Expected current signals:

- Core readiness schema: `core_readiness_report.v1`
- Core gate: `partial`
- Checkpoint schema: `assetcard_governance_checkpoint.v1`
- Validator schema: `assetcard_governance_checkpoint_validator.v1`
- Wrapper `checkpoint_passed`: `true`
- Validator `status`: `passed`
- Validator negative self-test: all unsafe in-memory mutations detected

If any signal differs, stop before changing AssetCard scope.

## Layer Responsibilities

| Layer | Command / surface | Responsibility | Stop if |
| ----- | ----------------- | -------------- | ------- |
| Core readiness report | `--core-readiness-report-json` | Provides current Core evidence and the conservative gate value. | Schema differs, gate is not `partial`, or JSON does not parse. |
| checkpoint wrapper | `scripts\assetcard_governance_checkpoint.py` | Aggregates leaf evidence: Core gate, required docs, false-safety flags, and fan-out counters. | `checkpoint_passed` is not `true`, `missing_docs` is non-empty, or any false-safety flag flips. |
| validator | `scripts\validate_assetcard_governance_checkpoint.py` | Validates wrapper JSON and boundary flags. | `status` is not `passed`, errors are non-empty, or fan-out is nonzero. |
| meta-test | focused tests only | Proves JSON purity, negative mutations, and recursion guard behavior. | Must not be called by checkpoint or validator scripts. |

## Wrapper Field Interpretation

| Field family | Fields | Good signal | Failure meaning |
| ------------ | ------ | ----------- | --------------- |
| identity | `schema`, `status` | Known schema and `passed`. | The wrapper contract changed or the checkpoint is blocked. |
| Core gate | `core_readiness_schema`, `core_gate_status`, `checkpoint_passed` | `core_readiness_report.v1`, `partial`, `true`. | Core evidence changed or the wrapper should not be treated as passed. |
| docs presence | `assetcard_governance_docs_present`, `redaction_docs_present`, `docs`, `missing_docs` | Required governance docs present; `missing_docs=[]`. | A governance doc path drifted or was removed. |
| false-safety fields | `export_query_api_exists`, `json_fixture_driver_exists`, `cross_repo_integration`, `payload_exposure`, `private_path_exposure`, `odoriba_consumption_claim` | All `false`. | Stop; a boundary changed or the wrapper is no longer safe. |
| runner guard | `runner_constraints` | Leaf-evidence-only and no test/validator recursion. | Stop if runner constraints imply recursive validation or undisclosed subprocess behavior. |
| fan-out evidence | `process_fanout` | All counters are zero in the current prototype. | Stop if subprocess or test fan-out appears without explicit reviewed scope. |
| boundary | `boundary` | No export, fixture packet execution, schema/readiness change, or downstream import. | Stop if any boundary flips toward implementation behavior. |

## Validator Field Interpretation

| Field family | Fields | Good signal | Failure meaning |
| ------------ | ------ | ----------- | --------------- |
| identity | `schema`, `status` | Known validator schema and `passed`. | Validator contract changed or validation failed. |
| checkpoint identity | `validated_checkpoint_schema` | `assetcard_governance_checkpoint.v1`. | Validator is reading an unexpected wrapper payload. |
| Core gate | `core_readiness_schema`, `core_gate_status`, `checkpoint_passed` | `core_readiness_report.v1`, `partial`, `true`. | Core gate drift or wrapper failure. |
| docs | `missing_docs` | Empty list. | A required governance doc is absent. |
| false-safety echo | `safety_false_fields` | Every listed value is `false`. | Stop; a safety flag no longer holds. |
| validation outcome | `errors` | Empty list. | Stop and inspect error codes. |
| negative self-test | `negative_self_test` | `passed=true`, `undetected_mutations=[]`, `case_count=8`. | Validator failed to catch an unsafe mutation. |
| fan-out evidence | `process_fanout` | All counters are zero in the current prototype. | Stop if validator starts process fan-out without explicit reviewed scope. |

## Failure State Cheat Sheet

| Failure state | Likely cause | Required response |
| ------------- | ------------ | ----------------- |
| Core JSON cannot parse | stdout pollution, runtime error, or command failure. | Stop; do not update governance docs as evidence until JSON mode is restored. |
| Core gate not `partial` | Core evidence changed. | Stop and request review before changing any AssetCard wording. |
| wrapper `checkpoint_passed=false` | Missing docs, gate drift, or safety flag change. | Inspect wrapper JSON; fix docs only if the issue is document drift. |
| `missing_docs` non-empty | A required governance document path moved or was removed. | Restore the document route or update docs after verifying the new source. |
| false-safety flag is `true` | The tool is no longer only a governance checkpoint. | Stop; this may require separate authorization. |
| `process_fanout` nonzero | A runner started invoking subprocesses. | Confirm every subprocess has timeout and no recursive test loop. |
| validator `errors` non-empty | Wrapper payload failed strict validation. | Treat error codes as source of truth for the checkpoint. |
| negative self-test misses a mutation | Validator is not guarding false-safety claims. | Stop; repair validator before relying on checkpoint output. |

## Stop Conditions

Stop and request review if any work would require:

- changing Core code;
- adding an AssetCard export/query surface;
- adding a JSON fixture driver;
- changing DB/schema/lifecycle/readiness behavior;
- exposing payload data or private local paths;
- importing c_2/c_3/c_4 or downstream runtime code;
- saying a requester can consume Core cards as an active surface;
- changing Core gate wording away from `partial`.

## Scan-Safe Wording Rule

When documenting boundaries, prefer phrases such as:

- "claims of product maturity are not authorized";
- "requester-consumption is not authorized";
- "the Core gate remains `partial`";
- "this is governance evidence only".

Avoid exact phrases that naive scans may treat as completed capability claims.

## Final Classification

`c1_assetcard_governance_checkpoint_usage_failure_index_complete_l2_no_push`
