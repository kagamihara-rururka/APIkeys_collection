# Core Integration Planning Gate Readiness

最後更新：2026-06-02

這份文件整理 RRKAL Core 目前可提供給未來 Integration Planning Gate 的證據與缺口。它只描述 Core control-plane readiness，不授權 renderer、compressor、SkinAsset、RendererSkinAsset 或跨 repo integration。

一句話邊界：

> RRKAL Core 可以描述資產生命週期、manifest reference、review gate、job status 與 lineage；它不讀 renderer payload，也不決定資產怎麼畫或怎麼壓縮。

## 已接受基線

| 項目 | 證據 |
| --- | --- |
| Core readiness JSON code checkpoint | `0ead886bd3a19f74c8115a4ffd1a8a8fa67f1ba5` / `feat(core): add readiness report JSON diagnostic` |
| Docs/log checkpoint | `75d0d5472e32acb48d4c9a40524f95e8e0bba737` / `docs: log core readiness checkpoint` |
| Core readiness CI | GitHub Actions run `26825598254` PASS |
| Docs checkpoint CI | GitHub Actions run `26827560343` PASS |
| Current readiness schema | `core_readiness_report.v1` |
| Current gate status | `partial` |
| Core review-required diagnostic | `--core-review-required-report-json` / `core_review_required_report.v1` |

`partial` 是刻意保守的狀態。它表示 Core 已有 registry / lifecycle / manifest / review / lineage 的 evidence surface，但仍缺 runtime state machine、unified scheduler、review queue persistence、deep adapter coverage 等證據。不得把此狀態解讀為 integration 已可開工。

## Evidence Gap Table

| Evidence area | Current evidence present | Missing evidence | Blocked reason | Core-only next action | Needs `o_1`? | Needs schema / lifecycle change? |
| --- | --- | --- | --- | --- | --- | --- |
| `registry_evidence` | Crawler registry 有 14 個 source type；content registry 有 direct import / review rule / unknown fallback；dataset adapter report 有 3 個 provider-specific deep adapters。 | `deep_adapter_coverage_does_not_match_supported_source_types` | 無硬阻塞；這是 coverage gap，不是 integration blocker。 | 只在能閉合真實 download/import path 時新增 deep adapter；維持 source dispatch 走 registry，不散回 `if source_type`。 | 視 adapter 是否影響跨 repo contract；一般 Core-only report 不需要。 | 不需要。 |
| `lifecycle_evidence` | `SKIN_ASSET_LIFECYCLE_STATUSES` 與 display profiles 已存在；空 registry summary 可回報 status counts；schema allowed lifecycle statuses 可查。 | `runtime_lifecycle_state_machine_not_unified` | 目前是 contract/control-plane evidence，尚未有統一 runtime lifecycle state machine。 | 在不新增 status 的前提下補狀態轉移 audit / report；UI 只吃 display profile。 | 若新增/改名 status 或轉移規則，必須。 | 若只補報表不需要；改 status/schema 需要。 |
| `manifest_reference_evidence` | `visual_skin_asset_registry` schema contract 含 `manifest_path`、`skin_asset_id`、`source_curated_asset_id`、`dataset_uid`；payload loading 明確 false。 | 無 manifest 欄位缺口。 | 尚未正式 user DB persistence，仍是 contract-only table。 | 保持 manifest reference control-plane-only；下一步可補 persistence migration review evidence。 | 若要正式 integration 或 downstream contract，需要。 | 正式 DB migration 需要審查；本文件不改 schema。 |
| `review_required_evidence` | Content review rules 可列 archive、scientific grid、geospatial asset、columnar table、database snapshot、document；visual lifecycle 有 `review_required`。 | `review_queue_persistence_not_unified` | `unsupported_payload_format` 仍會導向 review，不可硬轉 ready。 | 補 review queue / review-required surfaces 的只讀報表或 maturity evidence；未知/heavy format 不 promoted。 | 若要改 review workflow 或跨 repo review contract，需要。 | 報表不需要；持久化 queue schema 需要。 |
| `job_status_evidence` | Visual lifecycle statuses、explicit event writer contract、background scheduler maturity row、Tk single-flight start result contract 都可查。 | `unified_bounded_job_scheduler_not_yet_implemented` | `auto_lifecycle_event_emission_disabled` 是刻意安全邊界。 | 先設計 bounded scheduler / job status report，不全面改 asyncio；保持 auto event disabled。 | 若要啟用 auto lifecycle event 或跨 repo builder job adapter，需要。 | 若新增 job lifecycle schema/status 需要。 |
| `asset_lineage_evidence` | Schema contract 含 `source_request_id`、`source_curated_asset_id`、`dataset_uid`；lineage persistence schema 與 indexes 可查；control_plane_only true。 | 無 lineage 欄位缺口。 | 仍是 contract-only persistence schema，尚未 cross-project consumption。 | 正式 persistence 前先審 migration guard；不要把 Notion / archive transcript 直接寫進 product lineage。 | 若下游要 consumption contract，需要。 | 正式 persistence/migration 需要審查；本文件不改 schema。 |
| `integration_planning_gate` | Gate 聚合 missing evidence、blocked surfaces、next safe actions；status 為 `partial`。 | deep adapter coverage、review queue persistence、runtime lifecycle state machine、unified bounded scheduler。 | 目前還不能宣稱 ready；缺口有些需要設計與 review。 | 準備 Core-side evidence，不 import downstream repos；任何 lifecycle/cross-project contract 先送 `o_1`。 | 是，若要進入 lifecycle schema、cross-project contract 或 integration proposal。 | 視下一步而定；目前不改。 |

