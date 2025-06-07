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
