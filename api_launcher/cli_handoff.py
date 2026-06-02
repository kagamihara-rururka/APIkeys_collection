from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.db import resolve_project_path
from api_launcher.handoff import build_handoff_snapshot, handoff_snapshot_to_dict, render_handoff_markdown


def add_handoff_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--handoff-report", help="write a Markdown handoff report for humans and agents")
    parser.add_argument("--handoff-report-json", action="store_true", help="emit handoff snapshot as agent-readable JSON")


def handoff_command_active(args: argparse.Namespace) -> bool:
    return bool(args.handoff_report or args.handoff_report_json)


def handoff_json_stdout_active(args: argparse.Namespace) -> bool:
    return bool(args.handoff_report_json)


def run_handoff_cli(args: argparse.Namespace, repository: Any) -> None:
    if not handoff_command_active(args):
        return

    snapshot = build_handoff_snapshot(repository)
    if args.handoff_report:
        output_path = resolve_project_path(args.handoff_report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_handoff_markdown(snapshot), encoding="utf-8")
        if not args.handoff_report_json:
            print(f"[handoff] wrote {output_path}")
    if args.handoff_report_json:
        # JSON stdout must stay clean for agents and automation.
        print_cli_json(handoff_snapshot_to_dict(snapshot))
