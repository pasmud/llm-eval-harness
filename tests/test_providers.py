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
