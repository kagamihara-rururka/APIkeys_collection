from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.assetcard_governance_checkpoint import build_assetcard_governance_checkpoint


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "assetcard_governance_checkpoint.py"


class AssetCardGovernanceCheckpointTests(unittest.TestCase):
    def test_wrapper_stdout_is_pure_json_and_keeps_gate_partial(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
            timeout=60,
        )

        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("assetcard_governance_checkpoint.v1", payload["schema"])
        self.assertEqual("partial", payload["core_gate_status"])
        self.assertIs(payload["checkpoint_passed"], True)

    def test_checkpoint_reports_required_docs_and_redaction_docs(self) -> None:
        payload = build_assetcard_governance_checkpoint(ROOT)

        self.assertEqual("passed", payload["status"])
        self.assertIs(payload["assetcard_governance_docs_present"], True)
        self.assertIs(payload["redaction_docs_present"], True)
        self.assertEqual([], payload["missing_docs"])
        self.assertIn("redaction_fixture_matrix", payload["docs"])
        self.assertIn("redaction_fixture_packet_design", payload["docs"])

    def test_checkpoint_does_not_claim_export_api_or_integration(self) -> None:
        payload = build_assetcard_governance_checkpoint(ROOT)

        self.assertIs(payload["export_query_api_exists"], False)
        self.assertIs(payload["json_fixture_driver_exists"], False)
        self.assertIs(payload["cross_repo_integration"], False)
        self.assertIs(payload["payload_exposure"], False)
        self.assertIs(payload["private_path_exposure"], False)
        self.assertIs(payload["odoriba_consumption_claim"], False)
        self.assertIs(payload["boundary"]["exports_assetcards"], False)
        self.assertIs(payload["boundary"]["runs_fixture_packets"], False)
        self.assertIs(payload["boundary"]["imports_downstream_repos"], False)


if __name__ == "__main__":
    unittest.main()
