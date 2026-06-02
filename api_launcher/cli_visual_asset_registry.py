from __future__ import annotations

import argparse
from pathlib import Path

from api_launcher.cli_json import print_cli_json
from api_launcher.db import resolve_project_path
from api_launcher.visual_asset_event_logging import (
    log_visual_asset_ready_from_owned_test_database,
)
from api_launcher.visual_asset_registry_persistence import (
    visual_asset_registry_summary_for_owned_test_database,
)


def add_visual_asset_registry_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--visual-registry-db",
        default="",
        help="owned test SQLite database for Visual/Skin registry debug workflows",
    )
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
        help="explicitly acknowledge the Visual/Skin registry DB is an RRKAL owned test database",
    )
    parser.add_argument(
        "--visual-registry-entry-id",
        default="",
        help="Visual/Skin registry entry id for explicit ready-event debug workflows",
    )
    parser.add_argument(
        "--visual-registry-emit-ready-event-json",
        action="store_true",
        help="explicitly emit visual_asset_ready for one persisted ready registry entry and print JSON",
    )
    parser.add_argument(
        "--visual-registry-event-log",
        default="",
        help="event JSONL path for --visual-registry-emit-ready-event-json",
    )
    parser.add_argument(
        "--visual-registry-allow-duplicate-event",
        action="store_true",
        help="allow duplicate visual_asset_ready event emission for the same registry entry",
    )


def visual_asset_registry_command_active(args: argparse.Namespace) -> bool:
    return bool(
        args.visual_registry_summary_json
        or args.visual_registry_emit_ready_event_json
        or args.visual_registry_summary_db
        or args.visual_registry_db
    )


def run_visual_asset_registry_cli(args: argparse.Namespace) -> None:
    if args.visual_registry_summary_json:
        _run_visual_asset_registry_summary_json(args)
        return
    if args.visual_registry_emit_ready_event_json:
        _run_visual_asset_registry_ready_event_json(args)


def _run_visual_asset_registry_summary_json(args: argparse.Namespace) -> None:
    db_path = _visual_registry_db_path(args)
    summary = visual_asset_registry_summary_for_owned_test_database(
        db_path,
        allow_owned_test_database=bool(args.visual_registry_owned_test_db),
    )
    print_cli_json(summary, sort_keys=True)


def _run_visual_asset_registry_ready_event_json(args: argparse.Namespace) -> None:
    if not args.visual_registry_entry_id:
        raise RuntimeError("--visual-registry-emit-ready-event-json requires --visual-registry-entry-id ENTRY_ID")

    log_path = (
        resolve_project_path(args.visual_registry_event_log)
        if args.visual_registry_event_log
        else None
    )
    record = log_visual_asset_ready_from_owned_test_database(
        _visual_registry_db_path(args),
        args.visual_registry_entry_id,
        allow_owned_test_database=bool(args.visual_registry_owned_test_db),
        duplicate_policy=(
            "allow_duplicate"
            if args.visual_registry_allow_duplicate_event
            else "reject_existing"
        ),
        log_path=log_path,
    )
    payload = record.to_dict() if hasattr(record, "to_dict") else record
    print_cli_json(payload, sort_keys=True)


def _visual_registry_db_path(args: argparse.Namespace) -> Path:
    db_path = args.visual_registry_db or args.visual_registry_summary_db
    if not db_path:
        raise RuntimeError(
            "Visual registry command requires --visual-registry-db PATH "
            "or --visual-registry-summary-db PATH"
        )
    return resolve_project_path(db_path)


__all__ = [
    "add_visual_asset_registry_args",
    "run_visual_asset_registry_cli",
    "visual_asset_registry_command_active",
]
