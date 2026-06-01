from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from api_launcher.db import utc_now_iso


VISUAL_ASSET_CONTRACT_SCHEMA_VERSION = 1
VISUAL_ASSET_REGISTRY_TABLE_NAME = "visual_skin_asset_registry"


class SkinAssetLifecycleStatus(str, Enum):
    """Lifecycle vocabulary for renderer-ready references managed by RRKAL Core."""

    PLANNED = "planned"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"
    CONSUMED_BY_RENDERER = "consumed_by_renderer"


SKIN_ASSET_LIFECYCLE_STATUSES = frozenset(status.value for status in SkinAssetLifecycleStatus)


@dataclass(frozen=True)
class CuratedDataAssetReference:
    # RRKAL Core tracks the curated source of a visual asset, not renderer payload bytes.
    curated_asset_id: str
    dataset_uid: str
    provider_id: str = ""
    dataset_id: str = ""
    version: str = ""
    manifest_path: str = ""
    sha256: str = ""
    lineage_role: str = "source_data"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
            "curated_asset_id": self.curated_asset_id,
            "dataset_uid": self.dataset_uid,
            "provider_id": self.provider_id,
            "dataset_id": self.dataset_id,
            "version": self.version,
            "manifest_path": self.manifest_path,
            "sha256": self.sha256,
            "lineage_role": self.lineage_role,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SkinBuildRequest:
    # A build request is a control-plane job contract; builders live outside RRKAL Core.
    request_id: str
    source_asset: CuratedDataAssetReference
    requested_skin_type: str
    renderer_targets: tuple[str, ...]
    build_profile_id: str = ""
    bounds_signature: str = ""
    priority: str = "normal"
    review_required: bool = False
    requested_by: str = "rrkal_core"
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
            "request_id": self.request_id,
            "source_asset": self.source_asset.to_dict(),
            "requested_skin_type": self.requested_skin_type,
            "renderer_targets": list(self.renderer_targets),
            "build_profile_id": self.build_profile_id,
            "bounds_signature": self.bounds_signature,
            "priority": self.priority,
            "review_required": self.review_required,
            "requested_by": self.requested_by,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RendererSkinAssetReference:
    # This is a manifest reference. It intentionally does not load .npz, tiles, GPU buffers, or renderer code.
    skin_asset_id: str
    source_request_id: str
    source_curated_asset_id: str
    dataset_uid: str
    manifest_path: str
    lifecycle_status: SkinAssetLifecycleStatus | str
    renderer_targets: tuple[str, ...]
    asset_format: str = ""
    checksum: str = ""
    size_bytes: int = 0
    generated_by: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_lifecycle_status(self.lifecycle_status)

    @property
    def status(self) -> str:
        return _status_value(self.lifecycle_status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
            "skin_asset_id": self.skin_asset_id,
            "source_request_id": self.source_request_id,
            "source_curated_asset_id": self.source_curated_asset_id,
            "dataset_uid": self.dataset_uid,
            "manifest_path": self.manifest_path,
            "lifecycle_status": self.status,
            "lifecycle_status_display_profile": skin_asset_status_display_profile(self.status),
            "renderer_targets": list(self.renderer_targets),
            "asset_format": self.asset_format,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "generated_by": self.generated_by,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SkinBuildResult:
    # Build result records lifecycle and provenance. It does not imply RRKAL built or opened the skin payload.
    request_id: str
    lifecycle_status: SkinAssetLifecycleStatus | str
    skin_asset: RendererSkinAssetReference | None = None
    error_message: str = ""
    warning_codes: tuple[str, ...] = ()
    review_required: bool = False
    completed_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_lifecycle_status(self.lifecycle_status)

    @property
    def status(self) -> str:
        return _status_value(self.lifecycle_status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
            "request_id": self.request_id,
            "lifecycle_status": self.status,
            "lifecycle_status_display_profile": skin_asset_status_display_profile(self.status),
            "skin_asset": self.skin_asset.to_dict() if self.skin_asset else None,
            "error_message": self.error_message,
            "warning_codes": list(self.warning_codes),
            "review_required": self.review_required,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class VisualAssetReadyEvent:
    # Event payload sent when a renderer-ready reference can be consumed by another project.
    event_id: str
    skin_asset: RendererSkinAssetReference
    source_request_id: str
    emitted_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_type": "visual_asset_ready",
            "source_request_id": self.source_request_id,
            "skin_asset": self.skin_asset.to_dict(),
            "emitted_at": self.emitted_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RendererSkinAssetRegistryEntry:
    """RRKAL Core registry row for a renderer-ready manifest reference.

    The registry entry deliberately stores only control-plane metadata. It may
    point at a skin manifest, but it must not open renderer payloads, GPU
    buffers, or project files.
    """

    registry_entry_id: str
    skin_asset: RendererSkinAssetReference
    source_request: SkinBuildRequest | None = None
    latest_build_result: SkinBuildResult | None = None
    review_required: bool = False
    registered_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_registry_entry_lineage(self)

    @property
    def status(self) -> str:
        return self.skin_asset.status

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
            "registry_entry_id": self.registry_entry_id,
            "lifecycle_status": self.status,
            "lifecycle_status_label": skin_asset_status_label(self.status),
            "lifecycle_status_display_profile": skin_asset_status_display_profile(self.status),
            "manifest_path": self.skin_asset.manifest_path,
            "source_curated_asset_id": self.skin_asset.source_curated_asset_id,
            "dataset_uid": self.skin_asset.dataset_uid,
            "renderer_targets": list(self.skin_asset.renderer_targets),
            "review_required": self.review_required,
            "skin_asset": self.skin_asset.to_dict(),
            "source_request": self.source_request.to_dict() if self.source_request else None,
            "latest_build_result": self.latest_build_result.to_dict() if self.latest_build_result else None,
            "registered_at": self.registered_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
            "control_plane_only": True,
            "payload_loading": False,
        }


@dataclass(frozen=True)
class VisualAssetRegistryColumn:
    """Column contract for future visual asset registry persistence.

    This descriptor is intentionally schema-only. It lets RRKAL Core document
    which control-plane fields may be persisted without creating tables,
    opening renderer payloads, or emitting lifecycle events automatically.
    """

    name: str
    storage_type: str
    required: bool
    source: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "storage_type": self.storage_type,
            "required": self.required,
            "source": self.source,
            "description": self.description,
        }


