from __future__ import annotations

import json
import unittest

from api_launcher.cli_json import cli_json_dumps


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


if __name__ == "__main__":
    unittest.main()
