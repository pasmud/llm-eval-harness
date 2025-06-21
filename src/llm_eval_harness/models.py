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

    id: str
    prompt: str
    checks: list[dict[str, Any]]
    description: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int = 0) -> "TestCase":
        if not isinstance(data, dict):
            raise EvaluationError(f"case at index {index} must be an object")
        raw_id = data.get("id")
        case_id = str(raw_id).strip() if raw_id is not None else f"case-{index + 1}"
        if not case_id:
            raise EvaluationError(f"case at index {index} has an empty id")

        prompt = data.get("prompt")
        if prompt is not None and not isinstance(prompt, str):
            raise EvaluationError(f"case '{case_id}' prompt must be a string")
        prompt_text = prompt or ""

        raw_checks = data.get("checks")
        if not isinstance(raw_checks, list) or not raw_checks:
            raise EvaluationError(
                f"case '{case_id}' must define a non-empty 'checks' list"
            )
        checks: list[dict[str, Any]] = []
        for check_index, check in enumerate(raw_checks):
            if not isinstance(check, dict):
                raise EvaluationError(
                    f"case '{case_id}' check {check_index} must be an object"
                )
            check_type = check.get("type")
            if not isinstance(check_type, str) or not check_type.strip():
                raise EvaluationError(
                    f"case '{case_id}' check {check_index} must have a non-empty 'type'"
                )
            checks.append(dict(check))

        description = data.get("description", "")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise EvaluationError(f"case '{case_id}' description must be a string")

        tags_raw = data.get("tags", [])
        if tags_raw is None:
            tags_raw = []
        if not isinstance(tags_raw, list) or not all(
            isinstance(tag, str) for tag in tags_raw
        ):
            raise EvaluationError(f"case '{case_id}' tags must be a list of strings")

        metadata = data.get("metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise EvaluationError(f"case '{case_id}' metadata must be an object")

        return cls(
            id=case_id,
            prompt=prompt_text,
            checks=checks,
            description=description,
            tags=list(tags_raw),
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "prompt": self.prompt,
            "checks": [dict(check) for check in self.checks],
        }
        if self.description:
            data["description"] = self.description
        if self.tags:
            data["tags"] = list(self.tags)
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass
class Suite:
    """A collection of evaluation cases."""

    name: str
    cases: list[TestCase]
    description: str = ""
    version: str = "1"
    metadata: dict[str, Any] = field(default_factory=dict)