def visual_asset_registry_summary(entries: Iterable[RendererSkinAssetRegistryEntry]) -> dict[str, Any]:
    """Summarize registry entries without inspecting renderer payloads."""

    registry_entries = tuple(entries)
    status_counts = {status: 0 for status in sorted(SKIN_ASSET_LIFECYCLE_STATUSES)}
    renderer_target_counts: dict[str, int] = {}
    review_required_count = 0

    for entry in registry_entries:
        status_counts[entry.status] = status_counts.get(entry.status, 0) + 1
        if entry.review_required or entry.status == SkinAssetLifecycleStatus.REVIEW_REQUIRED.value:
            review_required_count += 1
        for target in entry.skin_asset.renderer_targets:
            renderer_target_counts[target] = renderer_target_counts.get(target, 0) + 1

    return {
        "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
        "registry_entry_count": len(registry_entries),
        "status_counts": status_counts,
        "status_display_profiles": {
            status: skin_asset_status_display_profile(status)
            for status in sorted(SKIN_ASSET_LIFECYCLE_STATUSES)
        },
        "ready_count": status_counts.get(SkinAssetLifecycleStatus.READY.value, 0),
        "review_required_count": review_required_count,
        "renderer_target_counts": renderer_target_counts,
        "control_plane_only": True,
        "payload_loading": False,
    }


