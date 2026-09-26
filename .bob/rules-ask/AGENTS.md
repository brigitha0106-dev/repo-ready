# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-obvious documentation context

- **`README.md` in the project root is empty.** The only working README is inside `sample-project/README.md` — it documents the demo app, not RepoReady itself.
- **`sample-project/tests/test_app.py` is intentionally empty.** It exists to ensure the demo ZIP triggers the "tests detected" signal in the analyzer. It is not a real test suite.
- **`requirements.txt` at the project root contains only `streamlit`.** The `pytest` dependency in `sample-project/requirements.txt` belongs to the demo project bundled inside the ZIP, not to RepoReady.
- **There is no linter, type checker, or formatter configured.** No `pyproject.toml`, `setup.cfg`, `.flake8`, or `mypy.ini` exists. Code style is entirely unenforced.
- **`report.py` is the interpretation layer, not a utility module.** It contains the entire business logic of what RepoReady "thinks". All scoring thresholds, concern wording, and recommendation logic live here.
