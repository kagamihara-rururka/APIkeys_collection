from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.core_manifest_reference_report import build_core_manifest_reference_report


def add_core_manifest_reference_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-manifest-reference-report-json",
        action="store_true",
        help="emit RRKAL Core manifest-reference readiness evidence as JSON",
    )


def core_manifest_reference_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_manifest_reference_report_json)


def run_core_manifest_reference_cli(args: argparse.Namespace, repository: Any) -> None:
    if args.core_manifest_reference_report_json:
        print_cli_json(build_core_manifest_reference_report(repository), sort_keys=True)


__all__ = [
    "add_core_manifest_reference_args",
    "core_manifest_reference_command_active",
    "run_core_manifest_reference_cli",
]