VISUAL_ASSET_REGISTRY_COLUMNS: tuple[VisualAssetRegistryColumn, ...] = (
    VisualAssetRegistryColumn(
        "registry_entry_id",
        "TEXT",
        True,
        "RendererSkinAssetRegistryEntry.registry_entry_id",
        "Stable primary key for the RRKAL control-plane registry row.",
    ),
    VisualAssetRegistryColumn(
        "skin_asset_id",
        "TEXT",
        True,
        "RendererSkinAssetReference.skin_asset_id",
        "External renderer skin asset reference id; not a payload locator by itself.",
    ),
    VisualAssetRegistryColumn(
        "lifecycle_status",
        "TEXT",
        True,
        "RendererSkinAssetReference.lifecycle_status",
        "Lifecycle vocabulary value used for display, filtering, and ready-event guards.",
    ),
    VisualAssetRegistryColumn(
        "manifest_path",
        "TEXT",
        True,
        "RendererSkinAssetReference.manifest_path",
        "Path to a renderer-safe manifest reference; RRKAL Core must not open payload bytes here.",
    ),
    VisualAssetRegistryColumn(
        "source_request_id",
        "TEXT",
        True,
        "RendererSkinAssetReference.source_request_id",
        "Skin build request lineage id.",
    ),
    VisualAssetRegistryColumn(
        "source_curated_asset_id",
        "TEXT",
        True,
        "RendererSkinAssetReference.source_curated_asset_id",
        "Curated data asset lineage id.",
    ),
    VisualAssetRegistryColumn(
        "dataset_uid",
        "TEXT",
        True,
        "RendererSkinAssetReference.dataset_uid",
        "RRKAL dataset uid used to trace the upstream data asset.",
    ),
    VisualAssetRegistryColumn(
        "renderer_targets_json",
        "TEXT",
        True,
        "RendererSkinAssetReference.renderer_targets",
        "JSON array of renderer targets allowed to consume this manifest reference.",
    ),
    VisualAssetRegistryColumn(
        "review_required",
        "INTEGER",
        True,
        "RendererSkinAssetRegistryEntry.review_required",
        "Boolean review gate; stored as 0/1 by concrete persistence layers.",
    ),
    VisualAssetRegistryColumn(
        "checksum",
        "TEXT",
        False,
        "RendererSkinAssetReference.checksum",
        "Checksum of the manifest reference or external builder output, when provided.",
    ),
    VisualAssetRegistryColumn(
        "size_bytes",
        "INTEGER",
        False,
        "RendererSkinAssetReference.size_bytes",
        "Declared manifest or artifact size, not loaded by this contract.",
    ),
    VisualAssetRegistryColumn(
        "registered_at",
        "TEXT",
        True,
        "RendererSkinAssetRegistryEntry.registered_at",
        "UTC timestamp for first registry entry creation.",
    ),
    VisualAssetRegistryColumn(
        "updated_at",
        "TEXT",
        True,
        "RendererSkinAssetRegistryEntry.updated_at",
        "UTC timestamp for latest registry entry update.",
    ),
    VisualAssetRegistryColumn(
        "metadata_json",
        "TEXT",
        False,
        "RendererSkinAssetRegistryEntry.metadata",
        "Bounded control-plane metadata serialized by a concrete persistence layer.",
    ),
)


VISUAL_ASSET_REGISTRY_INDEXES: tuple[dict[str, Any], ...] = (
    {"name": "idx_visual_skin_asset_registry_status", "columns": ("lifecycle_status",), "unique": False},
    {"name": "idx_visual_skin_asset_registry_dataset", "columns": ("dataset_uid",), "unique": False},
    {"name": "idx_visual_skin_asset_registry_curated", "columns": ("source_curated_asset_id",), "unique": False},
    {"name": "idx_visual_skin_asset_registry_skin_asset", "columns": ("skin_asset_id",), "unique": False},
)


def visual_asset_registry_persistence_schema() -> dict[str, Any]:
    """Return the future persistence schema contract without creating storage.

    The concrete repository/migration layer should consume this only after an
    OpenSpec or migration guard exists. Keeping it here prevents UI or renderer
    code from inventing a divergent registry table shape.
    """

    return {
        "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
        "table_name": VISUAL_ASSET_REGISTRY_TABLE_NAME,
        "persistence_status": "schema_contract_only",
        "primary_key": "registry_entry_id",
        "columns": [column.to_dict() for column in VISUAL_ASSET_REGISTRY_COLUMNS],
        "indexes": [
            {**index, "columns": list(index["columns"])}
            for index in VISUAL_ASSET_REGISTRY_INDEXES
        ],
        "allowed_lifecycle_statuses": sorted(SKIN_ASSET_LIFECYCLE_STATUSES),
        "migration_guards": {
            "create_table_automatically": False,
            "payload_columns_allowed": False,
            "auto_event_emission": False,
            "event_writer": "log_visual_asset_ready_registry_entry",
            "requires_explicit_migration": True,
        },
        "safety": {
            "control_plane_only": True,
            "payload_loading": False,
            "imports_renderer_projects": False,
            "reads_npz_or_gpu_buffers": False,
        },
    }


