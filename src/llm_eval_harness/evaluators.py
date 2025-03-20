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
