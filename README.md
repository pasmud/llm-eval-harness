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

