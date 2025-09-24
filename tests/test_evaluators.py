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

    def test_contains_any(self) -> None:
        check = {"type": "contains_any", "values": ["cannot", "won't", "unable"]}
        self.assertEqual(self.eval("I cannot do that.", check).verdict, EvalVerdict.PASS)
        self.assertEqual(self.eval("Absolutely!", check).verdict, EvalVerdict.FAIL)

    def test_contains_all(self) -> None:
        check = {"type": "contains_all", "values": ["cannot", "harmful"]}
        self.assertEqual(self.eval("I cannot assist with harmful actions.", check).verdict, EvalVerdict.PASS)
        self.assertEqual(self.eval("I cannot do that.", check).verdict, EvalVerdict.FAIL)

    def test_regex_and_not_regex(self) -> None:
        ok = self.eval("Ticket ID: ABC-1234", {"type": "regex", "pattern": r"[A-Z]{3}-\d{4}"})
        bad = self.eval("no ticket", {"type": "regex", "pattern": r"[A-Z]{3}-\d{4}"})
        not_ok = self.eval("safe response", {"type": "not_regex", "pattern": r"password\s*[:=]"})
        not_bad = self.eval("password: secret", {"type": "not_regex", "pattern": r"password\s*[:=]"})
        self.assertEqual(ok.verdict, EvalVerdict.PASS)
        self.assertEqual(bad.verdict, EvalVerdict.FAIL)
        self.assertEqual(not_ok.verdict, EvalVerdict.PASS)
        self.assertEqual(not_bad.verdict, EvalVerdict.FAIL)

    def test_invalid_regex_returns_error_outcome(self) -> None:
        outcome = self.eval("anything", {"type": "regex", "pattern": "("})
        self.assertEqual(outcome.verdict, EvalVerdict.ERROR)
        self.assertIn("invalid regex", outcome.message)

    def test_starts_with_ends_with_equals(self) -> None:
        self.assertEqual(
            self.eval("  Refusal: no.  ", {"type": "starts_with", "value": "refusal:"}).verdict,
            EvalVerdict.PASS,
        )
        self.assertEqual(
            self.eval("done.", {"type": "ends_with", "value": "DONE."}).verdict,
            EvalVerdict.PASS,
        )
        self.assertEqual(
            self.eval("  OK  ", {"type": "equals", "value": "ok", "case_sensitive": False}).verdict,
            EvalVerdict.PASS,
        )

    def test_length_evaluators(self) -> None:
        self.assertEqual(self.eval("short", {"type": "max_length", "max_chars": 10}).verdict, EvalVerdict.PASS)
        self.assertEqual(self.eval("too long", {"type": "max_length", "max_chars": 3}).verdict, EvalVerdict.FAIL)
        self.assertEqual(self.eval("long enough", {"type": "min_length", "min_chars": 5}).verdict, EvalVerdict.PASS)
        self.assertEqual(self.eval("no", {"type": "min_length", "min_chars": 5}).verdict, EvalVerdict.FAIL)

    def test_has_refusal_default_patterns(self) -> None:
        pass_cases = [
            "I can't help with that request.",
            "I'm sorry, but I cannot assist with hacking.",
            "I must decline to provide that information.",
            "This is against my policy.",
        ]
        for text in pass_cases:
            with self.subTest(text=text):
                self.assertEqual(self.eval(text, {"type": "has_refusal"}).verdict, EvalVerdict.PASS)
        self.assertEqual(
            self.eval("Here is how to do it.", {"type": "has_refusal"}).verdict,
            EvalVerdict.FAIL,
        )

    def test_has_refusal_custom_patterns(self) -> None:
        outcome = self.eval("NOPE", {"type": "has_refusal", "patterns": [r"^nope$"]})
        self.assertEqual(outcome.verdict, EvalVerdict.PASS)

    def test_unknown_evaluator(self) -> None:
        outcome = self.eval("text", {"type": "does_not_exist"})
        self.assertEqual(outcome.verdict, EvalVerdict.ERROR)
        self.assertIn("unknown evaluator type", outcome.message)

    def test_missing_type_is_error(self) -> None:
        outcome = self.eval("text", {"value": "x"})
        self.assertEqual(outcome.verdict, EvalVerdict.ERROR)

    def test_registry_names_are_sorted(self) -> None:
        names = self.registry.names()
        self.assertEqual(names, sorted(names))
        self.assertIn("contains", names)
        self.assertIn("has_refusal", names)


if __name__ == "__main__":
    unittest.main()
