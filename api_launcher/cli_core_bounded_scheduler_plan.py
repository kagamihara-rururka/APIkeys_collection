from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.core_bounded_scheduler_plan_report import (
    build_core_bounded_scheduler_plan_report,
)


def add_core_bounded_scheduler_plan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-bounded-scheduler-plan-json",
        action="store_true",
        help="emit RRKAL Core bounded scheduler planning evidence as JSON",
    )


def core_bounded_scheduler_plan_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_bounded_scheduler_plan_json)


def run_core_bounded_scheduler_plan_cli(
    args: argparse.Namespace,
    repository: Any,
) -> None:
    if args.core_bounded_scheduler_plan_json:
        print_cli_json(
            build_core_bounded_scheduler_plan_report(repository),
            sort_keys=True,
        )


__all__ = [
    "add_core_bounded_scheduler_plan_args",
    "core_bounded_scheduler_plan_command_active",
    "run_core_bounded_scheduler_plan_cli",
]
