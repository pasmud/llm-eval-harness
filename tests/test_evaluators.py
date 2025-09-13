"""Unit tests for built-in evaluators."""

from __future__ import annotations

import unittest

import tests._paths  # noqa: F401

from llm_eval_harness.evaluators import builtin_registry
from llm_eval_harness.models import EvalVerdict, EvaluationError


class EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = builtin_registry()

    def eval(self, response: str, check: dict):  # type: ignore[no-untyped-def]
        return self.registry.evaluate(response, check)
