"""Built-in evaluators for deterministic safety checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from .models import EvalOutcome, EvalVerdict, EvaluationError


class Evaluator:
    """Base evaluator interface."""

    name: str = "base"
