"""
report.py — Repository Readiness Report generator.

Transforms raw analyzer findings into a structured, developer-oriented
readiness report. All logic is deterministic; no external API calls are made.
"""


# ---------------------------------------------------------------------------
# Project type detection
# ---------------------------------------------------------------------------

_DEPENDENCY_TYPE_MAP = {
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "package.json": "Node.js / JavaScript",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java (Gradle)",
    "Gemfile": "Ruby",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
}

_EXTENSION_TYPE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
}


def _infer_project_type(results: dict) -> str:
    """Infer project type from dependency manifests first, then extensions."""
    for dep_file in results.get("dependencies", []):
        label = _DEPENDENCY_TYPE_MAP.get(dep_file)
        if label:
            return label

    extensions: dict = results.get("extensions", {})
    if extensions:
        # Pick the dominant source extension (ignore .md, .txt, .json, etc.)
        source_exts = {
            ext: count
            for ext, count in extensions.items()
            if ext in _EXTENSION_TYPE_MAP
        }
        if source_exts:
            dominant = max(source_exts, key=source_exts.get)
            return _EXTENSION_TYPE_MAP[dominant]

    return "Unknown"


# ---------------------------------------------------------------------------
# Readiness scoring
# ---------------------------------------------------------------------------

def _compute_score(results: dict) -> tuple[int, int]:
    """Return (score, max_score) based on onboarding/readiness signals."""
    score = 0
    max_score = 5

    if results.get("readme"):
        score += 1
    if results.get("dependencies"):
        score += 1
    if results.get("tests"):
        score += 1
    if results.get("fixme_count", 0) == 0:
        score += 1
    if results.get("todo_count", 0) < 5:
        score += 1

    return score, max_score


def _status_from_score(score: int, max_score: int) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.8:
        return "Ready"
    if ratio >= 0.4:
        return "Needs Attention"
    return "Not Ready"


# ---------------------------------------------------------------------------
# Strengths and concerns
# ---------------------------------------------------------------------------

def _build_strengths(results: dict) -> list[str]:
    strengths = []

    if results.get("readme"):
        strengths.append("README is present — new developers have a starting point.")

    deps = results.get("dependencies", [])
    if deps:
        strengths.append(
            f"Dependency manifest detected ({', '.join(deps)}) — "
            "the project's requirements are declared."
        )

    tests = results.get("tests", [])
    if tests:
        strengths.append(
            f"{len(tests)} test file(s) detected — "
            "some test coverage exists."
        )

    if results.get("fixme_count", 0) == 0:
        strengths.append("No FIXME comments — no flagged broken areas in source code.")

    if results.get("todo_count", 0) < 5:
        todo_count = results.get("todo_count", 0)
        if todo_count == 0:
            strengths.append("No TODO comments — no outstanding in-code work items.")
        else:
            strengths.append(
                f"Only {todo_count} TODO comment(s) — minimal outstanding in-code work."
            )

    return strengths


def _build_concerns(results: dict) -> list[str]:
    concerns = []

    if not results.get("readme"):
        concerns.append(
            "No README found — without documentation, "
            "new developers have no entry point."
        )

    if not results.get("dependencies"):
        concerns.append(
            "No dependency manifest detected — it is unclear "
            "what this project needs to run."
        )

    if not results.get("tests"):
        concerns.append(
            "No test files detected — making changes carries unknown risk."
        )

    fixme_count = results.get("fixme_count", 0)
    if fixme_count > 0:
        concerns.append(
            f"{fixme_count} FIXME comment(s) found — "
            "these mark known broken or incomplete areas."
        )

    todo_count = results.get("todo_count", 0)
    if todo_count >= 5:
        concerns.append(
            f"{todo_count} TODO comment(s) found — "
            "there is significant unfinished in-code work."
        )

    return concerns


# ---------------------------------------------------------------------------
# Start Here recommendations
# ---------------------------------------------------------------------------

