from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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


def skin_asset_status_label(status: SkinAssetLifecycleStatus | str) -> str:
    return _SKIN_ASSET_STATUS_LABELS.get(_status_value(status), "皮層資產狀態待確認")


def _validate_lifecycle_status(status: SkinAssetLifecycleStatus | str) -> None:
    value = _status_value(status)
    if value not in SKIN_ASSET_LIFECYCLE_STATUSES:
        raise ValueError(f"Unsupported skin asset lifecycle status: {value}")


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


__all__ = [
    "CuratedDataAssetReference",
    "RendererSkinAssetReference",
    "SKIN_ASSET_LIFECYCLE_STATUSES",
    "SkinAssetLifecycleStatus",
    "SkinBuildRequest",
    "SkinBuildResult",
    "VISUAL_ASSET_CONTRACT_SCHEMA_VERSION",
    "VisualAssetReadyEvent",
    "skin_asset_status_label",
]
