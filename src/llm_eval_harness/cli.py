"""Command-line interface for llm-eval-harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .evaluators import builtin_registry
from .harness import EvaluationHarness
from .models import EvaluationError, Suite
from .providers import load_responses_file


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-eval-harness",
        description=(
            "Deterministic evaluation harness for LLM safety test cases. "
            "Run suites against static responses, validate inputs, and inspect case inventories."
        ),
    )
