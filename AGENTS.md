# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack

- Python 3, Streamlit — dependencies: `streamlit`, `mcp` (declared in `requirements.txt`)
- No linter, no formatter, no type checker configured

## Run / Test

```bash
# Start the Streamlit app
streamlit run app.py

# Start the MCP server (Bob spawns this automatically via .bob/mcp.json)
python mcp_server.py

# Syntax-check all modules
python -m py_compile analyzer.py report.py app.py mcp_server.py

# Functional smoke-test — call the MCP tool function directly (no server needed)
python -c "
import asyncio, json, os, sys
sys.path.insert(0, os.path.abspath('.'))
from mcp_server import repo_ready_analyze
result = asyncio.run(repo_ready_analyze(zip_path=os.path.abspath('sample-project.zip')))
print(json.dumps(json.loads(result), indent=2))
"
```

No `pytest` is configured for the RepoReady app itself.
`sample-project/requirements.txt` contains `pytest` — that is the **demo repository bundled inside the ZIP**, not the test runner for RepoReady.

## Architecture — data flow

```
uploaded ZIP (Streamlit UI)
  └─ analyzer.analyze_project()   → results dict (7 original keys + "extensions")
       └─ report.generate_report()  → report dict (6 keys)
            ├─ report.generate_bob_task() → plain-text Bob prompt (str)
            └─ app.py renders everything in st.tabs()

ZIP path (IBM Bob via MCP)
  └─ mcp_server.repo_ready_analyze(zip_path)
       └─ analyzer.analyze_project()  →  report.generate_report()  → JSON string
```

- **`analyzer.py`** — only reads ZIPs; no state; returns a plain dict every call.
- **`report.py`** — pure functions; no I/O; takes the `results` dict, returns derived dicts/strings.
- **`app.py`** — all Streamlit UI; calls the above two in sequence inside the `if analyze_clicked:` block.
- **`mcp_server.py`** — STDIO MCP server; re-uses `analyzer` + `report`; registered via `.bob/mcp.json`. Tool accepts an **absolute path** to a ZIP; returns JSON.

## Critical conventions

- `analyzer.py` prunes `_SKIP_DIRS` (`node_modules`, `.git`, `venv`, `__pycache__`, etc.) via `dirs[:] = [...]` **in-place** so `os.walk` never descends into them. Do not replace this with a post-filter.
- The original 7 `results` keys (`files`, `directories`, `readme`, `dependencies`, `tests`, `todo_count`, `fixme_count`) must stay unchanged — `report.py` and `app.py` both read them directly. New keys are additive only.
- `generate_bob_task()` accepts the **report dict** (output of `generate_report`), not the raw `results` dict.
- `app.py` uses `st.code(bob_task, language=None)` for the Bob Handoff block — Streamlit renders a native copy button; no JS required.
- The "Readiness Report" tab is `tab0`; the original five detail tabs are `tab1`–`tab5`. The tab variable names matter for ordering.
- `readiness_score` is an **onboarding signal score only** (max 5). It does not claim production-readiness. Do not add more signals without a matching `max_score` increment.

## MCP server (`mcp_server.py`)

- Uses `mcp` **v2** — `MCPServer` from `mcp.server.mcpserver`, decorator `@server.tool()`, entry point `server.run_stdio_async()`. The v1 `FastMCP` import path **does not exist** in this version.
- The tool function `repo_ready_analyze` is `async` and must receive an **absolute path**. It returns a JSON string (not a dict) — the MCP layer wraps it in a `content` array automatically.
- `_PROJECT_ROOT` is inserted into `sys.path` at module load so `analyzer` and `report` are importable regardless of Bob's working directory when it spawns the server.
- Registered at **workspace scope** in `.bob/mcp.json` using `${workspaceFolder}` — no global installation needed.
- No credentials, no env vars, no external services required.

## sample-project

`sample-project/` and `sample-project.zip` are the **controlled demo input**. The ZIP is used for smoke-testing. `sample-project/tests/test_app.py` is intentionally empty (demo artifact).
