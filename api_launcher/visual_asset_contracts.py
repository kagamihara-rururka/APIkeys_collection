from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from api_launcher.db import utc_now_iso


VISUAL_ASSET_CONTRACT_SCHEMA_VERSION = 1


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
        "ready_count": status_counts.get(SkinAssetLifecycleStatus.READY.value, 0),
        "review_required_count": review_required_count,
        "renderer_target_counts": renderer_target_counts,
        "control_plane_only": True,
        "payload_loading": False,
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
    "renderer_skin_asset_manifest_projection",
    "skin_asset_status_display_profile",
    "skin_asset_status_label",
    "visual_asset_ready_event_from_registry_entry",
    "visual_asset_ready_event_log_context",
    "visual_asset_registry_summary",
]
