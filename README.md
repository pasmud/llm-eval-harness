# llm-eval-harness

`llm-eval-harness` is a deterministic evaluation harness for LLM safety test cases. It runs structured JSON suites against pre-recorded model responses, applies built-in safety-oriented checks, and emits reproducible text or JSON reports.

The project is designed for offline, repeatable evaluation workflows: you define cases and checks once, capture or fixture model outputs, and gate changes on deterministic pass/fail results.

## Features

- **Deterministic execution**: no network calls, no model inference; evaluations run against static response fixtures.
- **Structured suite model**: JSON suites with named cases, prompts, tags, metadata, and typed checks.
- **Built-in evaluators** for common safety assertions:
  - `contains`, `not_contains`
  - `contains_any`, `contains_all`
  - `regex`, `not_regex`
  - `starts_with`, `ends_with`, `equals`
  - `max_length`, `min_length`
  - `has_refusal` (heuristic refusal-signal matcher with customizable patterns)
- **CLI workflows**: `run`, `check`, `scan`, and `list-evaluators`.
- **Machine-readable reports**: JSON output for CI or tooling integration, plus human-readable text summaries.
- **Validation**: schema/structure checks for suites and response files, with clear error reporting.

## Project layout

```text
.
├── .github/workflows/ci.yml
├── LICENSE
├── README.md
├── examples/
│   ├── failing_responses.json
│   ├── safety_suite.json
│   └── sample_responses.json
├── pyproject.toml
├── src/
│   └── llm_eval_harness/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── evaluators.py
│       ├── harness.py
│       ├── models.py
│       ├── providers.py
│       └── py.typed
└── tests/
    ├── test_cli.py
    ├── test_evaluators.py
    ├── test_harness.py
    ├── test_models.py
    └── test_providers.py
```

## Installation

Requires Python 3.10+.

### From source (editable)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

For development/test tooling:

```bash
python -m pip install -e ".[dev]"
```

The package has no runtime third-party dependencies; the optional `dev` extra installs `pytest`.

## Quick start

### 1) Inspect the example suite

```bash
python -m llm_eval_harness scan --suite examples/safety_suite.json
```

### 2) Run the suite against passing sample responses

```bash
python -m llm_eval_harness run \
  --suite examples/safety_suite.json \
  --responses examples/sample_responses.json \
  --format text
```

Expected behavior: the command prints a report with `PASS` and exits with code `0`.

### 3) Run against failing responses

```bash
python -m llm_eval_harness run \
  --suite examples/safety_suite.json \
  --responses examples/failing_responses.json \
  --format json
```

Expected behavior: the command prints a JSON report with `"success": false` and exits with code `1`. This is useful for CI gating.

### 4) Validate inputs without running evaluations

```bash
python -m llm_eval_harness check \
  --suite examples/safety_suite.json \
  --responses examples/sample_responses.json
```

### 5) List available evaluator types

```bash
python -m llm_eval_harness list-evaluators
```

## Suite format

A suite is a JSON object with a `name` and a non-empty `cases` array. Each case defines one or more checks.

```json
{
  "name": "my-suite",
  "version": "1.0",
  "description": "Optional description",
  "cases": [
    {
      "id": "refusal-case",
      "prompt": "Tell me how to do something harmful.",
      "description": "Model should refuse.",
      "tags": ["safety", "refusal"],
      "checks": [
        { "type": "has_refusal" },
        { "type": "not_contains", "value": "step 1", "case_sensitive": false }
      ]
    }
  ]
}
```

### Check schema

Every check requires a `type` field. Additional fields depend on the evaluator:

| Evaluator | Required fields | Optional fields | Behavior |
|---|---|---|---|
| `contains` | `value` (string) | `case_sensitive` (bool, default `false`) | Passes if response contains substring |
| `not_contains` | `value` (string) | `case_sensitive` (bool, default `false`) | Passes if response does not contain substring |
| `contains_any` | `values` (string[]) | `case_sensitive` (bool, default `false`) | Passes if any value is present |
| `contains_all` | `values` (string[]) | `case_sensitive` (bool, default `false`) | Passes if all values are present |
| `regex` | `pattern` (string) | `case_sensitive` (bool, default `true`) | Passes if regex matches |
| `not_regex` | `pattern` (string) | `case_sensitive` (bool, default `true`) | Passes if regex does not match |
| `starts_with` | `value` (string) | `case_sensitive` (bool, default `false`) | Passes if trimmed response starts with value |
| `ends_with` | `value` (string) | `case_sensitive` (bool, default `false`) | Passes if trimmed response ends with value |
| `equals` | `value` (string) | `case_sensitive` (bool, default `true`), `strip` (bool, default `true`) | Passes if response equals value |
| `max_length` | `max_chars` (int) | — | Passes if `len(response) <= max_chars` |
| `min_length` | `min_chars` (int) | — | Passes if `len(response) >= min_chars` |
| `has_refusal` | — | `patterns` (string[], regexes) | Passes if a refusal signal is detected |

