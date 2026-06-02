from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from api_launcher.cli_json import print_cli_json
from api_launcher.db import resolve_project_path
from api_launcher.mvp_demo import (
    run_mvp_demo_offline_smoke,
    write_mvp_demo_flow as write_mvp_demo_flow_files,
)
from api_launcher.mvp_readiness import build_mvp_readiness_payload


def add_mvp_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--write-mvp-demo-flow", help="write the canonical MVP demo flow JSON plus its adapter-review plan")
    parser.add_argument("--run-mvp-demo-smoke-json", help="write the canonical MVP demo flow and run its offline download/import smoke as JSON")
    parser.add_argument("--mvp-readiness-json", action="store_true", help="emit canonical MVP closure readiness as JSON")
    parser.add_argument("--write-mvp-readiness-json", default="", help="write canonical MVP closure readiness JSON")


def mvp_command_active(args: argparse.Namespace) -> bool:
    return bool(
        args.write_mvp_demo_flow
        or args.run_mvp_demo_smoke_json
        or args.mvp_readiness_json
        or args.write_mvp_readiness_json
    )


def mvp_json_stdout_active(args: argparse.Namespace) -> bool:
    return bool(args.run_mvp_demo_smoke_json or args.mvp_readiness_json)


def run_mvp_cli(args: argparse.Namespace, repository: Any, log_event: Callable[..., object]) -> None:
    write_mvp_demo_flow_cli(args)
    run_mvp_demo_smoke_cli(args, repository, log_event)
    run_mvp_readiness_cli(args, repository)


def write_mvp_demo_flow_cli(args: argparse.Namespace) -> None:
    if not args.write_mvp_demo_flow:
        return

    result = write_mvp_demo_flow_files(resolve_project_path(args.write_mvp_demo_flow))
    print(
        "[mvp-demo] "
        f"wrote {result.flow_path} review_plan={result.review_plan_path} "
        f"offline_plan={result.offline_plan_path} resolved_plan={result.resolved_plan_path}"
    )
    for command in result.flow_payload.get("commands", []):
        if not isinstance(command, dict) or command.get("step") in {1, "1"}:
            continue
        print(f"[mvp-demo] step{command.get('step')} {command.get('command')}")


def run_mvp_demo_smoke_cli(args: argparse.Namespace, repository: Any, log_event: Callable[..., object]) -> None:
    if not args.run_mvp_demo_smoke_json:
        return

    result = run_mvp_demo_offline_smoke(
        resolve_project_path(args.run_mvp_demo_smoke_json),
        repository,
    )
    log_event(
        "mvp_demo_smoke_completed",
        "Ran canonical offline MVP demo smoke.",
        component="mvp_demo",
        context={
            "flow_path": str(result.flow.flow_path),
            "stage": result.run.stage,
            "succeeded": result.succeeded,
            "table_name": result.table_name,
            "row_count": result.row_count,
            "download_import": result.run.to_dict(),
        },
    )
    print_cli_json(result.to_dict())
    if not result.succeeded:
        raise RuntimeError("MVP demo offline smoke did not complete successfully.")


def run_mvp_readiness_cli(args: argparse.Namespace, repository: Any) -> None:
    if not (args.mvp_readiness_json or args.write_mvp_readiness_json):
        return

    payload = build_mvp_readiness_payload(repository, db_path=args.db)
    if args.write_mvp_readiness_json:
        output_path = resolve_project_path(args.write_mvp_readiness_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.mvp_readiness_json:
            print(f"[mvp-readiness] wrote {output_path}")
    if args.mvp_readiness_json:
        print_cli_json(payload)
