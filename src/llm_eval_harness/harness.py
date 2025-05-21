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
