"""Tests for response loading and provider behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import tests._paths  # noqa: F401

from llm_eval_harness.models import EvaluationError, TestCase
from llm_eval_harness.providers import StaticResponseProvider, load_responses_file


class ProviderTests(unittest.TestCase):
    def make_case(self, case_id: str) -> TestCase:
        return TestCase.from_dict(
            {"id": case_id, "prompt": "p", "checks": [{"type": "contains", "value": "x"}]}
        )

    def test_static_provider_returns_response(self) -> None:
        provider = StaticResponseProvider({"a": "response-a"})
        self.assertEqual(provider.get_response(self.make_case("a")), "response-a")

    def test_static_provider_default_response(self) -> None:
        provider = StaticResponseProvider({}, default_response="fallback")
        self.assertEqual(provider.get_response(self.make_case("missing")), "fallback")

    def test_static_provider_missing_raises(self) -> None:
        provider = StaticResponseProvider({"a": "x"})
        with self.assertRaises(EvaluationError):
            provider.get_response(self.make_case("b"))

    def test_load_responses_file_mapping_format(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.json"
            path.write_text(json.dumps({"case-1": "r1", "case-2": "r2"}), encoding="utf-8")
            loaded = load_responses_file(path)
        self.assertEqual(loaded, {"case-1": "r1", "case-2": "r2"})

    def test_load_responses_file_wrapped_object_format(self) -> None:
        data = {"responses": {"case-1": "r1", "case-2": {"response": "r2"}}}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = load_responses_file(path)
        self.assertEqual(loaded, {"case-1": "r1", "case-2": "r2"})

    def test_load_responses_file_list_format(self) -> None:
        data = [
            {"id": "case-1", "response": "r1"},
            {"case_id": "case-2", "output": "r2"},
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = load_responses_file(path)
        self.assertEqual(loaded, {"case-1": "r1", "case-2": "r2"})

    def test_load_responses_file_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(EvaluationError):
                load_responses_file(path)

    def test_load_responses_file_rejects_non_string(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "responses.json"
            path.write_text(json.dumps({"case-1": 123}), encoding="utf-8")
            with self.assertRaises(EvaluationError):
                load_responses_file(path)


if __name__ == "__main__":
    unittest.main()
