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
    lines.append(
        f"Result: {'PASS' if result['success'] else 'FAIL'} "
        f"({result['passed']}/{result['total']} passed, "
        f"{result['failed']} failed, {result['errors']} errors)"
    )
    lines.append(f"Pass rate: {result['pass_rate']:.2%}")
    lines.append("")
    for case in result["case_results"]:
        verdict = case["verdict"].upper()
        lines.append(f"[{verdict}] {case['case_id']} - {case['checks_passed']}/{case['checks_total']} checks")
        for outcome in case["outcomes"]:
            marker = "ok" if outcome["passed"] else outcome["verdict"].upper()
            lines.append(f"  - ({marker}) {outcome['evaluator']}: {outcome['message']}")
    return "\n".join(lines) + "\n"


def _cmd_run(args: argparse.Namespace) -> int:
    harness = EvaluationHarness(fail_fast=args.fail_fast)
    result = harness.run_suite_from_files(
        suite_path=args.suite,
        responses_path=args.responses,
        default_response=args.default_response,
    )
    payload = result.to_dict()
    if args.format == "json":
        text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    else:
        text = _format_text_report(payload)
    _emit(text, args.output)
    return EXIT_SUCCESS if result.success else EXIT_FAILURE


def _cmd_check(args: argparse.Namespace) -> int:
    suite_path = Path(args.suite)
    try:
        data = json.loads(suite_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EvaluationError(f"unable to read suite file '{suite_path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"invalid JSON in suite file '{suite_path}': {exc}") from exc

    suite = Suite.from_dict(data)
    report: dict[str, Any] = {
        "ok": True,
        "suite": {
            "path": str(suite_path),
            "name": suite.name,
            "version": suite.version,
            "cases": len(suite.cases),
            "checks": sum(len(case.checks) for case in suite.cases),
        },
        "issues": [],
    }

    if args.responses:
        responses = load_responses_file(args.responses)
        report["responses"] = {
            "path": str(Path(args.responses)),
            "count": len(responses),
        }
        missing = [case.id for case in suite.cases if case.id not in responses]
        extra = sorted(set(responses) - {case.id for case in suite.cases})
        if missing:
            report["ok"] = False
            report["issues"].append(
                {"type": "missing_responses", "case_ids": missing}
            )
        if extra:
            report["issues"].append({"type": "extra_responses", "case_ids": extra})

    if args.format == "json":
        _emit(json.dumps(report, indent=2) + "\n", None)
    else:
        lines = [
            f"Suite: {report['suite']['name']} (v{report['suite']['version']})",
            f"Cases: {report['suite']['cases']}, Checks: {report['suite']['checks']}",
        ]
        if "responses" in report:
            lines.append(f"Responses: {report['responses']['count']}")
        if report["issues"]:
            for issue in report["issues"]:
                lines.append(f"Issue: {issue['type']} - {', '.join(issue['case_ids'])}")
        lines.append(f"Status: {'OK' if report['ok'] else 'INVALID'}")
        _emit("\n".join(lines) + "\n", None)
    return EXIT_SUCCESS if report["ok"] else EXIT_FAILURE


def _cmd_scan(args: argparse.Namespace) -> int:
    harness = EvaluationHarness()
    suite = harness.load_suite(args.suite)
    cases_payload = []
    for case in suite.cases:
        item: dict[str, Any] = {
            "id": case.id,
            "description": case.description,
            "tags": list(case.tags),
            "checks": [dict(check) for check in case.checks],
            "check_count": len(case.checks),
        }
        cases_payload.append(item)

    payload = {
        "suite": {
            "path": str(Path(args.suite)),
            "name": suite.name,
            "version": suite.version,
            "description": suite.description,
            "case_count": len(suite.cases),
            "check_count": sum(len(case.checks) for case in suite.cases),
        },
        "cases": cases_payload,
    }

    if args.format == "json":
        _emit(json.dumps(payload, indent=2) + "\n", None)
    else:
        lines = [
            f"Suite: {suite.name} (v{suite.version})",
            f"Cases: {len(suite.cases)}, Checks: {payload['suite']['check_count']}",
        ]
        if suite.description:
            lines.append(f"Description: {suite.description}")
        lines.append("")
        for case in suite.cases:
            tags = f" tags={','.join(case.tags)}" if case.tags else ""
            lines.append(f"- {case.id}{tags} ({len(case.checks)} checks)")
            if case.description:
                lines.append(f"  description: {case.description}")
            if args.verbose:
                for check in case.checks:
                    lines.append(f"  check: {json.dumps(check, sort_keys=True)}")
        _emit("\n".join(lines) + "\n", None)
    return EXIT_SUCCESS


def _cmd_list_evaluators(args: argparse.Namespace) -> int:
    registry = builtin_registry()
    names = registry.names()
    if args.format == "json":
        _emit(json.dumps({"evaluators": names}, indent=2) + "\n", None)
    else:
        lines = ["Built-in evaluators:"]
        for name in names:
            lines.append(f"- {name}")
        _emit("\n".join(lines) + "\n", None)
    return EXIT_SUCCESS


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else EXIT_USAGE
        return code

    try:
        return int(args.func(args))
    except EvaluationError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return EXIT_FAILURE
    except KeyboardInterrupt:
        sys.stderr.write("error: interrupted\n")
        return EXIT_FAILURE