## JSON Quality Check

目前 `--core-readiness-report-json` 符合以下要求：

- stdout 是純 JSON，適合 agent / automation 解析。
- `schema_version` 為 `core_readiness_report.v1`。
- `integration_planning_gate.status` 保守維持 `partial`。
- 不輸出 `ready_for_planning=true` 或類似 production-ready 宣稱。
- 各 section 分開列出：
  - `existing_evidence`
  - `missing_evidence`
  - `blocked_surfaces`
  - `review_required_surfaces`
  - `contract_only_surfaces`
  - `planned_surfaces`
  - `next_safe_actions`
- `safety` flags 明確標出：
  - `control_plane_only=true`
  - `imports_renderer_projects=false`
  - `imports_compressor_projects=false`
  - `reads_renderer_payloads=false`
  - `reads_npz=false`
  - `changes_lifecycle_schema=false`
  - `cross_repo_implementation=false`

注意：Windows PowerShell 的 `>` 重導可能把 JSON 檔寫成 UTF-16。驗證 JSON stdout 時，優先使用 pipe 或 Python `subprocess.check_output()` 直接讀 bytes；不要把 PowerShell redirection 產生的檔案當成 CLI encoding 失敗證據。

## Review Required Evidence Report

`--core-review-required-report-json` 是 Core-only diagnostic，用來把 review-required surface 從完整 readiness report 中獨立拉出，方便下一輪設計 review queue 或 UI 顯示時先讀一份小報表。

目前輸出：

- `schema_version = core_review_required_report.v1`
- `status = partial`
- `missing_evidence = ["review_queue_persistence_not_unified"]`
- `blocked_surfaces = ["unsupported_payload_format"]`
- `review_required_surfaces` 會列出 content review rules 與 `visual_skin_asset_review_required`
- `safety.changes_review_queue_schema = false`
- `safety.changes_lifecycle_schema = false`
- `safety.cross_repo_implementation = false`

它不新增 review queue schema，不改 lifecycle vocabulary，不把 unknown/heavy payload promoted 成 ready，也不碰下游 repo。

## Integration Planning Gate Input Summary

Core 可以提供：

- source / crawler capability registry evidence。
- content parser / review rule registry evidence。
- provider-specific deep adapter inventory。
- Visual/Skin lifecycle vocabulary 與 UI-neutral display profiles。
- manifest reference schema contract。
- review_required / contract_only / planned surfaces。
- explicit event writer / auto event disabled evidence。
- asset lineage fields 與 control-plane-only safety flags。

Core 尚不能提供：

- 統一 runtime lifecycle state machine。
- 統一 bounded job scheduler。
- 統一 review queue persistence。
- 14 個 source crawler 對應的完整 deep adapter coverage。
- 正式 user DB visual registry persistence。
- 下游 renderer/compressor consumption contract。

不屬於 Core 的工作：

- 讀取 `.npz`、tile、GPU buffer、renderer payload。
- import `RRKAL_displaytools`、`rrkal-visual-compressor`、`vis_2_dis`。
- 實作 renderer preview、skin builder、compression integration。
- 宣稱 RendererSkinAsset / SkinAsset 已可產品整合。

## Required `o_1` Review Triggers

以下任何一項都必須先送 `o_1` review：

- 新增、改名或刪除 lifecycle status。
- 改 lifecycle schema 或 migration 欄位。
- 從 `partial` 改成 `ready_for_planning`。
- 啟用 auto lifecycle event emission。
- 定義 cross-repo contract。
- 引入 RendererSkinAsset / SkinAsset implementation wording。
- 引入 displaytools / compressor / vis_2_dis import 或 runtime dependency。
- 讓 Core 讀 `.npz` / renderer payload / compression payload。
- 把 contract-only 能力寫成 user-facing stable feature。

## Proposed Next Core-Only Slices

1. **Job Status Evidence Report**
   - 目標：聚合 Tk background job policy、single-flight result contract、download/import job status 與 visual lifecycle event boundary。
   - 邊界：不做 asyncio 重寫，不新增 scheduler schema。

2. **Lifecycle Transition Audit Draft**
   - 目標：只讀整理目前 lifecycle vocabulary、allowed transitions candidate、blocked transitions 與 review triggers。
   - 邊界：不新增 status，不改 transition runtime。

3. **Manifest Reference Persistence Readiness**
   - 目標：把 visual registry schema contract、DDL preview、owned-test persistence helper、formal DB gap 整理成 readiness report。
   - 邊界：不建立正式 user DB table，不跑 migration。

4. **Deep Adapter Coverage Plan**
   - 目標：列出 14 個 source crawler type 與 3 個 deep adapter 的差距，標示哪些只需要 metadata crawler、哪些需要真正 download/import adapter。
   - 邊界：不新增 adapter，避免 class explosion。

## Repo Consistency Audit

`#repo_consistency_audit` result for this slice:

- Active repo / branch: `L:\RRKAL_project`, `rrkal-32e215c-recovery`。
- Latest accepted code checkpoint: `0ead886`.
- Latest accepted docs checkpoint before this note: `75d0d54`.
- Active coordination route: Notion `Agents討論區`。
- Deprecated coordination route: `L:\AGENT_EXCHANGE` archive / historical reference only。
- Product evidence source: GitHub commits, tests, smoke, CLI JSON, actual UI behavior, git diff, GitHub Actions。
- Current readiness JSON: `core_readiness_report.v1`, gate `partial`。
- Current review-required JSON: `core_review_required_report.v1`, status `partial`。
- Cross-repo touch: none.
- Renderer/compressor/SkinAsset implementation: none.
- Lifecycle schema/status change: none.
