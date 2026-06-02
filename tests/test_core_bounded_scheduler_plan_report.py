from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from api_launcher.cli_flags import command_requested
from api_launcher.core import parse_args
from api_launcher.core_bounded_scheduler_plan_report import (
    CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
    build_core_bounded_scheduler_plan_report,
)
from api_launcher.core_scheduler_contracts import (
    CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION,
    SCHEDULER_JOB_STATUS_VALUES,
    scheduler_job_contract_draft,
    scheduler_lifecycle_event_emission_guard_contract,
    scheduler_next_action_payload_contract,
    scheduler_o1_review_gate_contract,
)
from api_launcher.core_scheduler_persistence_contract import (
    CORE_SCHEDULER_QUEUE_SCHEMA_VERSION,
    CORE_SCHEDULER_QUEUE_TABLE_NAME,
    OWNED_TEST_DATABASE_MARKER_TABLE,
    create_scheduler_queue_table_for_owned_test_database,
    scheduler_queue_sqlite_ddl_preview,
)


class CoreBoundedSchedulerPlanReportTests(unittest.TestCase):
    def test_report_is_conservative_and_schema_stable(self) -> None:
        report = build_core_bounded_scheduler_plan_report()

        self.assertEqual(
            CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
            report["schema_version"],
        )
        self.assertEqual("partial", report["status"])
        self.assertFalse(
            report["integration_planning_gate"]["ready_for_scheduler_runtime_poc"]
        )
        self.assertIn(
            "scheduler_contract_not_bound_to_runtime_or_persistence",
            report["missing_evidence"],
        )
        self.assertIn(
            "durable_job_queue_persistence_not_promoted_beyond_owned_test",
            report["missing_evidence"],
        )
        self.assertIn(
            "treating_tk_thread_policy_registry_as_full_scheduler",
            report["blocked_surfaces"],
        )
        self.assertIn(
            "bounded_scheduler_openspec",
            report["planned_surfaces"],
        )
        self.assertFalse(report["safety"]["implements_scheduler_runtime"])
        self.assertFalse(report["safety"]["changes_scheduler_schema"])
        self.assertFalse(report["safety"]["changes_lifecycle_schema"])
        self.assertFalse(report["safety"]["enables_auto_lifecycle_events"])
        self.assertFalse(report["safety"]["cross_repo_implementation"])

    def test_existing_evidence_lists_tk_lanes_and_sqlite_gate(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        evidence = report["existing_evidence"]

        lanes = evidence["tk_policy_registry"]["lanes"]
        lane_by_id = {lane["policy_id"]: lane for lane in lanes}
        self.assertGreaterEqual(evidence["tk_policy_registry"]["policy_count"], 8)
        self.assertEqual(1, lane_by_id["sqlite_import"]["max_active_jobs"])
        self.assertEqual(4, lane_by_id["crawler_asset"]["max_active_jobs"])

        gate = evidence["sqlite_write_gate"]
        self.assertEqual("process_per_sqlite_path", gate["scope"])
        self.assertEqual(1, gate["max_active_writers_per_database"])
        self.assertIn("download_plan_import", gate["protects"])

        single_flight = evidence["single_flight_contract"]
        self.assertEqual("TkBackgroundJobStartResult", single_flight["contract"])
        self.assertEqual(
            ("started", "duplicate", "capacity"),
            tuple(single_flight["outcomes"]),
        )

    def test_scheduler_lane_contract_coverage_is_partial_and_conservative(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        coverage = report["existing_evidence"]["scheduler_lane_contract_coverage"]

        self.assertEqual("scheduler_lane_contract_coverage.v1", coverage["schema_version"])
        self.assertEqual("partial", coverage["status"])
        self.assertFalse(coverage["safety"]["treats_tk_policy_registry_as_full_scheduler"])
        self.assertFalse(coverage["safety"]["implements_scheduler_runtime"])
        self.assertIn("concurrency_policy", coverage["covered_policy_facets"])
        self.assertIn("write_policy", coverage["covered_policy_facets"])
        self.assertIn("timeout_policy", coverage["missing_policy_facets"])
        self.assertIn("retry_policy", coverage["missing_policy_facets"])
        self.assertIn("cancellation_policy", coverage["missing_policy_facets"])
        self.assertIn("review_policy", coverage["missing_policy_facets"])

        lanes = {lane["policy_id"]: lane for lane in coverage["lanes"]}
        self.assertEqual(
            ("concurrency_policy",),
            tuple(lanes["crawler_asset"]["covered_contract_facets"]),
        )
        self.assertIn("write_policy", lanes["crawler_asset"]["missing_contract_facets"])
        self.assertEqual(
            ("concurrency_policy", "write_policy"),
            tuple(lanes["sqlite_import"]["covered_contract_facets"]),
        )
        self.assertNotIn("write_policy", lanes["sqlite_import"]["missing_contract_facets"])
        self.assertEqual(
            "define_scheduler_lane_contract_before_runtime_scheduler",
            lanes["sqlite_import"]["next_action"],
        )

    def test_cli_json_stdout_is_parseable_and_command_requested(self) -> None:
        args = parse_args(["--core-bounded-scheduler-plan-json"])
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
                    "--core-bounded-scheduler-plan-json",
                ],
                cwd=Path.cwd(),
                check=True,
                capture_output=True,
                encoding="utf-8",
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(
            CORE_BOUNDED_SCHEDULER_PLAN_SCHEMA_VERSION,
            payload["schema_version"],
        )
        self.assertEqual("partial", payload["status"])
        self.assertEqual("", completed.stderr)
        self.assertFalse(payload["safety"]["implements_scheduler_runtime"])

    def test_scheduler_contract_draft_is_reported_without_runtime_claims(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        contract = report["existing_evidence"]["scheduler_job_contract_draft"]

        self.assertEqual(
            CORE_SCHEDULER_JOB_CONTRACT_SCHEMA_VERSION,
            contract["schema_version"],
        )
        self.assertEqual("contract_only", contract["status"])
        self.assertEqual("not_implemented", contract["runtime_status"])
        self.assertEqual("not_implemented", contract["persistence_status"])
        self.assertEqual("scheduler_only_not_lifecycle", contract["status_scope"])
        self.assertFalse(contract["safety"]["implements_scheduler_runtime"])
        self.assertFalse(contract["safety"]["defines_durable_queue_schema"])
        self.assertFalse(contract["safety"]["changes_lifecycle_schema"])
        self.assertFalse(contract["safety"]["enables_auto_lifecycle_events"])

        fields = {field["field_id"]: field for field in contract["fields"]}
        for required_field in (
            "job_id",
            "owner",
            "stage",
            "status",
            "concurrency_policy",
            "timeout_policy",
            "retry_policy",
            "cancellation_policy",
            "write_policy",
            "review_policy",
            "evidence_source",
            "next_action",
        ):
            self.assertIn(required_field, fields)
            self.assertTrue(fields[required_field]["required"])

        self.assertEqual(
            tuple(SCHEDULER_JOB_STATUS_VALUES),
            tuple(fields["status"]["allowed_values"]),
        )

    def test_scheduler_contract_draft_has_no_downstream_runtime_flags(self) -> None:
        contract = scheduler_job_contract_draft()
        safety = contract["safety"]

        self.assertFalse(safety["imports_renderer_projects"])
        self.assertFalse(safety["imports_compressor_projects"])
        self.assertFalse(safety["reads_renderer_payloads"])
        self.assertFalse(safety["reads_npz"])
        self.assertFalse(safety["cross_repo_implementation"])

    def test_scheduler_next_action_payload_contract_covers_blocked_review_timeout_retry_cancel(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        contract = report["existing_evidence"]["scheduler_next_action_payload_contract"]

        self.assertEqual(
            "core_scheduler_next_action_payload_contract.v1",
            contract["schema_version"],
        )
        self.assertEqual("contract_only", contract["status"])
        self.assertFalse(contract["safety"]["implements_scheduler_runtime"])
        self.assertFalse(contract["safety"]["changes_lifecycle_schema"])
        self.assertFalse(contract["safety"]["enables_auto_lifecycle_events"])

        payload_by_scenario = {
            payload["scenario"]: payload for payload in contract["payloads"]
        }
        self.assertEqual(
            {
                "cancelled_job",
                "retryable_failure",
                "timed_out_job",
                "review_required_job",
                "blocked_job",
            },
            set(payload_by_scenario),
        )
        self.assertEqual(
            "inspect_cancellation_reason_or_requeue",
            payload_by_scenario["cancelled_job"]["next_action"],
        )
        self.assertEqual(
            "retry_when_policy_allows",
            payload_by_scenario["retryable_failure"]["next_action"],
        )
        self.assertEqual(
            "review_timeout_policy_or_retry",
            payload_by_scenario["timed_out_job"]["next_action"],
        )
        self.assertEqual(
            "open_review_queue_before_continuing",
            payload_by_scenario["review_required_job"]["next_action"],
        )
        self.assertEqual(
            "review_blocked_job_reason_before_retry",
            payload_by_scenario["blocked_job"]["next_action"],
        )
        for payload in payload_by_scenario.values():
            self.assertIn(payload["scheduler_status"], SCHEDULER_JOB_STATUS_VALUES)
            self.assertTrue(payload["next_action"])
            self.assertTrue(payload["outcome_bucket"])

    def test_scheduler_next_action_payload_contract_has_no_downstream_runtime_flags(self) -> None:
        contract = scheduler_next_action_payload_contract()
        safety = contract["safety"]

        self.assertFalse(safety["implements_scheduler_runtime"])
        self.assertFalse(safety["changes_scheduler_schema"])
        self.assertFalse(safety["changes_lifecycle_schema"])
        self.assertFalse(safety["changes_lifecycle_statuses"])
        self.assertFalse(safety["enables_auto_lifecycle_events"])
        self.assertFalse(safety["imports_renderer_projects"])
        self.assertFalse(safety["imports_compressor_projects"])
        self.assertFalse(safety["reads_renderer_payloads"])
        self.assertFalse(safety["reads_npz"])
        self.assertFalse(safety["cross_repo_implementation"])

    def test_scheduler_lifecycle_event_guard_keeps_job_completion_explicit_only(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        guard = report["existing_evidence"]["scheduler_lifecycle_event_emission_guard"]

        self.assertEqual(
            "core_scheduler_lifecycle_event_emission_guard.v1",
            guard["schema_version"],
        )
        self.assertEqual("contract_only", guard["status"])
        self.assertEqual(
            "scheduler_completion_does_not_emit_visual_lifecycle_events",
            guard["scope"],
        )
        self.assertEqual("scheduler_only_not_lifecycle", guard["scheduler_status_scope"])
        self.assertIn("completed", guard["guarded_scheduler_statuses"])
        self.assertIn("completed", SCHEDULER_JOB_STATUS_VALUES)

        completed_policy = guard["completed_job_policy"]
        self.assertEqual("completed", completed_policy["scheduler_status"])
        self.assertFalse(completed_policy["auto_emit_lifecycle_event"])
        self.assertTrue(completed_policy["requires_explicit_event_writer"])
        self.assertEqual(
            "log_visual_asset_ready_registry_entry",
            completed_policy["explicit_event_writer"],
        )
        self.assertIn("scheduler_runtime_completion", guard["forbidden_implicit_call_sites"])
        self.assertIn(
            "automatic_lifecycle_event_emission",
            guard["o1_review_required_for"],
        )
        self.assertFalse(guard["safety"]["calls_visual_asset_ready_writer"])
        self.assertFalse(guard["safety"]["emits_lifecycle_events"])
        self.assertFalse(guard["safety"]["enables_auto_lifecycle_events"])

    def test_scheduler_lifecycle_event_guard_has_no_downstream_runtime_flags(self) -> None:
        guard = scheduler_lifecycle_event_emission_guard_contract()
        safety = guard["safety"]

        self.assertFalse(safety["implements_scheduler_runtime"])
        self.assertFalse(safety["changes_scheduler_schema"])
        self.assertFalse(safety["changes_lifecycle_schema"])
        self.assertFalse(safety["changes_lifecycle_statuses"])
        self.assertFalse(safety["emits_lifecycle_events"])
        self.assertFalse(safety["enables_auto_lifecycle_events"])
        self.assertFalse(safety["calls_visual_asset_ready_writer"])
        self.assertFalse(safety["imports_renderer_projects"])
        self.assertFalse(safety["imports_compressor_projects"])
        self.assertFalse(safety["reads_renderer_payloads"])
        self.assertFalse(safety["reads_npz"])
        self.assertFalse(safety["cross_repo_implementation"])

    def test_scheduler_o1_review_gate_contract_blocks_future_runtime_work(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        gate_contract = report["existing_evidence"]["scheduler_o1_review_gate_contract"]

        self.assertEqual(
            "core_scheduler_o1_review_gate_contract.v1",
            gate_contract["schema_version"],
        )
        self.assertEqual("contract_only", gate_contract["status"])
        self.assertEqual(
            "required_before_future_runtime_work",
            gate_contract["gate_status"],
        )
        self.assertEqual(
            {
                "durable_queue_schema",
                "lifecycle_event_emission_change",
                "cross_repo_job_adapter",
                "asyncio_runtime_migration",
            },
            set(gate_contract["required_gate_ids"]),
        )

        gates = {gate["gate_id"]: gate for gate in gate_contract["gates"]}
        self.assertEqual(
            "any_durable_queue_schema_or_migration",
            gates["durable_queue_schema"]["required_before"],
        )
        self.assertEqual(
            "any_scheduler_to_visual_lifecycle_event_binding",
            gates["lifecycle_event_emission_change"]["required_before"],
        )
        self.assertEqual(
            "any_cross_repo_scheduler_or_builder_job_adapter",
            gates["cross_repo_job_adapter"]["required_before"],
        )
        self.assertEqual(
            "any_asyncio_runtime_migration_or_worker_pool_replacement",
            gates["asyncio_runtime_migration"]["required_before"],
        )
        self.assertFalse(any(gate["safe_without_review"] for gate in gates.values()))

    def test_scheduler_o1_review_gate_contract_has_no_runtime_or_integration_flags(self) -> None:
        gate_contract = scheduler_o1_review_gate_contract()
        safety = gate_contract["safety"]

        self.assertFalse(safety["implements_scheduler_runtime"])
        self.assertFalse(safety["changes_scheduler_schema"])
        self.assertFalse(safety["changes_lifecycle_schema"])
        self.assertFalse(safety["changes_lifecycle_statuses"])
        self.assertFalse(safety["emits_lifecycle_events"])
        self.assertFalse(safety["enables_auto_lifecycle_events"])
        self.assertFalse(safety["adds_cross_repo_job_adapter"])
        self.assertFalse(safety["starts_asyncio_runtime_migration"])
        self.assertFalse(safety["imports_renderer_projects"])
        self.assertFalse(safety["imports_compressor_projects"])
        self.assertFalse(safety["reads_renderer_payloads"])
        self.assertFalse(safety["reads_npz"])
        self.assertFalse(safety["cross_repo_implementation"])

    def test_scheduler_queue_ddl_preview_is_dry_run_only(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        preview = report["existing_evidence"]["scheduler_queue_ddl_preview"]

        self.assertEqual(CORE_SCHEDULER_QUEUE_SCHEMA_VERSION, preview["schema_version"])
        self.assertEqual(CORE_SCHEDULER_QUEUE_TABLE_NAME, preview["table_name"])
        self.assertEqual("sqlite_ddl_dry_run", preview["preview_type"])
        self.assertEqual("not_materialized", preview["persistence_status"])
        self.assertTrue(preview["dry_run"])
        self.assertFalse(preview["creates_database_state"])
        self.assertFalse(preview["connects_to_database"])
        self.assertFalse(preview["auto_lifecycle_event_emission"])
        self.assertGreaterEqual(preview["column_count"], 12)
        self.assertIn("CREATE TABLE IF NOT EXISTS", preview["table_sql"])
        self.assertNotIn("payload_bytes", preview["table_sql"])
        self.assertNotIn("npz_payload", preview["table_sql"])

    def test_scheduler_queue_ddl_preview_has_no_runtime_or_lifecycle_flags(self) -> None:
        preview = scheduler_queue_sqlite_ddl_preview()
        safety = preview["safety"]

        self.assertFalse(safety["implements_scheduler_runtime"])
        self.assertFalse(safety["creates_database_state"])
        self.assertFalse(safety["user_database_write_allowed"])
        self.assertFalse(safety["changes_lifecycle_schema"])
        self.assertFalse(safety["changes_lifecycle_statuses"])
        self.assertFalse(safety["enables_auto_lifecycle_events"])
        self.assertFalse(safety["imports_renderer_projects"])
        self.assertFalse(safety["imports_compressor_projects"])
        self.assertFalse(safety["reads_renderer_payloads"])
        self.assertFalse(safety["reads_npz"])
        self.assertFalse(safety["cross_repo_implementation"])

    def test_scheduler_queue_owned_test_table_creation_requires_explicit_gate(self) -> None:
        report = build_core_bounded_scheduler_plan_report()
        helper = report["existing_evidence"]["scheduler_owned_test_table_helper"]
        self.assertEqual("owned_test_database_only", helper["scope"])
        self.assertTrue(helper["requires_allow_owned_test_database"])
        self.assertTrue(helper["rejects_existing_unowned_database"])
        self.assertFalse(helper["writes_job_rows"])
        self.assertFalse(helper["implements_scheduler_runtime"])
        self.assertFalse(helper["user_database_write_allowed"])
        self.assertFalse(helper["auto_lifecycle_event_emission"])

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "scheduler.sqlite"

            with self.assertRaisesRegex(ValueError, "allow_owned_test_database=True"):
                create_scheduler_queue_table_for_owned_test_database(db_path)

            self.assertFalse(db_path.exists())

    def test_scheduler_queue_owned_test_table_materializes_schema_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "scheduler.sqlite"

            result = create_scheduler_queue_table_for_owned_test_database(
                db_path,
                allow_owned_test_database=True,
            )

            self.assertEqual("create_scheduler_queue_table_for_owned_test_database", result["operation"])
            self.assertTrue(result["creates_database_state"])
            self.assertFalse(result["dry_run"])
            self.assertEqual("owned_test_database_only", result["scope"])
            self.assertTrue(result["table_exists"])
            self.assertTrue(result["marker_table_exists"])
            self.assertFalse(result["writes_job_rows"])
            self.assertFalse(result["auto_lifecycle_event_emission"])
            self.assertFalse(result["implements_scheduler_runtime"])
            self.assertFalse(result["payload_loading"])

            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                table_names = {
                    row["name"]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }
                columns = [
                    row["name"]
                    for row in conn.execute(
                        f'PRAGMA table_info("{CORE_SCHEDULER_QUEUE_TABLE_NAME}")'
                    ).fetchall()
                ]

            self.assertIn(CORE_SCHEDULER_QUEUE_TABLE_NAME, table_names)
            self.assertIn(OWNED_TEST_DATABASE_MARKER_TABLE, table_names)
            self.assertIn("job_id", columns)
            self.assertIn("status", columns)
            self.assertNotIn("payload_bytes", columns)
            self.assertNotIn("npz_payload", columns)

    def test_scheduler_queue_owned_test_table_rejects_existing_unowned_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "user.sqlite"
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("CREATE TABLE user_data (id INTEGER PRIMARY KEY)")
                conn.commit()

            with self.assertRaisesRegex(ValueError, "unowned existing SQLite database"):
                create_scheduler_queue_table_for_owned_test_database(
                    db_path,
                    allow_owned_test_database=True,
                )

            with closing(sqlite3.connect(db_path)) as conn:
                table_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }

            self.assertEqual({"user_data"}, table_names)


if __name__ == "__main__":
    unittest.main()
