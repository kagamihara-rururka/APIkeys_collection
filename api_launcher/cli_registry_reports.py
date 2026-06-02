from __future__ import annotations

import argparse

from api_launcher.cli_json import print_cli_json
from api_launcher.content_registry import content_registry_report
from api_launcher.crawler_registry_report import crawler_registry_report
from api_launcher.dataset_adapters import dataset_adapter_report


def add_registry_report_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--crawler-registry-report-json",
        action="store_true",
        help="emit crawler registry matrix/capability report as JSON",
    )
    parser.add_argument(
        "--content-registry-report-json",
        action="store_true",
        help="emit content parser/import registry report as JSON",
    )
    parser.add_argument(
        "--dataset-adapter-report-json",
        action="store_true",
        help="emit provider-specific dataset adapter registry report as JSON",
    )


def registry_report_command_active(args: argparse.Namespace) -> bool:
    return bool(
        args.crawler_registry_report_json
        or args.content_registry_report_json
        or args.dataset_adapter_report_json
    )


def run_registry_report_cli(args: argparse.Namespace) -> None:
    """Emit registry diagnostics while keeping core CLI orchestration thin."""

    if args.crawler_registry_report_json:
        print_cli_json(crawler_registry_report())
    if args.content_registry_report_json:
        print_cli_json(content_registry_report())
    if args.dataset_adapter_report_json:
        print_cli_json(dataset_adapter_report())
