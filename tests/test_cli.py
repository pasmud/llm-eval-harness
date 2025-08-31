"""CLI smoke and behavior tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tests._paths  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "llm_eval_harness", *args],
        cwd=str(cwd or ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def write_suite_and_responses(self, td: str) -> tuple[Path, Path]:
        root = Path(td)
        suite = {
            "name": "cli-suite",
            "version": "1",
            "cases": [
                {
                    "id": "c1",
                    "prompt": "p1",
                    "checks": [{"type": "contains", "value": "cannot"}],
                },
                {
                    "id": "c2",
                    "prompt": "p2",
                    "checks": [{"type": "regex", "pattern": "^ok"}],
                },
            ],
        }
        responses = {"c1": "I cannot do that.", "c2": "ok done"}
        suite_path = root / "suite.json"
        responses_path = root / "responses.json"
        suite_path.write_text(json.dumps(suite), encoding="utf-8")
        responses_path.write_text(json.dumps(responses), encoding="utf-8")
        return suite_path, responses_path
