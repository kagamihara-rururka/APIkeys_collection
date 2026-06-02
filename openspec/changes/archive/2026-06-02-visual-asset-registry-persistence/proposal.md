## Why

RRKAL Core 已有 Visual/Skin Asset control-plane contract、ready-event writer、registry summary、persistence schema contract 與 row projection，但尚未有正式 registry persistence。若直接把 registry entry 寫入資料庫，容易讓 repository layer 自行發明欄位、誤讀 renderer payload，或在普通 serialization / table write 時自動發出 lifecycle event。

這個 change 先把 persistence 的要求、邊界與驗收條件寫成 OpenSpec，讓後續實作能安全消費 `visual_asset_registry_persistence_schema()` 與 `visual_asset_registry_entry_persistence_record()`，而不是臨時接 DB 寫入。

## What Changes

- 新增 Visual/Skin registry persistence capability 的規格。
- 定義 registry persistence 必須只保存 control-plane row，不讀 `.npz`、GPU buffer、renderer project、payload bytes。
- 定義 persistence 必須消費既有 schema / row projection contract，不得由 repository layer 自行拆欄位。
- 定義 migration / rollback / ownership guard：沒有明確 migration 時不得自動建表。
- 定義 ready-event 發送邊界：table write 不得自動發 event；只有 explicit workflow 可呼叫 `log_visual_asset_ready_registry_entry()`。
- 定義 agent/UI 可讀 summary：persistence 後仍必須輸出 lifecycle display profile / review flag / renderer target count 等 control-plane payload。
- 不包含 renderer integration、skin builder、payload validation、displaytools / compressor import。

## Capabilities

### New Capabilities

- `visual-asset-registry-persistence`: Defines how RRKAL Core may persist Visual/Skin registry entries as control-plane records, including schema ownership, migration guards, event emission boundaries, and summary/read APIs.

### Modified Capabilities

- None.

## Impact

- Affected code areas:
  - `api_launcher/visual_asset_contracts.py`
  - future repository / migration modules
  - `api_launcher/project_maturity.py`
  - tests for registry persistence, no-payload guarantees, migration guard, and event boundary
- Affected docs:
  - `docs/VISUAL_SKIN_ASSET_CONTRACT.zh-TW.md`
  - `docs/PROJECT_MATURITY_MATRIX.zh-TW.md`
  - `docs/AGENT_HANDOFF.zh-TW.md`
  - `docs/PROJECT_GTD.md`
- No new runtime dependency is expected.
- No UI behavior is required in the first implementation slice; UI may consume summary/read payload later.
