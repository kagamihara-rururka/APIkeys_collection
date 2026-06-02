## 1. Contract And Dry-Run Foundation

- [x] 1.1 Add a dry-run SQLite DDL renderer that consumes `visual_asset_registry_persistence_schema()` and writes no database state.
- [x] 1.2 Add tests proving dry-run DDL includes required columns/indexes and excludes payload columns.
- [x] 1.3 Expose the dry-run contract in project maturity metrics without changing renderer maturity away from `contract_only`.

## 2. Owned Test Persistence

- [x] 2.1 Add an owned test-only table creation helper gated behind explicit test/runtime options.
- [x] 2.2 Add write/read helpers that consume `visual_asset_registry_entry_persistence_record()` and return `RendererSkinAssetRegistryEntry`-compatible control-plane payloads.
- [x] 2.3 Add tests for write/read/list using a temporary SQLite database and existing SQLite write gate or equivalent per-path guard.
- [x] 2.4 Add rollback/drop preview for owned test databases only; do not enable destructive actions for user DBs.

## 3. Summary And UI-Neutral Read Payload

- [x] 3.1 Add read-side summary helper that returns lifecycle counts, `status_display_profiles`, review counts, renderer target counts, and safety flags.
- [x] 3.2 Add tests proving read payloads do not import displaytools / visual-compressor / vis_2_dis and do not read payload files.
- [x] 3.3 Add CLI JSON or debug endpoint only after service tests pass; UI integration remains a later slice.

## 4. Explicit Event Boundary

- [x] 4.1 Add a separate explicit workflow/CLI helper that can call `log_visual_asset_ready_registry_entry()` for a persisted ready entry.
- [x] 4.2 Add duplicate-event policy tests before enabling event emission from persisted entries.
- [x] 4.3 Prove ordinary table write/upsert does not emit `visual_asset_ready` events.

## 5. Documentation And Handoff

- [x] 5.1 Update `docs/VISUAL_SKIN_ASSET_CONTRACT.zh-TW.md` after each implemented slice.
- [x] 5.2 Update `docs/PROJECT_MATURITY_MATRIX.zh-TW.md`, `docs/PROJECT_GTD.md`, `docs/AGENT_HANDOFF.zh-TW.md`, and `docs/DEVELOPMENT_LOG.zh-TW.md`.
- [x] 5.3 Run docs/OpenSpec mojibake scan, `git diff --check`, focused tests, pre-push smoke, and GitHub Actions before marking the change ready to archive.
