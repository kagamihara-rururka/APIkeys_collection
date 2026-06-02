from __future__ import annotations

import argparse

from api_launcher.cli_json import print_cli_json
from api_launcher.core_deep_adapter_coverage_report import build_core_deep_adapter_coverage_report


def add_core_deep_adapter_coverage_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-deep-adapter-coverage-json",
        action="store_true",
        help="emit RRKAL Core source-crawler versus deep-adapter coverage evidence as JSON",
    )


def core_deep_adapter_coverage_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_deep_adapter_coverage_json)


def run_core_deep_adapter_coverage_cli(args: argparse.Namespace) -> None:
    if args.core_deep_adapter_coverage_json:
        print_cli_json(build_core_deep_adapter_coverage_report(), sort_keys=True)


__all__ = [
    "add_core_deep_adapter_coverage_args",
    "core_deep_adapter_coverage_command_active",
    "run_core_deep_adapter_coverage_cli",
]
