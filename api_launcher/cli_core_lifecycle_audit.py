from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.core_lifecycle_audit_report import build_core_lifecycle_audit_report


def add_core_lifecycle_audit_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-lifecycle-audit-json",
        action="store_true",
        help="emit RRKAL Core lifecycle vocabulary/transition audit evidence as JSON",
    )


def core_lifecycle_audit_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_lifecycle_audit_json)


def run_core_lifecycle_audit_cli(args: argparse.Namespace, repository: Any) -> None:
    if args.core_lifecycle_audit_json:
        print_cli_json(build_core_lifecycle_audit_report(repository), sort_keys=True)


__all__ = [
    "add_core_lifecycle_audit_args",
    "core_lifecycle_audit_command_active",
    "run_core_lifecycle_audit_cli",
]