_HEALTHY_START_HERE = [
    {
        "step": "FIRST",
        "action": "Read the README",
        "reason": (
            "The README is your map. It explains what the project does, "
            "how to set it up, and what the intended workflow is."
        ),
    },
    {
        "step": "SECOND",
        "action": "Install dependencies and verify the project runs",
        "reason": (
            "A dependency manifest is present. Install it and confirm "
            "the project starts correctly before exploring the code."
        ),
    },
    {
        "step": "THIRD",
        "action": "Run the existing tests",
        "reason": (
            "Tests are present. Run them to establish a green baseline "
            "before making any changes."
        ),
    },
]


def _build_start_here(results: dict, concerns: list[str]) -> list[list[dict]]:
    """Return an ordered list of up to 3 prioritized start-here actions."""
    if not concerns:
        return _HEALTHY_START_HERE

    actions = []
    step_labels = ["FIRST", "SECOND", "THIRD"]

    # Priority-ordered concern → action mapping
    candidates = []

    if not results.get("readme"):
        candidates.append({
            "action": "Create or locate a README",
            "reason": (
                "There is no README. Before exploring the code, "
                "try to find any existing documentation (wiki, Notion, Confluence) "
                "or ask the team for a project overview."
            ),
        })

    if not results.get("dependencies"):
        candidates.append({
            "action": "Identify how to install and run this project",
            "reason": (
                "No dependency manifest was found. Look for setup instructions, "
                "Makefiles, or ask the team how to get a local environment running."
            ),
        })

    if not results.get("tests"):
        candidates.append({
            "action": "Determine whether tests exist elsewhere",
            "reason": (
                "No test files were detected. Confirm with the team whether "
                "tests exist in a separate repository or CI system before making changes."
            ),
        })

    fixme_count = results.get("fixme_count", 0)
    if fixme_count > 0:
        candidates.append({
            "action": f"Review the {fixme_count} FIXME comment(s) in the source code",
            "reason": (
                "FIXME comments mark areas the previous developer flagged as broken "
                "or incomplete. Know where they are before you start coding."
            ),
        })

    todo_count = results.get("todo_count", 0)
    if todo_count >= 5:
        candidates.append({
            "action": f"Scan the {todo_count} TODO comment(s) before planning your work",
            "reason": (
                "A high number of TODOs suggests unfinished work. "
                "Review them to avoid duplicating effort or building on incomplete code."
            ),
        })

    # Fill remaining slots with healthy fallbacks
    fallbacks = []
    if results.get("readme"):
        fallbacks.append({
            "action": "Read the README",
            "reason": "Start with the documentation to understand the project's purpose and setup.",
        })
    if results.get("dependencies"):
        fallbacks.append({
            "action": "Install dependencies and verify the project runs",
            "reason": "Confirm the project starts correctly in your local environment.",
        })
    if results.get("tests"):
        fallbacks.append({
            "action": "Run the existing tests to establish a baseline",
            "reason": "A green test suite before you change anything is your safety net.",
        })
    fallbacks.append({
        "action": "Explore the project structure",
        "reason": "Get familiar with how the code is organized before making changes.",
    })

    combined = candidates + fallbacks
    seen = set()
    for item in combined:
        key = item["action"]
        if key not in seen:
            seen.add(key)
            actions.append(item)
        if len(actions) == 3:
            break

    return [
        {"step": step_labels[i], **actions[i]}
        for i in range(len(actions))
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(results: dict) -> dict:
    """
    Generate a readiness report from analyzer results.

    Parameters
    ----------
    results : dict
        Output of analyzer.analyze_project().

    Returns
    -------
    dict with keys:
        project_type, readiness_status, readiness_score,
        strengths, concerns, start_here
    """
    project_type = _infer_project_type(results)
    score, max_score = _compute_score(results)
    status = _status_from_score(score, max_score)
    strengths = _build_strengths(results)
    concerns = _build_concerns(results)
    start_here = _build_start_here(results, concerns)

    return {
        "project_type": project_type,
        "readiness_status": status,
        "readiness_score": {"score": score, "max": max_score},
        "strengths": strengths,
        "concerns": concerns,
        "start_here": start_here,
    }


# ---------------------------------------------------------------------------
# Bob Handoff — generate a context-aware task prompt for IBM Bob
# ---------------------------------------------------------------------------

def generate_bob_task(report: dict) -> str:
    """
    Generate a focused developer task prompt from a readiness report.

    The returned string is plain text intended to be pasted directly into
    IBM Bob. It contains only information derived from the analysis —
    no hardcoded sample content.

    Parameters
    ----------
    report : dict
        Output of generate_report().

    Returns
    -------
    str — a ready-to-use Bob task prompt.
    """
    project_type = report.get("project_type", "Unknown")
    status = report.get("readiness_status", "Unknown")
    score_data = report.get("readiness_score", {})
    score = score_data.get("score", 0)
    max_score = score_data.get("max", 5)
    strengths = report.get("strengths", [])
    concerns = report.get("concerns", [])
    start_here = report.get("start_here", [])

    lines = []

    # ── Role framing ────────────────────────────────────────────────────────
    lines.append(
        "You are working as the implementation engineer on this repository."
    )
    lines.append(
        "RepoReady has analyzed the repository. "
        "Use the findings below as your starting context."
    )
    lines.append(
        "Inspect the actual repository files before making any changes."
    )
    lines.append("")

    # ── Repository summary ───────────────────────────────────────────────────
    lines.append("## Repository Summary")
    lines.append(f"Project type : {project_type}")
    lines.append(
        f"Readiness    : {status} ({score}/{max_score} onboarding signals present)"
    )
    lines.append("")

    # ── Strengths ────────────────────────────────────────────────────────────
    lines.append("## What is already in good shape")
    if strengths:
        for s in strengths:
            lines.append(f"- {s}")
    else:
        lines.append("- No clear onboarding strengths detected.")
    lines.append("")

    # ── Concerns ─────────────────────────────────────────────────────────────
    if concerns:
        lines.append("## Areas needing attention")
        for c in concerns:
            lines.append(f"- {c}")
        lines.append("")
    else:
        lines.append("## Areas needing attention")
        lines.append(
            "- No critical concerns detected. "
            "The repository has all key onboarding signals."
        )
        lines.append("")

    # ── Start Here ───────────────────────────────────────────────────────────
    lines.append("## Recommended starting points")
    if start_here:
        for item in start_here:
            step = item.get("step", "")
            action = item.get("action", "")
            reason = item.get("reason", "")
            lines.append(f"{step}: {action}")
            lines.append(f"  Reason: {reason}")
    else:
        lines.append("No specific starting points were generated.")
    lines.append("")

    # ── Task instruction — varies by health ──────────────────────────────────
    lines.append("## Task")
    if concerns:
        # Derive the top concern from the first start_here item
        top_action = start_here[0].get("action", "address the highest-priority finding") if start_here else "address the highest-priority finding"
        lines.append(
            f"Inspect the repository and investigate: {top_action}"
        )
        lines.append("")
        lines.append(
            "Do not make broad architectural changes. "
            "Make the smallest safe improvement that addresses this finding."
        )
    else:
        lines.append(
            "This repository has all key onboarding signals in place. "
            "Your task is to orient yourself and identify the safest first improvement."
        )
        lines.append("")
        lines.append("Specifically:")
        lines.append("1. Read the README and understand what this project does.")
        lines.append(
            "2. Install the dependencies and verify the project runs locally."
        )
        lines.append(
            "3. Run the existing tests and confirm they pass."
        )
        lines.append(
            "4. Identify the single safest improvement you could make "
            "without breaking existing behaviour."
        )
    lines.append("")

    # ── Verification checklist (always included) ─────────────────────────────
    lines.append("After making any changes, explain:")
    lines.append("1. What you changed")
    lines.append("2. Why you changed it")
    lines.append("3. How to verify the change is correct")
    lines.append("4. What should be checked or improved next")

    return "\n".join(lines)
