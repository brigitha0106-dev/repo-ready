# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Non-obvious coding rules

- **Do not add new keys to `results`** in `analyzer.py` without also updating `report.py`'s consumers. The key contract between the two modules is implicit (no dataclass/TypedDict).
- **`dirs[:] = [...]` must stay in-place** in the `os.walk` loop. Replacing it with a skip-based `continue` will break directory pruning and cause vendor files to be counted.
- **`generate_report()` must remain pure** — no I/O, no side effects. It is called inside a `st.spinner` block; any blocking call will freeze the UI.
- **`generate_bob_task()` takes the *report* dict**, not the raw `results` dict. Passing `results` directly will silently produce an empty-field prompt (all `.get()` calls return defaults).
- **Tab variable names are positional** — `tab0` through `tab5` must match the order in `st.tabs([...])`. Reordering the list without renaming the variables will swap tab content silently.
- **`readiness_score["max"]` is hardcoded to 5** in `_compute_score`. Adding a new scoring signal without incrementing `max_score` will inflate every repo's percentage.
- **`_HEALTHY_START_HERE` is a module-level constant** reused across calls. Do not mutate it; `_build_start_here` must never append to it in-place.
- **`mcp_server.py` uses mcp v2 API** — `MCPServer` not `FastMCP`. `FastMCP` does not exist in this install and will raise `ModuleNotFoundError`.
- **`repo_ready_analyze` must receive an absolute path** — the tool rejects relative paths explicitly. Bob must call `os.path.abspath()` or use `${workspaceFolder}` when constructing the argument.
- **The MCP tool returns a JSON *string***, not a dict. The MCP framework wraps it in `content[0].text`. Parse with `json.loads()` before accessing fields.
