from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from api_launcher.event_log import log_event
from api_launcher.visual_asset_contracts import (
    RendererSkinAssetRegistryEntry,
    VisualAssetReadyEvent,
    visual_asset_ready_event_from_registry_entry,
    visual_asset_ready_event_log_context,
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


__all__ = ["log_visual_asset_ready_event", "log_visual_asset_ready_registry_entry"]
