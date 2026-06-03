from __future__ import annotations

import os
import tempfile
import unittest

from api_launcher.core_json_diagnostic_sweep_plan import (
    build_core_json_diagnostic_sweep_plan,
    classify_core_json_sweep_db_path,
)
from api_launcher.core_json_diagnostics_catalog import (
    core_json_diagnostic_flags,
    core_json_diagnostic_schema_versions,
)


class CoreJsonDiagnosticSweepPlanTests(unittest.TestCase):
    def test_sweep_plan_uses_explicit_db_for_all_catalog_flags(self) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "rrkal_core_json_sweep_test.sqlite")
        plans = build_core_json_diagnostic_sweep_plan(db_path)
        versions = core_json_diagnostic_schema_versions()

        self.assertEqual(core_json_diagnostic_flags(), tuple(plan.flag for plan in plans))
        for plan in plans:
            with self.subTest(flag=plan.flag):
                self.assertTrue(plan.uses_explicit_db)
                self.assertEqual("local_temp", plan.db_path_kind)
                self.assertEqual(versions[plan.flag], plan.schema_version)
                self.assertEqual(("APIkeys_collection.py", "--db", db_path, plan.flag), plan.launcher_args)

    def test_db_path_classifier_marks_cloud_drives_as_risky_for_sweeps(self) -> None:
        cloud_paths = (
            r"L:\RRKAL_project\state\launcher.sqlite",
            r"L:/RRKAL_project/state/launcher.sqlite",
            "L:",
            r"K:\APIkeys_collection\state\launcher.sqlite",
            r"K:/APIkeys_collection/state/launcher.sqlite",
            "K:",
        )

        for path in cloud_paths:
            with self.subTest(path=path):
                self.assertEqual("cloud_drive", classify_core_json_sweep_db_path(path))

    def test_db_path_classifier_accepts_temp_path(self) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "rrkal_core_json_sweep_test.sqlite")

        self.assertEqual("local_temp", classify_core_json_sweep_db_path(db_path))


if __name__ == "__main__":
    unittest.main()
