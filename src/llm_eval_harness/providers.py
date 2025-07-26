"""Response providers for deterministic evaluation runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from .models import EvaluationError, TestCase


class ResponseProvider(Protocol):
    """Provides a response for a test case."""

    def get_response(self, case: TestCase) -> str:
        """Return the model response for the given case."""


class StaticResponseProvider:
    """Deterministic response provider backed by an in-memory mapping."""

    def __init__(
        self,
        responses: dict[str, str],
        default_response: str | None = None,
    ) -> None:
        if not isinstance(responses, dict):
            raise EvaluationError("responses must be an object mapping case ids to strings")
        normalized: dict[str, str] = {}
        for key, value in responses.items():
            if not isinstance(key, str) or not key.strip():
                raise EvaluationError("response keys must be non-empty strings")
            if not isinstance(value, str):
                raise EvaluationError(
                    f"response for case '{key}' must be a string, got {type(value).__name__}"
                )
            normalized[key] = value
        if default_response is not None and not isinstance(default_response, str):
            raise EvaluationError("default_response must be a string when provided")
        self.responses = normalized
        self.default_response = default_response

    def get_response(self, case: TestCase) -> str:
        if case.id in self.responses:
            return self.responses[case.id]
        if self.default_response is not None:
            return self.default_response
        raise EvaluationError(
            f"no response provided for case '{case.id}' and no default_response configured"
        )


def _extract_response_value(value: Any, case_id: str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("response", "output", "text", "answer", "content"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
        raise EvaluationError(
            f"response entry for case '{case_id}' must be a string or an object with a string "
            "'response'/'output'/'text' field"
        )
    raise EvaluationError(
        f"response entry for case '{case_id}' must be a string, got {type(value).__name__}"
    )
