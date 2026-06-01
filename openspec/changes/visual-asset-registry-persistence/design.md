## Context

RRKAL Core 目前已定義 Visual/Skin Asset 的 control-plane contract，包含 build request/result、manifest reference、registry entry、ready event、lifecycle display profile、registry summary、persistence schema contract 與 row projection。這些能力都刻意不 import `RRKAL_displaytools`、`rrkal-visual-compressor`、`vis_2_dis`，也不讀 `.npz`、GPU buffer 或 renderer payload。

下一步若要真正持久化 registry entry，會跨到 repository / migration / event / maturity payload 邊界。這類變更不能直接在某個 repository 函式裡臨時建表或自動發 event，否則會打破 RRKAL Core 只管 control plane 的原則。

## Goals / Non-Goals

**Goals:**

- 讓 Visual/Skin registry persistence 有明確的 schema owner、migration guard、rollback guard 與 acceptance criteria。
- 讓 persistence 實作只消費 `visual_asset_registry_persistence_schema()` 與 `visual_asset_registry_entry_persistence_record()`。
- 讓 write/read/list/summary 行為可測，且只保存 control-plane row。
- 保留 explicit ready-event 邊界：table write 不等於 event emission。
- 在 project maturity / handoff 中維持 `contract_only` 或 `partial_bounded` 的精準狀態，不把 registry persistence 說成 renderer integration。

**Non-Goals:**

- 不實作 renderer、skin builder、compression、displaytools integration 或 payload validation。
- 不讀 `.npz`、tile、GPU buffer、Qt/Taichi payload、renderer project file。
- 不新增跨專案 import。
- 不做自動 background scheduler 或 lifecycle subscription。
- 不把 visual asset registry persistence 當成一般使用者已可操作功能寫進 user guide。

## Decisions

1. **Schema contract remains the source of truth**

   Repository / migration code MUST consume `visual_asset_registry_persistence_schema()` and `visual_asset_registry_entry_persistence_record()` rather than duplicating column names. This keeps docs, tests, maturity payload, and implementation aligned.

   Alternative considered: define SQL directly in repository code. Rejected because it would create a second untracked schema authority.

2. **Migration is explicit and reversible**

   The first implementation SHOULD provide dry-run SQL or migration preview before any real table creation. Real table creation MUST be opt-in and test-covered. Rollback must be documented before enabling write paths.

   Alternative considered: auto-create table on first write. Rejected because it hides destructive/migration behavior inside ordinary workflow execution.

3. **Persistence writes do not emit ready events**

   Registry persistence MAY store a `ready` entry, but it MUST NOT call `log_visual_asset_ready_registry_entry()` implicitly. Event emission remains an explicit workflow or command so the user/agent can reason about duplicates and downstream consumption.

   Alternative considered: emit event after successful write. Rejected because a retry, import replay, or migration backfill could spam duplicate `visual_asset_ready` events.

4. **Read APIs return UI-neutral control-plane payload**

   Any read/list/summary API should return lifecycle display profile, review flag, renderer targets, lineage fields, and safety flags. UI layers should not infer status labels or read payload files.

5. **No downstream runtime coupling**

   The persistence module MUST NOT import displaytools, visual-compressor, vis_2_dis, Taichi, PyQt, or other renderer runtime packages. Cross-project coordination should happen through manifest references and `L:\AGENT_EXCHANGE` / OpenSpec decisions.

## Risks / Trade-offs

- **Risk: Table schema drifts from contract** → Mitigation: tests compare row keys and schema columns; maturity payload exposes the active schema contract.
- **Risk: Persistence is mistaken for renderer readiness** → Mitigation: docs and maturity row keep renderer/simulation at `contract_only` until payload I/O and renderer consumption are implemented elsewhere.
- **Risk: Duplicate ready events** → Mitigation: persistence write path does not emit events; event emission must be explicit and test-covered.
- **Risk: Payload/secret metadata leaks into DB** → Mitigation: row projection uses bounded metadata filtering; tests must include payload/secret keys.
- **Risk: SQLite locking on Windows/cloud drive** → Mitigation: concrete write path should reuse existing SQLite write gate or equivalent per-path guard, and tests should avoid parallel writer assumptions.

## Migration Plan

1. Add repository/migration dry-run helper that renders the schema contract into SQL without executing it.
2. Add tests for schema/row key alignment, no payload columns, and no downstream imports.
3. Add explicit opt-in table creation only after dry-run acceptance exists.
4. Add write/read/list/summary helpers behind ownership guards.
5. Add explicit ready-event workflow only after persistence semantics and duplicate handling are defined.
6. Update project maturity and docs after each bounded implementation slice.

Rollback strategy:

- If migration is preview-only, rollback is deleting generated preview output.
- If table creation is later implemented, rollback must be explicit SQL and tested against an owned test database only.
- Never mutate non-test user DBs without user confirmation and backup/manifest context.

## Open Questions

- Should the first concrete persistence target be the existing launcher SQLite DB, a dedicated registry SQLite DB, or a JSONL/sidecar prototype?
- Should registry entries be upserted by `registry_entry_id` only, or should `(skin_asset_id, source_curated_asset_id)` uniqueness also be enforced?
- What duplicate policy should explicit `visual_asset_ready` event emission use after persistence exists?