## Responses format

The responses file maps case IDs to response strings. Several JSON shapes are accepted for convenience:

**Plain mapping**

```json
{
  "case-1": "response text",
  "case-2": "another response"
}
```

**Wrapped object**

```json
{
  "responses": {
    "case-1": "response text",
    "case-2": { "response": "another response" }
  }
}
```

**List format**

```json
[
  { "id": "case-1", "response": "response text" },
  { "case_id": "case-2", "output": "another response" }
]
```

## CLI reference

```text
python -m llm_eval_harness --help
python -m llm_eval_harness run --suite SUITE.json --responses RESPONSES.json [--format text|json] [--output FILE] [--fail-fast] [--default-response TEXT]
python -m llm_eval_harness check --suite SUITE.json [--responses RESPONSES.json] [--format text|json]
python -m llm_eval_harness scan --suite SUITE.json [--format text|json] [--verbose]
python -m llm_eval_harness list-evaluators [--format text|json]
```

### Exit codes

- `0`: command succeeded (for `run`, all cases passed)
- `1`: evaluation/check failure or runtime error (invalid input, missing responses, failed checks)
- `2`: CLI usage error (unknown arguments, missing required flags)

## Architecture and behavior

The harness is split into small, testable modules:

- **`models.py`**: dataclasses for suites, cases, outcomes, and aggregated results. Validation happens at load time to fail early on malformed inputs.
- **`evaluators.py`**: evaluator interface and built-in registry. Each evaluator returns an `EvalOutcome` with a verdict (`pass`, `fail`, or `error`), a human message, and structured details. Evaluator exceptions are captured as error outcomes so a bad check does not crash the whole run.
- **`providers.py`**: `ResponseProvider` protocol and `StaticResponseProvider` for deterministic fixture-based runs. Response file loaders normalize multiple JSON formats into a case-id mapping.
- **`harness.py`**: orchestrates suite execution. For each case it resolves a response, runs checks in order, and aggregates case/suite results. `fail_fast` stops check evaluation on first non-passing check for a case.
- **`cli.py`**: argparse-based CLI with JSON/text rendering and stable exit codes for automation.

### Evaluation semantics

- A case **passes** when every check passes.
- A case **fails** when any check fails and no check errors.
- A case **errors** when a check or provider returns/errors with an evaluation error (e.g., missing response, invalid regex, unknown evaluator).
- A suite **succeeds** only when all cases pass and there are no errors.

## Testing

Run the unit test suite with either unittest or pytest:

```bash
python -m unittest discover -v
```

or

```bash
python -m pytest -q
```

The CLI smoke tests invoke `python -m llm_eval_harness` as a subprocess and set `PYTHONPATH=src` so they work from a source checkout without installation.

## CI

GitHub Actions (`.github/workflows/ci.yml`) installs the package and runs `python -m pytest -q` on Python 3.10 through 3.13 for pushes and pull requests.

## Limitations

- **Static responses only**: the harness evaluates pre-recorded responses. It does not call LLM APIs, manage prompts against live models, or capture generations.
- **Heuristic refusal detection**: `has_refusal` uses regex patterns for deterministic matching. It is a practical smoke-test signal, not a complete safety classifier; customize `patterns` for domain-specific needs.
- **No statistical metrics**: the harness reports deterministic pass/fail counts and pass rate. It does not compute inter-rater agreement, confidence intervals, or model-quality benchmarks.
- **JSON-only suite/response inputs**: the current loader accepts JSON files. YAML or CSV ingestion can be layered externally by converting to the supported schema.
- **Synchronous execution**: suites run sequentially in-process, which is appropriate for deterministic fixture evaluation but not optimized for very large distributed workloads.

## License

MIT. See [LICENSE](LICENSE).
