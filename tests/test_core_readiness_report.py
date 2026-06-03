from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_readiness_report import (
    CORE_READINESS_SCHEMA_VERSION,
    _integration_planning_gate,
    build_core_readiness_report,
)
from api_launcher.core_readiness_sections import build_core_readiness_sections


class CoreReadinessReportTests(unittest.TestCase):
    def test_report_has_required_sections_and_safety_flags(self) -> None:
        report = build_core_readiness_report()

        self.assertEqual(CORE_READINESS_SCHEMA_VERSION, report["schema_version"])
        for section in (
            "registry_evidence",
            "lifecycle_evidence",
            "manifest_reference_evidence",
            "review_required_evidence",
            "job_status_evidence",
            "asset_lineage_evidence",
            "openspec_evidence",
            "integration_planning_gate",
        ):
            self.assertIn(section, report)

        self.assertTrue(report["safety"]["control_plane_only"])
        self.assertFalse(report["safety"]["imports_renderer_projects"])
        self.assertFalse(report["safety"]["imports_compressor_projects"])
        self.assertFalse(report["safety"]["reads_renderer_payloads"])
        self.assertFalse(report["safety"]["reads_npz"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_report_separates_evidence_categories(self) -> None:
        report = build_core_readiness_report()

        for section_name in (
            "registry_evidence",
            "lifecycle_evidence",
            "manifest_reference_evidence",
            "review_required_evidence",
            "job_status_evidence",
            "asset_lineage_evidence",
            "openspec_evidence",
        ):
            section = report[section_name]
            self.assertIn("existing_evidence", section)
            self.assertIn("missing_evidence", section)
            self.assertIn("blocked_surfaces", section)
            self.assertIn("review_required_surfaces", section)
            self.assertIn("contract_only_surfaces", section)
            self.assertIn("planned_surfaces", section)
            self.assertIn("next_safe_actions", section)

    def test_section_builder_matches_report_sections(self) -> None:
        sections = build_core_readiness_sections()
        report = build_core_readiness_report()

        expected_section_names = (
            "registry_evidence",
            "lifecycle_evidence",
            "manifest_reference_evidence",
            "review_required_evidence",
            "job_status_evidence",
            "asset_lineage_evidence",
            "openspec_evidence",
        )
        self.assertEqual(set(expected_section_names), set(sections))
        for section_name in expected_section_names:
            self.assertEqual(sections[section_name], report[section_name])

    def test_missing_or_contract_only_evidence_does_not_fake_ready_for_planning(self) -> None:
        report = build_core_readiness_report()
        gate = report["integration_planning_gate"]

        self.assertIn(gate["status"], {"partial", "not_ready"})
        self.assertNotEqual("ready_for_planning", gate["status"])
        self.assertIn("visual_skin_asset_registry_persistence", gate["contract_only_surfaces"])
        self.assertIn("unified_bounded_job_scheduler_not_yet_implemented", gate["missing_evidence"])
        self.assertIn("openspec_validate_result_not_embedded_in_report", gate["missing_evidence"])

    def test_integration_gate_aggregates_all_section_surface_buckets(self) -> None:
        report = build_core_readiness_report()
        sections = {key: value for key, value in report.items() if key.endswith("_evidence")}
        gate = report["integration_planning_gate"]

        self.assertEqual(_flatten_section_items(sections, "missing_evidence"), gate["missing_evidence"])
        self.assertEqual(_flatten_section_items(sections, "blocked_surfaces"), gate["blocked_reasons"])
        self.assertEqual(_flatten_section_items(sections, "contract_only_surfaces"), gate["contract_only_surfaces"])
        self.assertEqual(_flatten_section_items(sections, "planned_surfaces"), gate["planned_surfaces"])

    def test_integration_gate_stays_partial_for_any_incomplete_surface(self) -> None:
        complete_section = {
            "existing_evidence": {},
            "missing_evidence": (),
            "blocked_surfaces": (),
            "review_required_surfaces": (),
            "contract_only_surfaces": (),
            "planned_surfaces": (),
            "next_safe_actions": (),
        }
        self.assertEqual("ready_for_planning", _integration_planning_gate({"complete": complete_section})["status"])

        for key, value in (
            ("missing_evidence", ("missing_contract",)),
            ("blocked_surfaces", ("blocked_surface",)),
            ("contract_only_surfaces", ("contract_only_surface",)),
            ("planned_surfaces", ("future_surface",)),
        ):
            with self.subTest(key=key):
                section = dict(complete_section)
                section[key] = value
                self.assertEqual("partial", _integration_planning_gate({"incomplete": section})["status"])

    def test_registry_and_review_evidence_use_existing_reports(self) -> None:
        report = build_core_readiness_report()

        registry = report["registry_evidence"]["existing_evidence"]
        self.assertGreaterEqual(registry["crawler_registry"]["source_type_count"], 14)
        self.assertGreaterEqual(registry["content_registry"]["review_rule_count"], 1)
        self.assertGreaterEqual(registry["dataset_adapter_registry"]["dataset_adapter_count"], 3)

        review = report["review_required_evidence"]
        self.assertIn("unsupported_payload_format", review["blocked_surfaces"])
        self.assertTrue(review["existing_evidence"]["visual_review_status_available"])
        self.assertEqual(
            "core_review_item_identity_contract_draft.v1",
            review["existing_evidence"]["review_item_identity_contract_draft"]["schema_version"],
        )
        self.assertIn(
            "stable_review_item_identity_not_persisted",
            review["missing_evidence"],
        )
        self.assertIn(
            "core_review_item_identity_contract_draft",
            review["contract_only_surfaces"],
        )
        self.assertIn(
            "treating_display_counts_as_persisted_queue",
            review["blocked_surfaces"],
        )

    def test_job_status_evidence_includes_scheduler_contract_surfaces(self) -> None:
        report = build_core_readiness_report()
        job_status = report["job_status_evidence"]
        evidence = job_status["existing_evidence"]

        self.assertEqual(
            "core_scheduler_job_contract_draft.v1",
            evidence["scheduler_job_contract_draft"]["schema_version"],
        )
        self.assertEqual(
            "core_scheduler_queue_persistence_contract.v1",
            evidence["scheduler_queue_ddl_preview"]["schema_version"],
        )
        self.assertEqual(
            "owned_test_database_only",
            evidence["scheduler_owned_test_table_helper"]["scope"],
        )
        self.assertEqual(
            "core_scheduler_next_action_payload_contract.v1",
            evidence["scheduler_next_action_payload_contract"]["schema_version"],
        )
        self.assertEqual(
            "core_scheduler_lifecycle_event_emission_guard.v1",
            evidence["scheduler_lifecycle_event_emission_guard"]["schema_version"],
        )
        self.assertEqual(
            "core_scheduler_o1_review_gate_contract.v1",
            evidence["scheduler_o1_review_gate_contract"]["schema_version"],
        )
        self.assertIn(
            "durable_queue_schema",
            evidence["scheduler_o1_review_gate_contract"]["required_gate_ids"],
        )
        self.assertIn(
            "durable_job_queue_persistence_not_promoted_beyond_owned_test",
            job_status["missing_evidence"],
        )
        self.assertIn(
            "future_scheduler_runtime_changes_require_o1_review",
            job_status["blocked_surfaces"],
        )
        self.assertIn(
            "core_scheduler_o1_review_gate_contract",
            job_status["contract_only_surfaces"],
        )

    def test_openspec_evidence_is_inventory_only(self) -> None:
        report = build_core_readiness_report()
        openspec = report["openspec_evidence"]
        inventory = openspec["existing_evidence"]["openspec_inventory"]
        spec_ids = {entry["spec_id"] for entry in inventory["active_specs"]}

        self.assertEqual("core_openspec_evidence.v1", inventory["schema_version"])
        self.assertFalse(inventory["validation"]["executed_by_report"])
        self.assertFalse(inventory["safety"]["executes_openspec"])
        self.assertGreaterEqual(openspec["existing_evidence"]["active_spec_count"], 3)
        self.assertIn("bounded-scheduler-core-contract", spec_ids)
        self.assertIn("openspec_validate_result_not_embedded_in_report", openspec["missing_evidence"])
        self.assertIn("openspec_governance_inventory", openspec["contract_only_surfaces"])

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-readiness-report-json"])
        self.assertTrue(command_requested(args))

        with tempfile.TemporaryDirectory() as tmpdir:
            launcher_db = Path(tmpdir) / "launcher.sqlite"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "APIkeys_collection.py",
                    "--db",
                    str(launcher_db),
                    "--core-readiness-report-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(CORE_READINESS_SCHEMA_VERSION, payload["schema_version"])
        self.assertEqual("partial", payload["integration_planning_gate"]["status"])
        self.assertEqual("", completed.stderr)


def _flatten_section_items(sections: dict[str, dict[str, object]], key: str) -> list[str]:
    values = set()
    for section in sections.values():
        raw_items = section.get(key, ())
        values.update(str(item) for item in raw_items if item)
    return sorted(values)


if __name__ == "__main__":
    unittest.main()