def visual_asset_registry_entry_persistence_record(entry: RendererSkinAssetRegistryEntry) -> dict[str, Any]:
    """Project a registry entry into one flat persistence row without writing it.

    The future repository layer can store this row after an explicit migration
    exists. This helper keeps the flattening rules near the schema contract and
    avoids each UI/CLI/repository path inventing its own row shape.
    """

    return {
        "registry_entry_id": entry.registry_entry_id,
        "skin_asset_id": entry.skin_asset.skin_asset_id,
        "lifecycle_status": entry.status,
        "manifest_path": entry.skin_asset.manifest_path,
        "source_request_id": entry.skin_asset.source_request_id,
        "source_curated_asset_id": entry.skin_asset.source_curated_asset_id,
        "dataset_uid": entry.skin_asset.dataset_uid,
        "renderer_targets_json": _json_dumps_control_plane(list(entry.skin_asset.renderer_targets)),
        "review_required": 1 if entry.review_required else 0,
        "checksum": entry.skin_asset.checksum,
        "size_bytes": entry.skin_asset.size_bytes,
        "registered_at": entry.registered_at,
        "updated_at": entry.updated_at,
        "metadata_json": _json_dumps_control_plane(_bounded_registry_metadata(entry.metadata)),
    }


def renderer_skin_asset_manifest_projection(entry: RendererSkinAssetRegistryEntry) -> dict[str, Any]:
    """Project a registry entry into a compact cross-project manifest reference.

    This envelope is intentionally smaller than ``entry.to_dict()``. It is the
    payload RRKAL Core can hand to displaytools, a future skin builder, or an
    event log without exposing source request internals or touching renderer
    payload bytes.
    """

    skin_asset = entry.skin_asset
    return {
        "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
        "projection_type": "renderer_skin_asset_manifest_reference",
        "registry_entry_id": entry.registry_entry_id,
        "skin_asset_id": skin_asset.skin_asset_id,
        "manifest_path": skin_asset.manifest_path,
        "lifecycle_status": skin_asset.status,
        "lifecycle_status_label": skin_asset_status_label(skin_asset.status),
        "lifecycle_status_display_profile": skin_asset_status_display_profile(skin_asset.status),
        "renderer_targets": list(skin_asset.renderer_targets),
        "asset_format": skin_asset.asset_format,
        "checksum": skin_asset.checksum,
        "size_bytes": skin_asset.size_bytes,
        "generated_by": skin_asset.generated_by,
        "review_required": entry.review_required,
        "registered_at": entry.registered_at,
        "updated_at": entry.updated_at,
        "lineage": {
            "source_request_id": skin_asset.source_request_id,
            "source_curated_asset_id": skin_asset.source_curated_asset_id,
            "dataset_uid": skin_asset.dataset_uid,
        },
        "safety": {
            "control_plane_only": True,
            "payload_loading": False,
            "imports_renderer_projects": False,
        },
    }


def visual_asset_ready_event_from_registry_entry(
    entry: RendererSkinAssetRegistryEntry,
    *,
    event_id: str = "",
    emitted_at: str = "",
    metadata: dict[str, Any] | None = None,
) -> VisualAssetReadyEvent:
    """Create a ready event from a registry entry without hand-written lineage ids."""

    if entry.status != SkinAssetLifecycleStatus.READY.value:
        raise ValueError("VisualAssetReadyEvent can only be emitted for ready skin assets")
    event_metadata = dict(metadata or {})
    event_metadata.setdefault("registry_entry_id", entry.registry_entry_id)
    event_metadata.setdefault("projection_type", "renderer_skin_asset_manifest_reference")
    return VisualAssetReadyEvent(
        event_id=event_id or f"visual-ready:{entry.skin_asset.skin_asset_id}",
        skin_asset=entry.skin_asset,
        source_request_id=entry.skin_asset.source_request_id,
        emitted_at=emitted_at or utc_now_iso(),
        metadata=event_metadata,
    )


