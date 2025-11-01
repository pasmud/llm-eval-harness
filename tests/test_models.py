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

    def test_test_case_requires_checks(self) -> None:
        with self.assertRaises(EvaluationError):
            TestCase.from_dict({"id": "c1", "prompt": "hello", "checks": []})

    def test_test_case_rejects_bad_check(self) -> None:
        with self.assertRaises(EvaluationError):
            TestCase.from_dict({"id": "c1", "prompt": "hello", "checks": [{"value": "x"}]})

    def test_suite_from_dict_and_round_trip_shape(self) -> None:
        suite = Suite.from_dict(
            {
                "name": "demo",
                "version": 2,
                "description": "desc",
                "cases": [
                    {
                        "id": "a",
                        "prompt": "p",
                        "checks": [{"type": "contains", "value": "x"}],
                    }
                ],
            }
        )
        self.assertEqual(suite.version, "2")
        data = suite.to_dict()
        self.assertEqual(data["name"], "demo")
        self.assertEqual(data["cases"][0]["id"], "a")

    def test_suite_rejects_duplicate_case_ids(self) -> None:
        with self.assertRaises(EvaluationError):
            Suite.from_dict(
                {
                    "name": "dup",
                    "cases": [
                        {"id": "same", "prompt": "p1", "checks": [{"type": "contains", "value": "a"}]},
                        {"id": "same", "prompt": "p2", "checks": [{"type": "contains", "value": "b"}]},
                    ],
                }
            )

    def test_suite_rejects_empty_cases(self) -> None:
        with self.assertRaises(EvaluationError):
            Suite.from_dict({"name": "empty", "cases": []})

    def test_case_result_aggregation(self) -> None:
        result = CaseResult(
            case_id="c1",
            prompt="p",
            response="r",
            outcomes=[
                EvalOutcome("contains", EvalVerdict.PASS, "ok"),
                EvalOutcome("regex", EvalVerdict.FAIL, "bad"),
            ],
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.verdict, EvalVerdict.FAIL)
        self.assertEqual(result.checks_passed, 1)
        self.assertEqual(result.checks_total, 2)

    def test_case_result_error_verdict(self) -> None:
        result = CaseResult(
            case_id="c1",
            prompt="p",
            response="r",
            outcomes=[
                EvalOutcome("contains", EvalVerdict.PASS, "ok"),
                EvalOutcome("regex", EvalVerdict.ERROR, "broken"),
            ],
        )
        self.assertEqual(result.verdict, EvalVerdict.ERROR)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
