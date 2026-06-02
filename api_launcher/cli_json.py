from __future__ import annotations

import json
from typing import Any


def cli_json_dumps(payload: Any, *, indent: int = 2, sort_keys: bool = False) -> str:
    """Serialize JSON for stdout in a Windows-pipe-safe form.

    File artifacts should keep using UTF-8 with ``ensure_ascii=False`` when
    human-readable Chinese labels are useful.  Stdout JSON is different: it is
    often piped between external processes in PowerShell, where legacy
    codepages can damage non-ASCII bytes before the next process parses them.
    ASCII escaping keeps the stream parseable while ``json.loads`` restores the
    original Unicode values for agents and tests.
    """

    return json.dumps(payload, ensure_ascii=True, indent=indent, sort_keys=sort_keys)


def print_cli_json(payload: Any, *, indent: int = 2, sort_keys: bool = False) -> None:
    print(cli_json_dumps(payload, indent=indent, sort_keys=sort_keys))


__all__ = [
    "cli_json_dumps",
    "print_cli_json",
]
