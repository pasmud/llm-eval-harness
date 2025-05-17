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
