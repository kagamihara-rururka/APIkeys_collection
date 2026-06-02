from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.core_job_status_report import build_core_job_status_report


def add_core_job_status_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--core-job-status-report-json",
        action="store_true",
        help="emit RRKAL Core job-status evidence as JSON",
    )


def core_job_status_command_active(args: argparse.Namespace) -> bool:
    return bool(args.core_job_status_report_json)


def run_core_job_status_cli(args: argparse.Namespace, repository: Any) -> None:
    if args.core_job_status_report_json:
        print_cli_json(build_core_job_status_report(repository), sort_keys=True)


__all__ = [
    "add_core_job_status_args",
    "core_job_status_command_active",
    "run_core_job_status_cli",
]
