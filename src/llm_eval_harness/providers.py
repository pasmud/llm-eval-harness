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
