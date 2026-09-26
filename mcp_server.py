#!/usr/bin/env python3
"""
mcp_server.py — RepoReady MCP server.

Exposes the RepoReady analysis pipeline as a single MCP tool so that
IBM Bob can call it directly without manual copy-paste.

Transport: STDIO (spawned as a child process by Bob).
No LLM, no external API, no credentials required.

Tool exposed:
  repo_ready_analyze(zip_path: str) -> dict
    Analyzes a repository ZIP and returns the structured readiness report.
"""

import asyncio
import json
import os
import sys
from typing import Annotated

# Ensure the RepoReady project root is on the path so analyzer/report
# are importable regardless of the working directory Bob uses.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from mcp.server.mcpserver import MCPServer  # mcp 2.x

from analyzer import analyze_project
from report import generate_report

# ---------------------------------------------------------------------------
# Server definition
# ---------------------------------------------------------------------------

server = MCPServer(
    name="repoready",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Tool: repo_ready_analyze
# ---------------------------------------------------------------------------

@server.tool(
    name="repo_ready_analyze",
    description=(
        "Analyze a repository ZIP file and return a structured readiness report. "
        "Returns project_type, readiness_status, readiness_score, strengths, "
        "concerns, and prioritized start_here actions. "
        "Pass the absolute path to a .zip file on disk."
    ),
)
async def repo_ready_analyze(
    zip_path: Annotated[str, "Absolute path to the repository ZIP file to analyze"],
) -> str:
    """Analyze a repository ZIP and return JSON-encoded readiness findings."""

    # Validate input
    if not zip_path:
        return json.dumps({"error": "zip_path is required"})

    if not os.path.isabs(zip_path):
        return json.dumps({
            "error": (
                f"zip_path must be an absolute path. "
                f"Received: {zip_path!r}. "
                f"Hint: the sample ZIP is at {os.path.join(_PROJECT_ROOT, 'sample-project.zip')!r}"
            )
        })

    if not os.path.exists(zip_path):
        return json.dumps({"error": f"File not found: {zip_path!r}"})

    if not zip_path.lower().endswith(".zip"):
        return json.dumps({"error": f"Expected a .zip file, got: {zip_path!r}"})

    try:
        with open(zip_path, "rb") as f:
            results = analyze_project(f)

        report = generate_report(results)

        # Return the report as a clean JSON string.
        # Include the raw file/test counts as a lightweight summary.
        output = {
            "project_type": report["project_type"],
            "readiness_status": report["readiness_status"],
            "readiness_score": report["readiness_score"],
            "strengths": report["strengths"],
            "concerns": report["concerns"],
            "start_here": report["start_here"],
            # Lightweight raw counts for Bob's context
            "_raw": {
                "file_count": len(results["files"]),
                "directory_count": len(results["directories"]),
                "test_file_count": len(results["tests"]),
                "todo_count": results["todo_count"],
                "fixme_count": results["fixme_count"],
                "dependency_files": results["dependencies"],
            },
        }
        return json.dumps(output, indent=2, ensure_ascii=False)

    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Analysis failed: {exc}"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(server.run_stdio_async())
