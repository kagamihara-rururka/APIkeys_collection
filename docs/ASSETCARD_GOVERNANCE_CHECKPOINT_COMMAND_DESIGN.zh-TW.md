# AssetCard Governance Checkpoint Command Design

Updated: 2026-06-06

Status: governance-tooling prototype / no AssetCard export/query implementation.

Purpose: define and document the local Core AssetCard governance checkpoint wrapper that aggregates current Core readiness evidence and AssetCard governance document references.

The prototype script is `scripts/assetcard_governance_checkpoint.py`. It does not add an export/query API, JSON fixture driver, database schema, lifecycle status, readiness change, renderer integration, compressor integration, Odoriba integration, or cross-repo implementation.

The validator script is `scripts/validate_assetcard_governance_checkpoint.py`. It validates the wrapper JSON and can run an in-memory negative self-test for false-safety fields. It does not execute redaction fixture packets or create any AssetCard export/query surface.

Checkpoint and validator runners may aggregate leaf evidence only. They must not invoke pytest, unittest, or any test that calls the checkpoint/validator scripts again. If a future implementation uses subprocesses, every subprocess call must set an explicit timeout and the JSON report must disclose process fan-out evidence.

## TL;DR

The checkpoint wrapper gives agents one local command to confirm the AssetCard governance lane is still safe before implementation planning.

It should aggregate:

1. `py -3 -B APIkeys_collection.py --core-readiness-report-json`;
2. `ASSETCARD_GOVERNANCE_CHECKPOINT_INDEX.zh-TW.md`;
3. `ASSETCARD_REDACTION_FIXTURE_PACKET_DESIGN.zh-TW.md`;
4. the redaction fixture matrix and preimplementation gate references.

The wrapper does not export AssetCards, run fixture packets, read payloads, or claim downstream consumption.

## Current Wrapper Command

Run this from `L:\RRKAL_project`:

```powershell
py -3 -B scripts\assetcard_governance_checkpoint.py
```

The output is pure JSON and should parse through:

```powershell
py -3 -B scripts\assetcard_governance_checkpoint.py |
  py -3 -c "import sys,json; d=json.load(sys.stdin); assert d['checkpoint_passed'] is True; assert d['core_gate_status'] == 'partial'"
```

## Current Validator Command

Run this from `L:\RRKAL_project`:

```powershell
py -3 -B scripts\validate_assetcard_governance_checkpoint.py
```

The validator output is pure JSON and should report:

```text
assetcard_governance_checkpoint_validator.v1
passed
partial
```

The negative self-test mutates in-memory JSON copies only:

```powershell
py -3 -B scripts\validate_assetcard_governance_checkpoint.py --self-test-negative
```

It must detect these unsafe mutations:

- `export_query_api_exists=true`;
- `json_fixture_driver_exists=true`;
- `cross_repo_integration=true`;
- `payload_exposure=true`;
- `private_path_exposure=true`;
- `odoriba_consumption_claim=true`;
- `core_gate_status` not equal to `partial`;
- `missing_docs` non-empty.

## Current Manual Command

The current evidence command remains manual:

```powershell
py -3 -B APIkeys_collection.py --core-readiness-report-json
```

Expected current evidence:

```text
core_readiness_report.v1
partial
```

If the schema or gate changes unexpectedly, stop before touching AssetCard implementation scope.

## Wrapper Goals

| Goal | Why useful | Boundary |
| ---- | ---------- | -------- |
| gather Core readiness evidence | Gives agents the current `core_readiness_report.v1` / gate value quickly. | It must not change readiness. |
| list AssetCard governance docs | Makes the governance chain discoverable. | It must not treat docs as implementation evidence. |
| summarize redaction fixture design status | Shows whether redaction design exists and remains non-executable. | It must not run fixture packets. |
| emit agent-readable JSON | Lets `n_1`, `o_1`, and future agents parse checkpoint status. | stdout must be pure JSON. |
| preserve conservative gate | Keeps Core gate visible as `partial`. | It must not promote planning or product readiness. |

## Wrapper Input Sources

