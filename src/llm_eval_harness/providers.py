"""Response providers for deterministic evaluation runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from .models import EvaluationError, TestCase
