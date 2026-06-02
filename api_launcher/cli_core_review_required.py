from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.core_review_required_report import build_core_review_required_report


def add_core_review_required_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-review-required-report-json",
        action="store_true",
        help="emit RRKAL Core review-required evidence as JSON",
    )


def core_review_required_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_review_required_report_json)


def run_core_review_required_cli(args: argparse.Namespace, repository: Any) -> None:
    if args.core_review_required_report_json:
        print_cli_json(build_core_review_required_report(repository), sort_keys=True)


__all__ = [
    "add_core_review_required_args",
    "core_review_required_command_active",
    "run_core_review_required_cli",
]
