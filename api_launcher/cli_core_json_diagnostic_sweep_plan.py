from __future__ import annotations

import argparse

from api_launcher.cli_json import print_cli_json
from api_launcher.core_json_diagnostic_sweep_plan import (
    build_core_json_diagnostic_sweep_plan_report,
)


def add_core_json_diagnostic_sweep_plan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-json-diagnostic-sweep-plan-json",
        action="store_true",
        help="emit a non-executing RRKAL Core JSON diagnostic sweep command plan as JSON",
    )


def core_json_diagnostic_sweep_plan_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_json_diagnostic_sweep_plan_json)


def run_core_json_diagnostic_sweep_plan_cli(args: argparse.Namespace) -> None:
    if args.core_json_diagnostic_sweep_plan_json:
        print_cli_json(
            build_core_json_diagnostic_sweep_plan_report(args.db),
            sort_keys=True,
        )


__all__ = [
    "add_core_json_diagnostic_sweep_plan_args",
    "core_json_diagnostic_sweep_plan_command_active",
    "run_core_json_diagnostic_sweep_plan_cli",
]
