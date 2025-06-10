"""Data models for the evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class EvaluationError(ValueError):
    """Raised when suite or case definitions are invalid."""


@dataclass(frozen=True)
class EvalVerdict:
    """Verdict constants for an evaluation check."""

    PASS: str = "pass"
    FAIL: str = "fail"
    ERROR: str = "error"


@dataclass
class EvalOutcome:
    """Result of a single evaluator check."""

    evaluator: str
    verdict: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.verdict == EvalVerdict.PASS

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "evaluator": self.evaluator,
            "verdict": self.verdict,
            "passed": self.passed,
            "message": self.message,
        }
        if self.details:
            data["details"] = self.details
        return data


@dataclass
class TestCase:
    """A single evaluation case."""

    __test__ = False
