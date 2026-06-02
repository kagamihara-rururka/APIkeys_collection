from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.core_readiness_report import build_core_readiness_report


def add_core_readiness_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-readiness-report-json",
        action="store_true",
        help="emit RRKAL Core registry/lifecycle readiness evidence as JSON",
    )


def core_readiness_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_readiness_report_json)


def run_core_readiness_cli(args: argparse.Namespace, repository: Any) -> None:
    if args.core_readiness_report_json:
        print_cli_json(build_core_readiness_report(repository), sort_keys=True)


__all__ = [
    "add_core_readiness_args",
    "core_readiness_command_active",
    "run_core_readiness_cli",
]
