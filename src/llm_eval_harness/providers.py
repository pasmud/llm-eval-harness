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


def load_responses_data(data: Any) -> dict[str, str]:
    """Normalize supported response file formats into a case-id mapping."""
    if isinstance(data, dict):
        # Format 1: {"responses": {"id": "..."}} or {"responses": [{"id":..., "response":...}]}
        if "responses" in data:
            payload = data["responses"]
            if isinstance(payload, list):
                responses: dict[str, str] = {}
                for index, item in enumerate(payload):
                    if not isinstance(item, dict):
                        raise EvaluationError(
                            f"responses[{index}] must be an object with 'id' and response text"
                        )
                    case_id = item.get("id") or item.get("case_id")
                    if not isinstance(case_id, str) or not case_id.strip():
                        raise EvaluationError(
                            f"responses[{index}] must include a non-empty 'id'"
                        )
                    if "response" in item:
                        responses[case_id] = _extract_response_value(item["response"], case_id)
                    elif "output" in item:
                        responses[case_id] = _extract_response_value(item["output"], case_id)
                    elif "text" in item:
                        responses[case_id] = _extract_response_value(item["text"], case_id)
                    else:
                        raise EvaluationError(
                            f"responses[{index}] for case '{case_id}' must include 'response'"
                        )
                return responses
            if isinstance(payload, dict):
                return {
                    str(key): _extract_response_value(value, str(key))
                    for key, value in payload.items()
                }
            raise EvaluationError("'responses' must be an object or a list")

        # Format 2: plain mapping {"case-id": "response"}
        if data and all(isinstance(v, (str, dict)) for v in data.values()):
            # Heuristic: treat as mapping unless it looks like a single response object.
            reserved = {"name", "version", "cases", "description", "metadata"}
            if not reserved.intersection(data.keys()):
                return {
                    str(key): _extract_response_value(value, str(key))
                    for key, value in data.items()
                }

        raise EvaluationError(
            "unsupported responses object format; expected {'responses': ...} or a case-id mapping"
        )

    if isinstance(data, list):
        # Format 3: [{"id": "case-1", "response": "..."}]
        responses = {}
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise EvaluationError(
                    f"responses[{index}] must be an object with 'id' and response text"
                )
            case_id = item.get("id") or item.get("case_id")
            if not isinstance(case_id, str) or not case_id.strip():
                raise EvaluationError(f"responses[{index}] must include a non-empty 'id'")
            if "response" in item:
                responses[case_id] = _extract_response_value(item["response"], case_id)
            elif "output" in item:
                responses[case_id] = _extract_response_value(item["output"], case_id)
            elif "text" in item:
                responses[case_id] = _extract_response_value(item["text"], case_id)
            else:
                raise EvaluationError(
                    f"responses[{index}] for case '{case_id}' must include 'response'"
                )
        return responses

    raise EvaluationError("responses data must be an object or a list")


def load_responses_file(path: str | Path) -> dict[str, str]:
    """Load response mappings from a JSON file."""
