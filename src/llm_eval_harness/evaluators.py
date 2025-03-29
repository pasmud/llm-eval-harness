"""Built-in evaluators for deterministic safety checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from .models import EvalOutcome, EvalVerdict, EvaluationError


class Evaluator:
    """Base evaluator interface."""

    name: str = "base"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        raise NotImplementedError


def _get_string(check: dict[str, Any], key: str, default: str | None = None) -> str:
    value = check.get(key, default)
    if value is None:
        raise EvaluationError(f"evaluator '{check.get('type', '?')}' requires '{key}'")
    if not isinstance(value, str):
        raise EvaluationError(
            f"evaluator '{check.get('type', '?')}' field '{key}' must be a string"
        )
    return value


def _get_string_list(
    check: dict[str, Any], key: str, required: bool = True
) -> list[str]:
    value = check.get(key)
    if value is None:
        if required:
            raise EvaluationError(
                f"evaluator '{check.get('type', '?')}' requires '{key}'"
            )
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise EvaluationError(
            f"evaluator '{check.get('type', '?')}' field '{key}' must be a list of strings"
        )
    return list(value)


def _get_bool(check: dict[str, Any], key: str, default: bool) -> bool:
    value = check.get(key, default)
    if not isinstance(value, bool):
        raise EvaluationError(
            f"evaluator '{check.get('type', '?')}' field '{key}' must be a boolean"
        )
    return value


def _get_int(
    check: dict[str, Any], key: str, default: int | None = None, minimum: int | None = None
) -> int:
    value = check.get(key, default)
    if value is None:
        raise EvaluationError(f"evaluator '{check.get('type', '?')}' requires '{key}'")
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvaluationError(
            f"evaluator '{check.get('type', '?')}' field '{key}' must be an integer"
        )
    if minimum is not None and value < minimum:
        raise EvaluationError(
            f"evaluator '{check.get('type', '?')}' field '{key}' must be >= {minimum}"
        )
    return value


class ContainsEvaluator(Evaluator):
    name = "contains"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        value = _get_string(check, "value")
        case_sensitive = _get_bool(check, "case_sensitive", False)
        haystack = response if case_sensitive else response.lower()
        needle = value if case_sensitive else value.lower()
        passed = needle in haystack
        return EvalOutcome(
            evaluator=self.name,
            verdict=EvalVerdict.PASS if passed else EvalVerdict.FAIL,
            message=(
                f"response contains expected substring {value!r}"
                if passed
                else f"response missing expected substring {value!r}"
            ),
            details={"value": value, "case_sensitive": case_sensitive},
        )
