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


class NotContainsEvaluator(Evaluator):
    name = "not_contains"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        value = _get_string(check, "value")
        case_sensitive = _get_bool(check, "case_sensitive", False)
        haystack = response if case_sensitive else response.lower()
        needle = value if case_sensitive else value.lower()
        found = needle in haystack
        return EvalOutcome(
            evaluator=self.name,
            verdict=EvalVerdict.FAIL if found else EvalVerdict.PASS,
            message=(
                f"response contains forbidden substring {value!r}"
                if found
                else f"response does not contain forbidden substring {value!r}"
            ),
            details={"value": value, "case_sensitive": case_sensitive},
        )


class ContainsAnyEvaluator(Evaluator):
    name = "contains_any"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        values = _get_string_list(check, "values")
        if not values:
            raise EvaluationError("evaluator 'contains_any' requires non-empty 'values'")
        case_sensitive = _get_bool(check, "case_sensitive", False)
        haystack = response if case_sensitive else response.lower()
        matched = [
            value
            for value in values
            if (value if case_sensitive else value.lower()) in haystack
        ]
        passed = bool(matched)
        return EvalOutcome(
            evaluator=self.name,
            verdict=EvalVerdict.PASS if passed else EvalVerdict.FAIL,
            message=(
                f"response contains at least one expected value: {matched!r}"
                if passed
                else f"response contains none of the expected values: {values!r}"
            ),
            details={
                "values": values,
                "matched": matched,
                "case_sensitive": case_sensitive,
            },
        )


class ContainsAllEvaluator(Evaluator):
    name = "contains_all"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        values = _get_string_list(check, "values")
        if not values:
            raise EvaluationError("evaluator 'contains_all' requires non-empty 'values'")
        case_sensitive = _get_bool(check, "case_sensitive", False)
        haystack = response if case_sensitive else response.lower()
        missing = [
            value
            for value in values
            if (value if case_sensitive else value.lower()) not in haystack
        ]
        passed = not missing
        return EvalOutcome(
            evaluator=self.name,
            verdict=EvalVerdict.PASS if passed else EvalVerdict.FAIL,
            message=(
                "response contains all expected values"
                if passed
                else f"response missing expected values: {missing!r}"
            ),
            details={
                "values": values,
                "missing": missing,
                "case_sensitive": case_sensitive,
            },
        )


class RegexEvaluator(Evaluator):
    name = "regex"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        pattern = _get_string(check, "pattern")
        case_sensitive = _get_bool(check, "case_sensitive", True)
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
        except re.error as exc:
            raise EvaluationError(f"invalid regex pattern {pattern!r}: {exc}") from exc
        match = compiled.search(response)
        passed = match is not None
        return EvalOutcome(
            evaluator=self.name,
            verdict=EvalVerdict.PASS if passed else EvalVerdict.FAIL,
            message=(
                f"response matches regex {pattern!r}"
                if passed
                else f"response does not match regex {pattern!r}"
            ),
            details={
                "pattern": pattern,
                "case_sensitive": case_sensitive,
                "match": match.group(0) if match else None,
            },
        )


class NotRegexEvaluator(Evaluator):
    name = "not_regex"

    def evaluate(self, response: str, check: dict[str, Any]) -> EvalOutcome:
        pattern = _get_string(check, "pattern")
        case_sensitive = _get_bool(check, "case_sensitive", True)
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
        except re.error as exc:
            raise EvaluationError(f"invalid regex pattern {pattern!r}: {exc}") from exc
        match = compiled.search(response)
        passed = match is None
        return EvalOutcome(
            evaluator=self.name,
            verdict=EvalVerdict.PASS if passed else EvalVerdict.FAIL,
            message=(
                f"response does not match forbidden regex {pattern!r}"
                if passed
                else f"response matches forbidden regex {pattern!r}"
            ),
            details={
                "pattern": pattern,
                "case_sensitive": case_sensitive,
                "match": match.group(0) if match else None,
            },
        )


class StartsWithEvaluator(Evaluator):
    name = "starts_with"
