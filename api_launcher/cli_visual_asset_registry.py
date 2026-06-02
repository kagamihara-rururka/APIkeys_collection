from __future__ import annotations

import argparse
import json

from api_launcher.db import resolve_project_path
from api_launcher.visual_asset_registry_persistence import (
    visual_asset_registry_summary_for_owned_test_database,
)


def add_visual_asset_registry_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--visual-registry-summary-db",
        default="",
        help="owned test SQLite database to summarize for Visual/Skin registry debug JSON",
    )
    parser.add_argument(
        "--visual-registry-summary-json",
        action="store_true",
        help="emit Visual/Skin registry summary JSON from an owned test database",
    )
    parser.add_argument(
        "--visual-registry-owned-test-db",
        action="store_true",
        help="explicitly acknowledge --visual-registry-summary-db is an RRKAL owned test database",
    )


def visual_asset_registry_command_active(args: argparse.Namespace) -> bool:
    return bool(args.visual_registry_summary_json or args.visual_registry_summary_db)


def run_visual_asset_registry_cli(args: argparse.Namespace) -> None:
    if not args.visual_registry_summary_json:
        return
    if not args.visual_registry_summary_db:
        raise RuntimeError("--visual-registry-summary-json requires --visual-registry-summary-db PATH")

    summary = visual_asset_registry_summary_for_owned_test_database(
        resolve_project_path(args.visual_registry_summary_db),
        allow_owned_test_database=bool(args.visual_registry_owned_test_db),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


__all__ = [
    "add_visual_asset_registry_args",
    "run_visual_asset_registry_cli",
    "visual_asset_registry_command_active",
]
