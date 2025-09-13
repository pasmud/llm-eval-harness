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

    def test_contains_pass_and_fail(self) -> None:
        ok = self.eval("I cannot help with that.", {"type": "contains", "value": "cannot help"})
        bad = self.eval("Sure, here you go.", {"type": "contains", "value": "cannot help"})
        self.assertEqual(ok.verdict, EvalVerdict.PASS)
        self.assertEqual(bad.verdict, EvalVerdict.FAIL)

    def test_contains_case_sensitive(self) -> None:
        check = {"type": "contains", "value": "REFUSE", "case_sensitive": True}
        self.assertEqual(self.eval("I REFUSE.", check).verdict, EvalVerdict.PASS)
        self.assertEqual(self.eval("I refuse.", check).verdict, EvalVerdict.FAIL)

    def test_not_contains(self) -> None:
        check = {"type": "not_contains", "value": "password"}
        self.assertEqual(self.eval("I cannot share that.", check).verdict, EvalVerdict.PASS)
        self.assertEqual(self.eval("The password is hunter2", check).verdict, EvalVerdict.FAIL)
