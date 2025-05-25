"""Core evaluation harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evaluators import EvaluatorRegistry, builtin_registry
from .models import (
    CaseResult,
    EvalOutcome,
    EvalVerdict,
    EvaluationError,
    Suite,
    SuiteResult,
    TestCase,
    utc_now_iso,
)
from .providers import ResponseProvider, StaticResponseProvider


def _load_json_file(path: str | Path, label: str) -> Any:
    file_path = Path(path)
    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvaluationError(f"unable to read {label} '{file_path}': {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"invalid JSON in {label} '{file_path}': {exc}") from exc


class EvaluationHarness:
    """Runs deterministic evaluation suites against a response provider."""

    def __init__(
        self,
        registry: EvaluatorRegistry | None = None,
        fail_fast: bool = False,
    ) -> None:
        self.registry = registry or builtin_registry()
        self.fail_fast = fail_fast

    @staticmethod
    def load_suite(path: str | Path) -> Suite:
        data = _load_json_file(path, "suite file")
        return Suite.from_dict(data)

    def evaluate_case(self, case: TestCase, response: str) -> CaseResult:
        outcomes: list[EvalOutcome] = []
        for check in case.checks:
            outcome = self.registry.evaluate(response, check)
            outcomes.append(outcome)
            if self.fail_fast and not outcome.passed:
                break
        return CaseResult(
            case_id=case.id,
            prompt=case.prompt,
            response=response,
            outcomes=outcomes,
            description=case.description,
            tags=list(case.tags),
        )

    def run_suite(
        self,
        suite: Suite,
        provider: ResponseProvider,
        metadata: dict[str, Any] | None = None,
    ) -> SuiteResult:
        started_at = utc_now_iso()
        case_results: list[CaseResult] = []
        for case in suite.cases:
            try:
                response = provider.get_response(case)
            except EvaluationError as exc:
                outcomes = [
                    EvalOutcome(
                        evaluator="provider",
                        verdict=EvalVerdict.ERROR,
                        message=str(exc),
                    )
                ]
                case_results.append(
                    CaseResult(
                        case_id=case.id,
                        prompt=case.prompt,
                        response="",
                        outcomes=outcomes,
                        description=case.description,
                        tags=list(case.tags),
                    )
                )
                continue
            except Exception as exc:  # defensive provider boundary
                outcomes = [
                    EvalOutcome(
                        evaluator="provider",
                        verdict=EvalVerdict.ERROR,
                        message=f"unexpected provider error: {exc}",
                    )
                ]
                case_results.append(
                    CaseResult(
                        case_id=case.id,
                        prompt=case.prompt,
                        response="",
                        outcomes=outcomes,
                        description=case.description,
                        tags=list(case.tags),
                    )
                )
                continue

            if not isinstance(response, str):
                outcomes = [
                    EvalOutcome(
                        evaluator="provider",
                        verdict=EvalVerdict.ERROR,
                        message=(
                            f"provider returned non-string response of type "
                            f"{type(response).__name__}"
                        ),
                    )
                ]
                case_results.append(
                    CaseResult(
                        case_id=case.id,
                        prompt=case.prompt,
                        response="",
                        outcomes=outcomes,
                        description=case.description,
                        tags=list(case.tags),
                    )
                )
                continue

            case_results.append(self.evaluate_case(case, response))

        finished_at = utc_now_iso()
        return SuiteResult(
            suite_name=suite.name,
            suite_version=suite.version,
            case_results=case_results,
            started_at=started_at,
            finished_at=finished_at,
            metadata=dict(metadata or {}),
        )
