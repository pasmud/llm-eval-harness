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

    def test_help(self) -> None:
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("llm-eval-harness", proc.stdout)
        self.assertIn("run", proc.stdout)

    def test_run_text_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            suite_path, responses_path = self.write_suite_and_responses(td)
            proc = run_cli(
                "run",
                "--suite",
                str(suite_path),
                "--responses",
                str(responses_path),
                "--format",
                "text",
            )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("PASS", proc.stdout)
        self.assertIn("2/2 passed", proc.stdout)

    def test_run_json_failure_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            suite_path, responses_path = self.write_suite_and_responses(td)
            bad_responses = Path(td) / "bad.json"
            bad_responses.write_text(json.dumps({"c1": "sure", "c2": "nope"}), encoding="utf-8")
            proc = run_cli(
                "run",
                "--suite",
                str(suite_path),
                "--responses",
                str(bad_responses),
                "--format",
                "json",
            )
        self.assertEqual(proc.returncode, 1, msg=proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["success"])
        self.assertEqual(payload["failed"], 2)
