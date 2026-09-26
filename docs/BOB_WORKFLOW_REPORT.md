# RepoReady + IBM Bob MCP Workflow

## Purpose

RepoReady is a developer onboarding assistant that analyzes an unfamiliar repository and produces a structured readiness report - covering project type, dependency health, test coverage signals, and prioritized actions. It exposes this analysis to IBM Bob through the `repo_ready_analyze` MCP tool, so Bob can receive structured findings directly rather than through manual copy-paste. Together they form a closed loop: RepoReady diagnoses, Bob investigates and acts.

---

## Architecture

```
Repository ZIP
      |
      v
analyzer.py          - deterministic scan: files, deps, tests, TODOs, extensions
      |
      v
report.py            - scoring, strengths, concerns, start_here recommendations
      |
      v
mcp_server.py        - STDIO MCP server wrapping the pipeline
      |
      v  (JSON over stdio)
IBM Bob Agent        - reads findings, investigates, proposes and implements fixes
```

No LLM is involved in the analysis layer. Every finding is derived from file evidence.

---

## MCP Tool

| Property | Value |
|---|---|
| **Tool name** | `repo_ready_analyze` |
| **Transport** | STDIO (Bob spawns the server as a child process) |
| **Configuration** | `.bob/mcp.json` - workspace-scoped, no credentials required |
| **Input** | `zip_path` - absolute path to a repository ZIP file on disk |
| **Output** | Structured JSON containing: |
| | `project_type` - inferred from dependency manifest or dominant file extension |
| | `readiness_status` - `"Ready"` / `"Needs Attention"` / `"Not Ready"` |
| | `readiness_score` - `{ score: N, max: 5 }` onboarding signal count |
| | `strengths` - list of positively-evidenced findings |
| | `concerns` - list of missing or problematic signals |
| | `start_here` - up to 3 prioritized actions with step labels and reasons |
| | `_raw` - file count, directory count, TODO/FIXME counts, dependency files |

---

## Demonstrated Workflow

### Step 1 - Initial MCP analysis
Bob called `repo_ready_analyze` on `sample-project.zip`. The tool returned:

- **Score:** 5/5 - all onboarding signals satisfied
- **Status:** Ready
- **Concerns:** none
- **Start Here:** Read the README -> Install dependencies -> Run the existing tests

### Step 2 - Independent file inspection
Bob was asked to verify whether the 5/5 result was consistent with the actual repository contents. Bob read the ZIP directly and found:

- `sample-project/app.py` - valid Python source, no TODOs
- `sample-project/tests/test_app.py` - **completely empty**

### Step 3 - Root cause tracing
Bob traced the inflated score to the test-detection logic in `analyzer.py`. The check was purely filename-based:

```python
if "test" in file_lower or "spec" in file_lower:
    results["tests"].append(file)
```

An empty file named `test_app.py` satisfied this condition and earned the tests signal without containing a single assertion.

### Step 4 - Fix proposed
Bob proposed a minimal, localized change: before appending a file to `results["tests"]`, open it and check for at least one non-blank, non-comment line. Files that are empty or contain only `#` comments are skipped.

### Step 5 - Fix implemented
The change was made to `analyzer.py` only. No other files were modified. The `results["tests"]` contract (a list of filenames) was preserved.

### Step 6 - Re-analysis via MCP
Bob called `repo_ready_analyze` again after the server reloaded. The result:

- **Score:** 4/5
- **Status:** Ready (4/5 = 80%, meets the >= 0.8 threshold)
- **Tests detected:** 0
- **Concerns:** *"No test files detected - making changes carries unknown risk."*
- **Start Here (updated):**
  1. FIRST - Determine whether tests exist elsewhere
  2. SECOND - Read the README
  3. THIRD - Install dependencies and verify the project runs

The empty test file no longer inflates the score. The concern is surfaced and the start-here recommendations reflect it.

---

## AI Contribution

| Layer | Who does it | How |
|---|---|---|
| File extraction and scanning | RepoReady (`analyzer.py`) | Deterministic - `os.walk`, string matching, file I/O |
| Scoring and recommendations | RepoReady (`report.py`) | Deterministic - rule-based thresholds and templates |
| MCP transport | RepoReady (`mcp_server.py`) | Deterministic - serialises findings to JSON over stdio |
| Receiving and interpreting findings | **IBM Bob** | AI reasoning over the structured JSON |
| Cross-referencing against actual files | **IBM Bob** | Bob read the ZIP contents independently to verify claims |
| Root cause identification | **IBM Bob** | Bob traced the inflated score to the exact line in `analyzer.py` |
| Fix design and implementation | **IBM Bob** | Bob proposed the minimal safe change and applied it |
| Verification | **IBM Bob** | Bob re-ran the MCP tool and confirmed the corrected output |

RepoReady provides the structured evidence. IBM Bob provides the reasoning, investigation, and action.

---

## Limitations

- **Local ZIP path required** - the MCP tool currently accepts a path to a ZIP file on the local filesystem. It cannot accept a URL, a git remote, or a Streamlit in-memory upload directly from the UI.
- **Bob as the AI development environment** - this prototype is designed for use within IBM Bob. The MCP server runs as a local stdio process registered in `.bob/mcp.json` and is not exposed as a network service.
- **Readiness score is onboarding-signal only** - a score of 5/5 means all five checked signals are present; it does not assess code quality, security, or architectural soundness.
- **Test detection is content-heuristic, not runtime** - the fix distinguishes empty files from non-empty ones, but does not execute tests or validate that assertions are correct.
