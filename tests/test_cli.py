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

    def test_run_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            suite_path, responses_path = self.write_suite_and_responses(td)
            out_path = Path(td) / "report.json"
            proc = run_cli(
                "run",
                "--suite",
                str(suite_path),
                "--responses",
                str(responses_path),
                "--format",
                "json",
                "--output",
                str(out_path),
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            self.assertTrue(out_path.exists())
            payload = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["success"])

    def test_check_valid_and_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            suite_path, responses_path = self.write_suite_and_responses(td)
            ok = run_cli("check", "--suite", str(suite_path), "--responses", str(responses_path))
            self.assertEqual(ok.returncode, 0, msg=ok.stdout + ok.stderr)
            self.assertIn("Status: OK", ok.stdout)

            missing = Path(td) / "missing.json"
            missing.write_text(json.dumps({"c1": "only one"}), encoding="utf-8")
            bad = run_cli("check", "--suite", str(suite_path), "--responses", str(missing), "--format", "json")
            self.assertEqual(bad.returncode, 1, msg=bad.stdout + bad.stderr)
            payload = json.loads(bad.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["issues"][0]["type"], "missing_responses")

    def test_scan_and_list_evaluators(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            suite_path, _ = self.write_suite_and_responses(td)
            scan = run_cli("scan", "--suite", str(suite_path), "--format", "json")
            self.assertEqual(scan.returncode, 0, msg=scan.stderr)
            scan_payload = json.loads(scan.stdout)
            self.assertEqual(scan_payload["suite"]["case_count"], 2)

        listing = run_cli("list-evaluators", "--format", "json")
        self.assertEqual(listing.returncode, 0, msg=listing.stderr)
        payload = json.loads(listing.stdout)
        self.assertIn("has_refusal", payload["evaluators"])
