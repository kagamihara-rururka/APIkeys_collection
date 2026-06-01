from __future__ import annotations

import unittest
from pathlib import Path

from api_launcher.visual_asset_contracts import (
    SKIN_ASSET_LIFECYCLE_STATUSES,
    CuratedDataAssetReference,
    RendererSkinAssetReference,
    RendererSkinAssetRegistryEntry,
    SkinAssetLifecycleStatus,
    SkinBuildRequest,
    SkinBuildResult,
    VisualAssetReadyEvent,
    renderer_skin_asset_manifest_projection,
    skin_asset_status_display_profile,
    skin_asset_status_label,
    visual_asset_ready_event_from_registry_entry,
    visual_asset_ready_event_log_context,
    visual_asset_registry_summary,
)


class VisualAssetContractTest(unittest.TestCase):
    def test_lifecycle_status_values_are_fixed_control_plane_vocabulary(self) -> None:
        self.assertEqual(
            {
                "planned",
                "building",
                "ready",
                "failed",
                "review_required",
                "rejected",
                "consumed_by_renderer",
            },
            set(SKIN_ASSET_LIFECYCLE_STATUSES),
        )

    def test_build_request_serializes_source_reference_without_renderer_payload(self) -> None:
        source = CuratedDataAssetReference(
            curated_asset_id="curated-gebco-2025",
            dataset_uid="gebco:gebco_2025",
            provider_id="gebco",
            dataset_id="gebco_2025",
            version="2025",
            manifest_path="state/manifests/gebco_2025.manifest.json",
            sha256="abc123",
        )
        request = SkinBuildRequest(
            request_id="skin-build-1",
            source_asset=source,
            requested_skin_type="terrain_skin",
            renderer_targets=("displaytools", "taichi_global_bathymetry"),
            build_profile_id="terrain-default",
            bounds_signature="global",
            review_required=True,
            created_at="2026-06-01T00:00:00Z",
        )

        payload = request.to_dict()

        self.assertEqual(1, payload["schema_version"])
        self.assertEqual("skin-build-1", payload["request_id"])
        self.assertEqual("terrain_skin", payload["requested_skin_type"])
        self.assertEqual(["displaytools", "taichi_global_bathymetry"], payload["renderer_targets"])
        self.assertTrue(payload["review_required"])
        self.assertEqual("curated-gebco-2025", payload["source_asset"]["curated_asset_id"])
        self.assertEqual("state/manifests/gebco_2025.manifest.json", payload["source_asset"]["manifest_path"])
        self.assertNotIn("payload", payload)
        self.assertNotIn("npz", payload)

    def test_build_result_and_ready_event_reference_manifest_only(self) -> None:
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-gebco-2025",
            source_request_id="skin-build-1",
            source_curated_asset_id="curated-gebco-2025",
            dataset_uid="gebco:gebco_2025",
            manifest_path="state/visual_assets/skin-gebco-2025.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
            asset_format="renderer_skin_asset_manifest",
            checksum="def456",
            size_bytes=2048,
            generated_by="external_skin_builder",
            created_at="2026-06-01T00:10:00Z",
        )
        result = SkinBuildResult(
            request_id="skin-build-1",
            lifecycle_status="ready",
            skin_asset=skin_asset,
            warning_codes=("external_builder_output",),
            completed_at="2026-06-01T00:11:00Z",
        )
        event = VisualAssetReadyEvent(
            event_id="visual-ready-1",
            skin_asset=skin_asset,
            source_request_id="skin-build-1",
            emitted_at="2026-06-01T00:12:00Z",
        )

        result_payload = result.to_dict()
        event_payload = event.to_dict()

        self.assertEqual("ready", result_payload["lifecycle_status"])
        self.assertEqual("success", result_payload["lifecycle_status_display_profile"]["display_tone"])
        self.assertEqual("skin-gebco-2025", result_payload["skin_asset"]["skin_asset_id"])
        self.assertEqual("state/visual_assets/skin-gebco-2025.manifest.json", result_payload["skin_asset"]["manifest_path"])
        self.assertEqual(["external_builder_output"], result_payload["warning_codes"])
        self.assertEqual("visual_asset_ready", event_payload["event_type"])
        self.assertEqual("ready", event_payload["skin_asset"]["lifecycle_status"])
        self.assertNotIn("payload_bytes", str(event_payload))
        self.assertNotIn("renderer_import", str(event_payload))

    def test_build_result_display_profile_works_without_skin_asset(self) -> None:
        result = SkinBuildResult(
            request_id="skin-build-failed",
            lifecycle_status=SkinAssetLifecycleStatus.FAILED,
            error_message="builder failed",
            completed_at="2026-06-01T00:11:00Z",
        )

        payload = result.to_dict()

        self.assertEqual("failed", payload["lifecycle_status"])
        self.assertIsNone(payload["skin_asset"])
        self.assertEqual("danger", payload["lifecycle_status_display_profile"]["display_tone"])
        self.assertTrue(payload["lifecycle_status_display_profile"]["is_terminal"])
        self.assertFalse(payload["lifecycle_status_display_profile"]["is_ready"])

    def test_invalid_lifecycle_status_fails_fast(self) -> None:
        with self.assertRaises(ValueError):
            RendererSkinAssetReference(
                skin_asset_id="skin-1",
                source_request_id="request-1",
                source_curated_asset_id="curated-1",
                dataset_uid="dataset-1",
                manifest_path="state/visual_assets/skin-1.manifest.json",
                lifecycle_status="opened_in_renderer",
                renderer_targets=("displaytools",),
            )

    def test_status_label_is_ui_neutral_display_payload(self) -> None:
        self.assertEqual("可供 renderer 使用", skin_asset_status_label("ready"))
        self.assertEqual("皮層資產狀態待確認", skin_asset_status_label("future_status"))

    def test_status_display_profile_marks_ready_review_and_unknown_states(self) -> None:
        ready = skin_asset_status_display_profile(SkinAssetLifecycleStatus.READY)
        self.assertEqual("ready", ready["status"])
        self.assertEqual("✓", ready["status_icon"])
        self.assertEqual("success", ready["display_tone"])
        self.assertEqual("可供 renderer 使用", ready["display_label"])
        self.assertTrue(ready["is_ready"])
        self.assertFalse(ready["construction"])

        review = skin_asset_status_display_profile("review_required")
        self.assertEqual("🚧", review["status_icon"])
        self.assertEqual("review", review["display_tone"])
        self.assertTrue(review["review_required"])
        self.assertTrue(review["construction"])

        unknown = skin_asset_status_display_profile("future_status")
        self.assertEqual("?", unknown["status_icon"])
        self.assertEqual("neutral", unknown["display_tone"])
        self.assertEqual("皮層資產狀態待確認", unknown["display_label"])
        self.assertTrue(unknown["review_required"])

    def test_registry_entry_serializes_manifest_reference_without_payload_loading(self) -> None:
        source = CuratedDataAssetReference(
            curated_asset_id="curated-gebco-2025",
            dataset_uid="gebco:gebco_2025",
            provider_id="gebco",
            manifest_path="state/manifests/gebco_2025.manifest.json",
        )
        request = SkinBuildRequest(
            request_id="skin-build-1",
            source_asset=source,
            requested_skin_type="terrain_skin",
            renderer_targets=("displaytools",),
            created_at="2026-06-01T00:00:00Z",
        )
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-gebco-2025",
            source_request_id="skin-build-1",
            source_curated_asset_id="curated-gebco-2025",
            dataset_uid="gebco:gebco_2025",
            manifest_path="state/visual_assets/skin-gebco-2025.manifest.json",
            lifecycle_status="ready",
            renderer_targets=("displaytools",),
            checksum="def456",
            created_at="2026-06-01T00:10:00Z",
        )
        result = SkinBuildResult(
            request_id="skin-build-1",
            lifecycle_status="ready",
            skin_asset=skin_asset,
            completed_at="2026-06-01T00:11:00Z",
        )
        entry = RendererSkinAssetRegistryEntry(
            registry_entry_id="registry-skin-gebco-2025",
            skin_asset=skin_asset,
            source_request=request,
            latest_build_result=result,
            registered_at="2026-06-01T00:12:00Z",
            updated_at="2026-06-01T00:13:00Z",
        )

        payload = entry.to_dict()

        self.assertEqual("registry-skin-gebco-2025", payload["registry_entry_id"])
        self.assertEqual("ready", payload["lifecycle_status"])
        self.assertEqual("可供 renderer 使用", payload["lifecycle_status_label"])
        self.assertEqual("success", payload["lifecycle_status_display_profile"]["display_tone"])
        self.assertTrue(payload["lifecycle_status_display_profile"]["is_ready"])
        self.assertEqual("state/visual_assets/skin-gebco-2025.manifest.json", payload["manifest_path"])
        self.assertEqual(["displaytools"], payload["renderer_targets"])
        self.assertTrue(payload["control_plane_only"])
        self.assertFalse(payload["payload_loading"])
        self.assertNotIn(".npz", str(payload))
        self.assertNotIn("payload_bytes", str(payload))

    def test_registry_summary_counts_lifecycle_and_renderer_targets(self) -> None:
        ready_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools", "qt_preview"),
        )
        review_asset = RendererSkinAssetReference(
            skin_asset_id="skin-review",
            source_request_id="request-review",
            source_curated_asset_id="curated-review",
            dataset_uid="dataset-review",
            manifest_path="state/visual_assets/review.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.REVIEW_REQUIRED,
            renderer_targets=("displaytools",),
        )

        summary = visual_asset_registry_summary(
            (
                RendererSkinAssetRegistryEntry("entry-ready", ready_asset),
                RendererSkinAssetRegistryEntry("entry-review", review_asset, review_required=True),
            )
        )

        self.assertEqual(2, summary["registry_entry_count"])
        self.assertEqual(1, summary["ready_count"])
        self.assertEqual(1, summary["review_required_count"])
        self.assertEqual(1, summary["status_counts"]["ready"])
        self.assertEqual(1, summary["status_counts"]["review_required"])
        self.assertEqual("success", summary["status_display_profiles"]["ready"]["display_tone"])
        self.assertEqual("🚧", summary["status_display_profiles"]["review_required"]["status_icon"])
        self.assertEqual(2, summary["renderer_target_counts"]["displaytools"])
        self.assertEqual(1, summary["renderer_target_counts"]["qt_preview"])
        self.assertTrue(summary["control_plane_only"])
        self.assertFalse(summary["payload_loading"])

    def test_manifest_projection_is_compact_renderer_safe_reference(self) -> None:
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
        )
        entry = RendererSkinAssetRegistryEntry(
            "entry-ready",
            skin_asset,
            review_required=False,
            registered_at="2026-06-02T00:00:00Z",
            updated_at="2026-06-02T00:01:00Z",
        )

        projection = renderer_skin_asset_manifest_projection(entry)

        self.assertEqual("renderer_skin_asset_manifest_reference", projection["projection_type"])
        self.assertEqual("entry-ready", projection["registry_entry_id"])
        self.assertEqual("skin-ready", projection["skin_asset_id"])
        self.assertEqual("state/visual_assets/ready.manifest.json", projection["manifest_path"])
        self.assertEqual("ready", projection["lifecycle_status"])
        self.assertEqual("可供 renderer 使用", projection["lifecycle_status_label"])
        self.assertEqual("success", projection["lifecycle_status_display_profile"]["display_tone"])
        self.assertTrue(projection["lifecycle_status_display_profile"]["is_ready"])
        self.assertEqual(["displaytools"], projection["renderer_targets"])
        self.assertEqual("request-ready", projection["lineage"]["source_request_id"])
        self.assertTrue(projection["safety"]["control_plane_only"])
        self.assertFalse(projection["safety"]["payload_loading"])
        self.assertFalse(projection["safety"]["imports_renderer_projects"])
        self.assertNotIn("source_request", projection)
        self.assertNotIn("latest_build_result", projection)
        self.assertNotIn("payload_bytes", str(projection))

    def test_ready_event_factory_uses_registry_entry_lineage(self) -> None:
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

        event = visual_asset_ready_event_from_registry_entry(
            entry,
            emitted_at="2026-06-02T00:02:00Z",
            metadata={"note": "checked"},
        )
        payload = event.to_dict()

        self.assertEqual("visual-ready:skin-ready", payload["event_id"])
        self.assertEqual("visual_asset_ready", payload["event_type"])
        self.assertEqual("request-ready", payload["source_request_id"])
        self.assertEqual("entry-ready", payload["metadata"]["registry_entry_id"])
        self.assertEqual("renderer_skin_asset_manifest_reference", payload["metadata"]["projection_type"])
        self.assertEqual("checked", payload["metadata"]["note"])
        self.assertEqual("ready", payload["skin_asset"]["lifecycle_status"])
        self.assertNotIn("payload_bytes", str(payload))

    def test_ready_event_factory_rejects_non_ready_registry_entry(self) -> None:
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
            visual_asset_ready_event_from_registry_entry(entry)

    def test_ready_event_log_context_is_bounded_manifest_reference(self) -> None:
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
            emitted_at="2026-06-02T00:03:00Z",
            metadata={
                "registry_entry_id": "entry-ready",
                "projection_type": "renderer_skin_asset_manifest_reference",
                "note": "do-not-log",
                "token": "secret",
                "payload_bytes": "bad",
            },
        )

        context = visual_asset_ready_event_log_context(event)

        self.assertEqual("visual_asset_ready", context["event_type"])
        self.assertEqual("visual-ready-1", context["event_id"])
        self.assertEqual("skin-ready", context["skin_asset_id"])
        self.assertEqual("state/visual_assets/ready.manifest.json", context["manifest_path"])
        self.assertEqual("ready", context["lifecycle_status"])
        self.assertEqual(["displaytools"], context["renderer_targets"])
        self.assertEqual("request-ready", context["lineage"]["source_request_id"])
        self.assertEqual("curated-ready", context["lineage"]["source_curated_asset_id"])
        self.assertEqual("dataset-ready", context["lineage"]["dataset_uid"])
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
        self.assertFalse(context["safety"]["arbitrary_metadata_logged"])
        self.assertNotIn("token", str(context))
        self.assertNotIn("payload_bytes", str(context))
        self.assertNotIn("do-not-log", str(context))
        self.assertNotIn("skin_asset", context)

    def test_registry_entry_rejects_mismatched_source_request(self) -> None:
        source = CuratedDataAssetReference(
            curated_asset_id="curated-other",
            dataset_uid="dataset-ready",
        )
        request = SkinBuildRequest(
            request_id="request-other",
            source_asset=source,
            requested_skin_type="terrain_skin",
            renderer_targets=("displaytools",),
        )
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
        )

        with self.assertRaisesRegex(ValueError, "source_request.request_id"):
            RendererSkinAssetRegistryEntry("entry-ready", skin_asset, source_request=request)

    def test_registry_entry_rejects_mismatched_source_curated_asset(self) -> None:
        source = CuratedDataAssetReference(
            curated_asset_id="curated-other",
            dataset_uid="dataset-ready",
        )
        request = SkinBuildRequest(
            request_id="request-ready",
            source_asset=source,
            requested_skin_type="terrain_skin",
            renderer_targets=("displaytools",),
        )
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
        )

        with self.assertRaisesRegex(ValueError, "source asset"):
            RendererSkinAssetRegistryEntry("entry-ready", skin_asset, source_request=request)

    def test_registry_entry_rejects_mismatched_build_result_skin_asset(self) -> None:
        skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-ready",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/ready.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
        )
        other_skin_asset = RendererSkinAssetReference(
            skin_asset_id="skin-other",
            source_request_id="request-ready",
            source_curated_asset_id="curated-ready",
            dataset_uid="dataset-ready",
            manifest_path="state/visual_assets/other.manifest.json",
            lifecycle_status=SkinAssetLifecycleStatus.READY,
            renderer_targets=("displaytools",),
        )
        result = SkinBuildResult(
            request_id="request-ready",
            lifecycle_status="ready",
            skin_asset=other_skin_asset,
        )

        with self.assertRaisesRegex(ValueError, "latest_build_result.skin_asset"):
            RendererSkinAssetRegistryEntry("entry-ready", skin_asset, latest_build_result=result)

    def test_contract_module_does_not_import_renderer_projects(self) -> None:
        source = Path("api_launcher/visual_asset_contracts.py").read_text(encoding="utf-8")
        forbidden = ("RRKAL_displaytools", "rrkal_visual_compressor", "vis_2_dis", "taichi", "PyQt")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
