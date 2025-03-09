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
