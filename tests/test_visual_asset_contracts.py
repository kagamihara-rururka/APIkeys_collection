from __future__ import annotations

import unittest
from pathlib import Path

from api_launcher.visual_asset_contracts import (
    SKIN_ASSET_LIFECYCLE_STATUSES,
    CuratedDataAssetReference,
    RendererSkinAssetReference,
    SkinAssetLifecycleStatus,
    SkinBuildRequest,
    SkinBuildResult,
    VisualAssetReadyEvent,
    skin_asset_status_label,
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
        self.assertEqual("skin-gebco-2025", result_payload["skin_asset"]["skin_asset_id"])
        self.assertEqual("state/visual_assets/skin-gebco-2025.manifest.json", result_payload["skin_asset"]["manifest_path"])
        self.assertEqual(["external_builder_output"], result_payload["warning_codes"])
        self.assertEqual("visual_asset_ready", event_payload["event_type"])
        self.assertEqual("ready", event_payload["skin_asset"]["lifecycle_status"])
        self.assertNotIn("payload_bytes", str(event_payload))
        self.assertNotIn("renderer_import", str(event_payload))

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

    def test_contract_module_does_not_import_renderer_projects(self) -> None:
        source = Path("api_launcher/visual_asset_contracts.py").read_text(encoding="utf-8")
        forbidden = ("RRKAL_displaytools", "rrkal_visual_compressor", "vis_2_dis", "taichi", "PyQt")
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