| Source | Current path / command | Intended wrapper use |
| ------ | ---------------------- | -------------------- |
| Core readiness report | `py -3 -B APIkeys_collection.py --core-readiness-report-json` | Parse schema version and `integration_planning_gate.status`. |
| Governance index | `docs/ASSETCARD_GOVERNANCE_CHECKPOINT_INDEX.zh-TW.md` | Confirm index exists and list linked governance docs. |
| Redaction fixture packet design | `docs/ASSETCARD_REDACTION_FIXTURE_PACKET_DESIGN.zh-TW.md` | Confirm packet shape is documented but not executable. |
| Redaction fixture matrix | `docs/ASSETCARD_EXPORT_QUERY_REDACTION_FIXTURE_MATRIX.zh-TW.md` | Confirm fixture case matrix exists. |
| Preimplementation gate | `docs/ASSETCARD_EXPORT_QUERY_PREIMPLEMENTATION_GATE.zh-TW.md` | Confirm stop conditions and redaction requirements are documented. |
| Touchpoint negative matrix | `docs/ASSETCARD_EXPORT_QUERY_TOUCHPOINT_NEGATIVE_TEST_MATRIX.zh-TW.md` | Confirm future code touchpoints and negative tests are mapped. |
| ADR draft | `docs/ASSETCARD_EXPORT_QUERY_CONTRACT_ADR_DRAFT.zh-TW.md` | Confirm neutral contract language exists. |

## JSON Output Fields

Current prototype shape:

```json
{
  "schema": "assetcard_governance_checkpoint.v1",
  "status": "passed",
  "core_readiness_schema": "core_readiness_report.v1",
  "core_gate_status": "partial",
  "assetcard_governance_docs_present": true,
  "redaction_docs_present": true,
  "docs": {
    "governance_checkpoint_index": {
      "path": "docs/ASSETCARD_GOVERNANCE_CHECKPOINT_INDEX.zh-TW.md",
      "present": true
    }
  },
  "export_query_api_exists": false,
  "json_fixture_driver_exists": false,
  "cross_repo_integration": false,
  "payload_exposure": false,
  "private_path_exposure": false,
  "odoriba_consumption_claim": false,
  "next_safe_actions": [
    "keep_docs_index_current",
    "request_review_before_any_implementation"
  ],
  "checkpoint_passed": true
}
```

## Required Wrapper Behavior

| Behavior | Requirement |
| -------- | ----------- |
| JSON mode | stdout is pure JSON; no banners, logs, Markdown, or warning text. |
| readiness parsing | Must parse `--core-readiness-report-json` and preserve `partial`. |
| docs inventory | Must only check tracked docs references, not infer implementation. |
| recursion guard | Must not call tests, pytest, unittest, or the validator. |
| timeout guard | Current prototype has zero subprocess fan-out. Future subprocess calls require explicit timeout. |
| fan-out evidence | JSON must disclose process fan-out counters. |
| no fixture execution | Must not run or materialize redaction fixture packets. |
| no payload access | Must not read manifest payloads, `.npz`, renderer buffers, or private files. |
| no cross-repo import | Must not import c_2/c_3/c_4, displaytools, visual-compressor, or Odoriba code. |
| failure mode | If readiness schema/gate is unexpected, report `blocked` or `needs_review`, not success. |

## Negative Assertions For Future Tests

Tests should assert:

1. `schema` is stable;
2. Core readiness evidence reports `core_readiness_report.v1`;
3. gate status remains `partial` unless separately reviewed;
4. `fixture_driver_exists` is false until a separate implementation is authorized;
5. `export_query_api_exists` is false until a separate implementation is authorized;
6. no payload/private path fields are emitted;
7. no requester-consumption claim is emitted;
8. no cross-repo imports are required.

The current validator enforces these assertions against the wrapper output and keeps the negative self-test in memory only. It is a governance self-check, not an executable fixture driver.

## What This Design Does Not Authorize

- No `api_launcher` CLI flag.
- No AssetCard export/query API.
- No JSON fixture driver.
- No DB/schema/lifecycle/readiness change.
- No payload/private path exposure.
- No c_2/c_3/c_4 import.
- No Odoriba/displaytools/compressor integration.
- No claim that any requester can consume Core cards.

## Future Safe Expansion Slice

If Owner / `o_1` later authorizes implementation, keep the first wrapper slice narrow:

1. one Core-only helper or CLI diagnostic;
2. no AssetCard export/query behavior;
3. no fixture packet execution;
4. parse only `--core-readiness-report-json` plus static docs inventory;
5. focused tests for pure JSON and conservative safety fields;
6. no UI changes.

Anything involving export/query behavior, fixture driver execution, DB/schema/lifecycle changes, or downstream requester wording needs a separate reviewed task.

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

`c1_assetcard_governance_checkpoint_command_design_complete_l2_no_push`
