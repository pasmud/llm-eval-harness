"""Command-line interface for llm-eval-harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .evaluators import builtin_registry
from .harness import EvaluationHarness
from .models import EvaluationError, Suite
from .providers import load_responses_file


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-eval-harness",
        description=(
            "Deterministic evaluation harness for LLM safety test cases. "
            "Run suites against static responses, validate inputs, and inspect case inventories."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run an evaluation suite against a responses file.",
        description="Execute all cases in a suite using deterministic static responses.",
    )
    run_parser.add_argument("--suite", required=True, help="Path to suite JSON file.")
    run_parser.add_argument(
        "--responses",
        required=True,
        help="Path to responses JSON file mapping case ids to response strings.",
    )
    run_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    run_parser.add_argument(
        "--output",
        help="Write report to a file instead of stdout.",
    )
    run_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop evaluating checks for a case after the first failure.",
    )
    run_parser.add_argument(
        "--default-response",
        help="Fallback response used when a case id is missing from the responses file.",
    )
    run_parser.set_defaults(func=_cmd_run)

    check_parser = subparsers.add_parser(
        "check",
        help="Validate suite and optional responses files.",
        description="Validate schema/structure of suite and response inputs without running evaluations.",
    )
    check_parser.add_argument("--suite", required=True, help="Path to suite JSON file.")
    check_parser.add_argument(
        "--responses",
        help="Optional responses JSON file to validate against the suite.",
    )
    check_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    check_parser.set_defaults(func=_cmd_check)

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a suite and list its cases and checks.",
        description="Inspect a suite definition and report case inventory.",
    )
    scan_parser.add_argument("--suite", required=True, help="Path to suite JSON file.")
    scan_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    scan_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include check details for each case in text output.",
    )
    scan_parser.set_defaults(func=_cmd_scan)

    list_parser = subparsers.add_parser(
        "list-evaluators",
        help="List built-in evaluator types.",
        description="Show the evaluator types available in the built-in registry.",
    )
    list_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    list_parser.set_defaults(func=_cmd_list_evaluators)

    return parser


def _emit(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def _format_text_report(result: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"Suite: {result['suite_name']} (v{result['suite_version']})")
