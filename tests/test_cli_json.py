from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from api_launcher.cli_json import cli_json_dumps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIRECT_JSON_STDOUT_PATTERN = re.compile(r"print\s*\(\s*json\.dumps")


class CliJsonTests(unittest.TestCase):
    def test_cli_json_dumps_escapes_unicode_for_stdout_streams(self) -> None:
        payload = {
            "label": "可展示小閉環",
            "status_icon": "🚧",
        }

        encoded = cli_json_dumps(payload)
        decoded = json.loads(encoded)

        self.assertTrue(encoded.isascii())
        self.assertEqual(payload, decoded)

    def test_api_launcher_json_stdout_uses_cli_helper(self) -> None:
        offenders: list[str] = []
        for path in sorted((PROJECT_ROOT / "api_launcher").rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if DIRECT_JSON_STDOUT_PATTERN.search(text):
                offenders.append(path.relative_to(PROJECT_ROOT).as_posix())

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
