# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-obvious architectural constraints

- **Three-module pipeline — no shared state.** `analyzer.py` → `report.py` → `app.py` is a strict one-way data flow. Neither `report.py` nor `app.py` import `analyzer.py` directly except at the `app.py` call site. Do not introduce cross-imports.
- **`app.py` is the only stateful layer.** Streamlit re-runs the entire script on every interaction. All computation happens inside `if analyze_clicked:` to avoid re-running on unrelated widget changes.
- **The readiness score is a 5-point onboarding signal, not a quality metric.** Architectural decisions about score thresholds (`>= 0.8` → Ready, `>= 0.4` → Needs Attention) live in `_status_from_score()` in `report.py`. Changing thresholds changes what every repo scores — not a local change.
- **Project type inference is priority-ordered: manifest file first, dominant extension second.** A repo with both `requirements.txt` and `.js` files will always be typed as Python. This is intentional — manifest is more reliable than extension counts.
- **`_build_start_here` fills slots from candidates then fallbacks.** The maximum output is always 3 items. Adding a 4th concern candidate does not produce a 4th start-here action — it is silently dropped. If the number of displayed actions needs to change, the `step_labels` list and cap must both be updated.
- **`generate_bob_task()` branches on `len(concerns) > 0`**, not on `readiness_status`. A repo can have status "Needs Attention" with no concerns if the score falls in the 0.4–0.8 band for other reasons — though currently the score is derived directly from the same signals.
