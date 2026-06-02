from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from api_launcher.event_log import latest_events
from api_launcher.event_log import log_event
from api_launcher.visual_asset_contracts import (
    RendererSkinAssetRegistryEntry,
    VisualAssetReadyEvent,
    visual_asset_ready_event_from_registry_entry,
    visual_asset_ready_event_log_context,
)
from api_launcher.visual_asset_registry_persistence import (
    read_visual_asset_registry_entry_for_owned_test_database,
)


LogEventFunc = Callable[..., Any]


def log_visual_asset_ready_event(
    event: VisualAssetReadyEvent,
    *,
    log_event_func: LogEventFunc = log_event,
    log_path: Path | None = None,
) -> Any:
    """Write a visual-ready event using the bounded RRKAL Core context.

    This adapter is intentionally explicit: importing the module does not write
    logs, and callers may inject a test logger.  The context is produced by the
    visual asset contract layer so arbitrary event metadata or renderer payload
    hints never enter the event log.
    """

    kwargs: dict[str, Any] = {
        "level": "info",
        "component": "visual_asset",
        "context": visual_asset_ready_event_log_context(event),
    }
    if log_path is not None:
        kwargs["log_path"] = log_path
    return log_event_func(
        "visual_asset_ready",
        "Visual asset manifest reference is ready.",
        **kwargs,
    )


def log_visual_asset_ready_registry_entry(
    entry: RendererSkinAssetRegistryEntry,
    *,
    event_id: str = "",
    emitted_at: str = "",
    metadata: dict[str, Any] | None = None,
    log_event_func: LogEventFunc = log_event,
    log_path: Path | None = None,
) -> Any:
    """Create and write a ready event from a ready registry entry.

    This is the explicit one-call path future registry workflows can use after
    a skin asset becomes ready.  The underlying factory still rejects non-ready
    entries, so review/failed assets cannot accidentally emit a ready event.
    """

    event = visual_asset_ready_event_from_registry_entry(
        entry,
        event_id=event_id,
        emitted_at=emitted_at,
        metadata=metadata,
    )
    return log_visual_asset_ready_event(
        event,
        log_event_func=log_event_func,
        log_path=log_path,
    )


def log_visual_asset_ready_from_owned_test_database(
    sqlite_path: str | Path,
    registry_entry_id: str,
    *,
    allow_owned_test_database: bool = False,
    duplicate_policy: str = "reject_existing",
    max_duplicate_scan_events: int = 10_000,
    event_id: str = "",
    emitted_at: str = "",
    metadata: dict[str, Any] | None = None,
    log_event_func: LogEventFunc = log_event,
    log_path: Path | None = None,
) -> Any:
    """Explicitly emit `visual_asset_ready` for one persisted ready entry.

    Persistence write/upsert helpers never call this.  A workflow or CLI must
    opt in, name the entry, and acknowledge the owned-test database boundary.
    The default duplicate policy rejects an existing ready event for the same
    registry entry or skin asset within the bounded log scan window.
    """

    entry = read_visual_asset_registry_entry_for_owned_test_database(
        sqlite_path,
        registry_entry_id,
        allow_owned_test_database=allow_owned_test_database,
    )
    if entry is None:
        raise ValueError(f"Visual asset registry entry not found: {registry_entry_id}")

    _validate_duplicate_policy(duplicate_policy)
    if duplicate_policy == "reject_existing" and _visual_asset_ready_event_exists(
        entry,
        log_path=log_path,
        max_scan_events=max_duplicate_scan_events,
    ):
        raise ValueError(
            "A visual_asset_ready event already exists for this registry entry or skin asset"
        )

    return log_visual_asset_ready_registry_entry(
        entry,
        event_id=event_id,
        emitted_at=emitted_at,
        metadata=metadata,
        log_event_func=log_event_func,
        log_path=log_path,
    )


def _validate_duplicate_policy(value: str) -> None:
    if value not in {"reject_existing", "allow_duplicate"}:
        raise ValueError(
            "visual_asset_ready duplicate_policy must be 'reject_existing' or 'allow_duplicate'"
        )


def _visual_asset_ready_event_exists(
    entry: RendererSkinAssetRegistryEntry,
    *,
    log_path: Path | None,
    max_scan_events: int,
) -> bool:
    if max_scan_events < 1:
        raise ValueError("max_duplicate_scan_events must be >= 1 when duplicate rejection is enabled")

    for event in latest_events(limit=max_scan_events, log_path=log_path):
        if event.get("event") != "visual_asset_ready":
            continue
        context = event.get("context")
        if not isinstance(context, dict):
            continue
        metadata = context.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        if metadata.get("registry_entry_id") == entry.registry_entry_id:
            return True
        if context.get("skin_asset_id") == entry.skin_asset.skin_asset_id:
            return True
    return False


__all__ = [
    "log_visual_asset_ready_event",
    "log_visual_asset_ready_from_owned_test_database",
    "log_visual_asset_ready_registry_entry",
]
