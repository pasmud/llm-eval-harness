"""Tests for the evaluation harness core."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import tests._paths  # noqa: F401

from llm_eval_harness.harness import EvaluationHarness
