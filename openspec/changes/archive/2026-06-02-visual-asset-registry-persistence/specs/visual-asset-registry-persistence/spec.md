## ADDED Requirements

### Requirement: Registry persistence uses the Visual/Skin schema contract
The system SHALL use `visual_asset_registry_persistence_schema()` and `visual_asset_registry_entry_persistence_record()` as the source of truth for Visual/Skin registry persistence fields.

#### Scenario: Repository prepares a registry row
- **WHEN** a repository or migration helper needs a persistable row for a `RendererSkinAssetRegistryEntry`
- **THEN** it SHALL consume `visual_asset_registry_entry_persistence_record()` rather than manually rebuilding column names.

#### Scenario: Schema columns are checked
- **WHEN** tests validate registry persistence shape
- **THEN** the persisted row keys SHALL match the column names exposed by `visual_asset_registry_persistence_schema()`.

### Requirement: Registry persistence is explicit and migration guarded
The system SHALL NOT create or mutate Visual/Skin registry tables unless an explicit migration or owned test setup requests it.

#### Scenario: Ordinary serialization occurs
- **WHEN** code calls `to_dict()`, `visual_asset_registry_summary()`, `renderer_skin_asset_manifest_projection()`, or `visual_asset_registry_entry_persistence_record()`
- **THEN** the system SHALL NOT create a database table, connect to a database, or write files.

#### Scenario: Migration preview exists
- **WHEN** a future implementation renders SQL or migration steps
- **THEN** the output SHALL be reviewable as dry-run material before any real table creation is allowed.

### Requirement: Registry persistence stores control-plane data only
The system SHALL persist only Visual/Skin control-plane fields and SHALL NOT read or store renderer payload bytes.

#### Scenario: Registry entry contains payload-like metadata
- **WHEN** metadata includes keys such as `payload`, `payload_bytes`, `secret`, `token`, `api_key`, `password`, `npz`, or `gpu_buffer`
- **THEN** the persistence row SHALL omit those metadata fields.

#### Scenario: Downstream renderer payload exists
- **WHEN** a registry entry references a manifest path
- **THEN** RRKAL Core SHALL store the reference and SHALL NOT open `.npz`, tile, GPU buffer, renderer project, or displaytools payload files.

### Requirement: Registry writes do not automatically emit ready events
The system SHALL keep registry persistence and `visual_asset_ready` event emission as separate explicit actions.

#### Scenario: Ready entry is persisted
- **WHEN** a future repository writes a registry entry whose lifecycle status is `ready`
- **THEN** the write SHALL NOT automatically call `log_visual_asset_ready_registry_entry()`.

#### Scenario: Ready event is needed
- **WHEN** an explicit workflow needs to notify downstream consumers
- **THEN** it SHALL call the ready-event writer intentionally and SHALL handle duplicate-event policy in tests.

### Requirement: Registry read surfaces are UI-neutral
The system SHALL expose lifecycle status, display profile, review flags, lineage fields, renderer targets, and safety flags without requiring UI layers to inspect renderer payloads.

#### Scenario: UI or agent reads registry summary
- **WHEN** a UI, CLI, or agent reads Visual/Skin registry summary data
- **THEN** it SHALL receive lifecycle counts and status display profiles from backend payloads.

#### Scenario: Unknown or review-required status appears
- **WHEN** a registry entry is not ready for renderer consumption
- **THEN** the backend payload SHALL expose review or construction state so UI layers can show a safe non-ready state.