def visual_asset_ready_event_log_context(event: VisualAssetReadyEvent) -> dict[str, Any]:
    """Return a bounded event-log context for a visual-ready notification.

    ``VisualAssetReadyEvent.to_dict()`` is intentionally richer than the event
    log context because it preserves caller metadata. Event logs should only
    carry the stable manifest reference fields needed for audit and follow-up,
    never arbitrary metadata or renderer payload hints.
    """

    skin_asset = event.skin_asset
    metadata = event.metadata
    allowed_metadata = {
        key: metadata[key]
        for key in ("registry_entry_id", "projection_type")
        if key in metadata and metadata[key]
    }
    return {
        "schema_version": VISUAL_ASSET_CONTRACT_SCHEMA_VERSION,
        "event_type": "visual_asset_ready",
        "event_id": event.event_id,
        "source_request_id": event.source_request_id,
        "skin_asset_id": skin_asset.skin_asset_id,
        "manifest_path": skin_asset.manifest_path,
        "lifecycle_status": skin_asset.status,
        "lifecycle_status_label": skin_asset_status_label(skin_asset.status),
        "lifecycle_status_display_profile": skin_asset_status_display_profile(skin_asset.status),
        "renderer_targets": list(skin_asset.renderer_targets),
        "asset_format": skin_asset.asset_format,
        "checksum": skin_asset.checksum,
        "size_bytes": skin_asset.size_bytes,
        "generated_by": skin_asset.generated_by,
        "emitted_at": event.emitted_at,
        "lineage": {
            "source_request_id": skin_asset.source_request_id,
            "source_curated_asset_id": skin_asset.source_curated_asset_id,
            "dataset_uid": skin_asset.dataset_uid,
        },
        "metadata": allowed_metadata,
        "safety": {
            "control_plane_only": True,
            "payload_loading": False,
            "imports_renderer_projects": False,
            "arbitrary_metadata_logged": False,
        },
    }


def skin_asset_status_label(status: SkinAssetLifecycleStatus | str) -> str:
    return _SKIN_ASSET_STATUS_LABELS.get(_status_value(status), "皮層資產狀態待確認")


def skin_asset_status_display_profile(status: SkinAssetLifecycleStatus | str) -> dict[str, Any]:
    """Return UI-neutral display metadata for a visual/skin lifecycle status."""

    value = _status_value(status)
    profile = dict(_SKIN_ASSET_STATUS_DISPLAY_PROFILES.get(value, _UNKNOWN_SKIN_ASSET_STATUS_DISPLAY_PROFILE))
    profile["status"] = value
    profile["display_label"] = skin_asset_status_label(value)
    return profile


def _validate_lifecycle_status(status: SkinAssetLifecycleStatus | str) -> None:
    value = _status_value(status)
    if value not in SKIN_ASSET_LIFECYCLE_STATUSES:
        raise ValueError(f"Unsupported skin asset lifecycle status: {value}")


def _validate_registry_entry_lineage(entry: RendererSkinAssetRegistryEntry) -> None:
    skin_asset = entry.skin_asset
    if entry.source_request:
        if entry.source_request.request_id != skin_asset.source_request_id:
            raise ValueError(
                "Renderer skin registry entry source_request.request_id must match skin_asset.source_request_id"
            )
        source_curated_id = entry.source_request.source_asset.curated_asset_id
        if source_curated_id and source_curated_id != skin_asset.source_curated_asset_id:
            raise ValueError(
                "Renderer skin registry entry source_request source asset must match skin_asset.source_curated_asset_id"
            )
    if entry.latest_build_result:
        if entry.latest_build_result.request_id != skin_asset.source_request_id:
            raise ValueError(
                "Renderer skin registry entry latest_build_result.request_id must match skin_asset.source_request_id"
            )
        result_skin_asset = entry.latest_build_result.skin_asset
        if result_skin_asset and result_skin_asset.skin_asset_id != skin_asset.skin_asset_id:
            raise ValueError(
                "Renderer skin registry entry latest_build_result.skin_asset must match skin_asset.skin_asset_id"
            )


def _status_value(status: SkinAssetLifecycleStatus | str) -> str:
    if isinstance(status, SkinAssetLifecycleStatus):
        return status.value
    return str(status or "").strip()


