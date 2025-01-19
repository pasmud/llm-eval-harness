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
