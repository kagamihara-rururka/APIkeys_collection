from __future__ import annotations

import argparse
from typing import Any

from api_launcher.cli_json import print_cli_json
from api_launcher.db import resolve_project_path
from api_launcher.project_maturity import (
    build_project_maturity_payload,
    render_project_maturity_markdown,
    write_project_maturity_payload,
)


def add_project_maturity_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-maturity-json", action="store_true", help="emit RRKAL project maturity matrix as JSON")
    parser.add_argument("--write-project-maturity-json", default="", help="write RRKAL project maturity matrix JSON")
    parser.add_argument("--project-maturity-markdown", default="", help="write RRKAL project maturity matrix Markdown")


def project_maturity_command_active(args: argparse.Namespace) -> bool:
    return bool(
        args.project_maturity_json
        or args.write_project_maturity_json
        or args.project_maturity_markdown
    )


def run_project_maturity_cli(args: argparse.Namespace, repository: Any) -> None:
    """Emit or write the project maturity matrix without expanding core CLI logic."""

    if not project_maturity_command_active(args):
        return

    payload = build_project_maturity_payload(repository, db_path=args.db)
    if args.write_project_maturity_json:
        output_path = resolve_project_path(args.write_project_maturity_json)
        write_project_maturity_payload(output_path, payload)
        if not args.project_maturity_json:
            print(f"[project-maturity] wrote {output_path}")
    if args.project_maturity_markdown:
        output_path = resolve_project_path(args.project_maturity_markdown)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_project_maturity_markdown(payload), encoding="utf-8")
        if not args.project_maturity_json:
            print(f"[project-maturity] wrote {output_path}")
    if args.project_maturity_json:
        print_cli_json(payload)
