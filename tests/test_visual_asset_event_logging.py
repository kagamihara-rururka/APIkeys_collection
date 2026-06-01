from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from api_launcher.event_log import latest_events
from api_launcher.visual_asset_contracts import (
    RendererSkinAssetReference,
    RendererSkinAssetRegistryEntry,
    SkinAssetLifecycleStatus,
    VisualAssetReadyEvent,
)
from api_launcher.visual_asset_event_logging import log_visual_asset_ready_event, log_visual_asset_ready_registry_entry


class VisualAssetEventLoggingTests(unittest.TestCase):
    def test_ready_event_log_writer_uses_bounded_context(self) -> None:
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
            asset_format="renderer_skin_asset_manifest",
            checksum="abc123",
            size_bytes=4096,
            generated_by="external_builder",
            metadata={"payload_bytes": "do-not-log"},
        )
        event = VisualAssetReadyEvent(
            event_id="visual-ready-1",
            skin_asset=skin_asset,
            source_request_id="request-ready",
            emitted_at="2026-06-02T00:04:00Z",
            metadata={
                "registry_entry_id": "entry-ready",
                "projection_type": "renderer_skin_asset_manifest_reference",
                "token": "secret",
                "payload_bytes": "bad",
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            record = log_visual_asset_ready_event(event, log_path=log_path)
            events = latest_events(log_path=log_path)

        self.assertEqual("visual_asset_ready", record.event)
        self.assertEqual(1, len(events))
        context = events[0]["context"]
        self.assertEqual("visual_asset", events[0]["component"])
        self.assertEqual("visual_asset_ready", events[0]["event"])
        self.assertEqual("skin-ready", context["skin_asset_id"])
        self.assertEqual("state/visual_assets/ready.manifest.json", context["manifest_path"])
        self.assertEqual("request-ready", context["lineage"]["source_request_id"])
        self.assertEqual(
            {
                "registry_entry_id": "entry-ready",
                "projection_type": "renderer_skin_asset_manifest_reference",
            },
            context["metadata"],
        )
        self.assertTrue(context["safety"]["control_plane_only"])
        self.assertFalse(context["safety"]["payload_loading"])
        self.assertFalse(context["safety"]["imports_renderer_projects"])
        self.assertNotIn("token", str(events[0]))
        self.assertNotIn("payload_bytes", str(events[0]))
        self.assertNotIn("do-not-log", str(events[0]))

    def test_ready_event_log_writer_accepts_injected_logger(self) -> None:
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
        )
        event = VisualAssetReadyEvent(
            event_id="visual-ready-1",
            skin_asset=skin_asset,
            source_request_id="request-ready",
        )
        calls: list[dict[str, object]] = []

        def fake_logger(event_name: str, message: str, **kwargs: object) -> dict[str, object]:
            call = {"event": event_name, "message": message, **kwargs}
            calls.append(call)
            return call

        returned = log_visual_asset_ready_event(event, log_event_func=fake_logger)

        self.assertIs(returned, calls[0])
        self.assertEqual("visual_asset_ready", calls[0]["event"])
        self.assertEqual("Visual asset manifest reference is ready.", calls[0]["message"])
        self.assertEqual("visual_asset", calls[0]["component"])
        self.assertNotIn("log_path", calls[0])
        self.assertEqual("skin-ready", calls[0]["context"]["skin_asset_id"])  # type: ignore[index]

    def test_ready_registry_entry_log_writer_creates_event_and_context(self) -> None:
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
        )
        entry = RendererSkinAssetRegistryEntry("entry-ready", skin_asset)

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "events.jsonl"
            log_visual_asset_ready_registry_entry(
                entry,
                emitted_at="2026-06-02T00:05:00Z",
                metadata={"note": "do-not-log"},
                log_path=log_path,
            )
            events = latest_events(log_path=log_path)

        self.assertEqual(1, len(events))
        context = events[0]["context"]
        self.assertEqual("visual-ready:skin-ready", context["event_id"])
        self.assertEqual("entry-ready", context["metadata"]["registry_entry_id"])
        self.assertEqual("renderer_skin_asset_manifest_reference", context["metadata"]["projection_type"])
        self.assertNotIn("do-not-log", str(context))

    def test_ready_registry_entry_log_writer_rejects_non_ready_entry(self) -> None:
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-review",
            source_request_id="request-review",
            source_curated_asset_id="curated-review",
            dataset_uid="dataset-review",
            manifest_path="state/visual_assets/review.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.REVIEW_REQUIRED,
            renderer_targets=("displaytools",),
        )
        entry = RendererSkinAssetRegistryEntry("entry-review", skin_asset)

        with self.assertRaisesRegex(ValueError, "ready skin assets"):
            log_visual_asset_ready_registry_entry(entry)


if __name__ == "__main__":
    unittest.main()