def _json_dumps_control_plane(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _bounded_registry_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Keep metadata persistence small and free of obvious payload/secret keys."""

    blocked_fragments = ("payload", "secret", "token", "api_key", "password", "npz", "gpu_buffer")
    bounded: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized_key = str(key)
        lowered = normalized_key.lower()
        if any(fragment in lowered for fragment in blocked_fragments):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            bounded[normalized_key] = value
        elif isinstance(value, (list, tuple)):
            scalar_items = [
                item
                for item in value
                if isinstance(item, (str, int, float, bool)) or item is None
            ]
            if len(scalar_items) == len(value):
                bounded[normalized_key] = scalar_items
    return bounded


_SKIN_ASSET_STATUS_LABELS = {
    SkinAssetLifecycleStatus.PLANNED.value: "已規劃",
    SkinAssetLifecycleStatus.BUILDING.value: "建立中",
    SkinAssetLifecycleStatus.READY.value: "可供 renderer 使用",
    SkinAssetLifecycleStatus.FAILED.value: "建立失敗",
    SkinAssetLifecycleStatus.REVIEW_REQUIRED.value: "需審核",
    SkinAssetLifecycleStatus.REJECTED.value: "已拒絕",
    SkinAssetLifecycleStatus.CONSUMED_BY_RENDERER.value: "已被 renderer 消費",
}


_SKIN_ASSET_STATUS_DISPLAY_PROFILES: dict[str, dict[str, Any]] = {
    SkinAssetLifecycleStatus.PLANNED.value: {
        "status_icon": "🚧",
        "display_tone": "neutral",
        "next_action": "等待建立皮層資產",
        "is_ready": False,
        "is_terminal": False,
        "review_required": False,
        "construction": True,
    },
    SkinAssetLifecycleStatus.BUILDING.value: {
        "status_icon": "◐",
        "display_tone": "warning",
        "next_action": "等待外部 builder 完成",
        "is_ready": False,
        "is_terminal": False,
        "review_required": False,
        "construction": True,
    },
    SkinAssetLifecycleStatus.READY.value: {
        "status_icon": "✓",
        "display_tone": "success",
        "next_action": "可交給 renderer 消費",
        "is_ready": True,
        "is_terminal": False,
        "review_required": False,
        "construction": False,
    },
    SkinAssetLifecycleStatus.FAILED.value: {
        "status_icon": "!",
        "display_tone": "danger",
        "next_action": "檢查 build error 並重新排程",
        "is_ready": False,
        "is_terminal": True,
        "review_required": True,
        "construction": False,
    },
    SkinAssetLifecycleStatus.REVIEW_REQUIRED.value: {
        "status_icon": "🚧",
        "display_tone": "review",
        "next_action": "進入人工審核",
        "is_ready": False,
        "is_terminal": False,
        "review_required": True,
        "construction": True,
    },
    SkinAssetLifecycleStatus.REJECTED.value: {
        "status_icon": "!",
        "display_tone": "danger",
        "next_action": "保留紀錄並停止交付",
        "is_ready": False,
        "is_terminal": True,
        "review_required": False,
        "construction": False,
    },
    SkinAssetLifecycleStatus.CONSUMED_BY_RENDERER.value: {
        "status_icon": "✓",
        "display_tone": "success",
        "next_action": "記錄 renderer 消費狀態",
        "is_ready": True,
        "is_terminal": False,
        "review_required": False,
        "construction": False,
    },
}


_UNKNOWN_SKIN_ASSET_STATUS_DISPLAY_PROFILE: dict[str, Any] = {
    "status_icon": "?",
    "display_tone": "neutral",
    "next_action": "確認皮層資產狀態",
    "is_ready": False,
    "is_terminal": False,
    "review_required": True,
    "construction": True,
}


__all__ = [
    "CuratedDataAssetReference",
    "RendererSkinAssetReference",
    "RendererSkinAssetRegistryEntry",
    "SKIN_ASSET_LIFECYCLE_STATUSES",
    "SkinAssetLifecycleStatus",
    "SkinBuildRequest",
    "SkinBuildResult",
    "VISUAL_ASSET_CONTRACT_SCHEMA_VERSION",
    "VisualAssetReadyEvent",
    "VisualAssetRegistryColumn",
    "VISUAL_ASSET_REGISTRY_COLUMNS",
    "VISUAL_ASSET_REGISTRY_INDEXES",
    "VISUAL_ASSET_REGISTRY_TABLE_NAME",
    "renderer_skin_asset_manifest_projection",
    "skin_asset_status_display_profile",
    "skin_asset_status_label",
    "visual_asset_ready_event_from_registry_entry",
    "visual_asset_ready_event_log_context",
    "visual_asset_registry_entry_persistence_record",
    "visual_asset_registry_persistence_schema",
    "visual_asset_registry_summary",
]
