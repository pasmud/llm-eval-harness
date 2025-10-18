"""Unit tests for data model validation and serialization."""

from __future__ import annotations

import unittest

import tests._paths  # noqa: F401

from llm_eval_harness.models import (
    CaseResult,
    EvalOutcome,
    EvalVerdict,
    EvaluationError,
    Suite,
    TestCase,
)


class ModelTests(unittest.TestCase):
    def test_test_case_from_dict_defaults(self) -> None:
        case = TestCase.from_dict(
            {"id": "c1", "prompt": "hello", "checks": [{"type": "contains", "value": "hi"}]}
        )
        self.assertEqual(case.id, "c1")
        self.assertEqual(case.description, "")
        self.assertEqual(case.tags, [])
