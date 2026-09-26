import os
import zipfile
import tempfile
from collections import defaultdict

# Directories that should be skipped entirely during analysis.
_SKIP_DIRS = {
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".tox",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
}

# Dependency manifest filenames (exact, case-sensitive as stored in ZIPs).
_DEPENDENCY_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "pom.xml",
    "build.gradle",
    "Gemfile",
    "go.mod",
    "Cargo.toml",
}

# Source file extensions for TODO/FIXME scanning.
_SOURCE_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".cs",
    ".go",
    ".rs",
    ".rb",
)


def analyze_project(zip_file):
    """
    Analyze an uploaded project ZIP file.
    Returns a dictionary containing project information.
    """

    results = {
        # --- original keys (preserved exactly) ---
        "files": [],
        "directories": [],
        "readme": False,
        "dependencies": [],
        "tests": [],
        "todo_count": 0,
        "fixme_count": 0,
        # --- new keys for report.py ---
        "extensions": {},   # {".py": 4, ".js": 2, ...}
    }

    extension_counts = defaultdict(int)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:

        # Extract the ZIP
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Scan the extracted project
        for root, dirs, files in os.walk(temp_dir):

            # Prune vendor / generated directories in-place so os.walk
            # does not descend into them.
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]

            for directory in dirs:
                results["directories"].append(directory)

            for file in files:
                results["files"].append(file)

                file_lower = file.lower()

                # Check for README
                if file_lower.startswith("readme"):
                    results["readme"] = True

                # Check dependency files (match both original lowercase set
                # and the extended set which includes mixed-case names).
                if file in _DEPENDENCY_FILES or file_lower in _DEPENDENCY_FILES:
                    if file not in results["dependencies"]:
                        results["dependencies"].append(file)

                # Check test files/folders — only count files with actual content
                # (a filename match alone is not sufficient; empty files do not
                # provide test coverage and should not score the tests signal).
                if "test" in file_lower or "spec" in file_lower:
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as tf:
                            has_content = any(
                                line.strip() and not line.strip().startswith("#")
                                for line in tf
                            )
                        if has_content:
                            results["tests"].append(file)
                    except Exception:
                        pass  # unreadable files are silently skipped

                # Track file extensions for project-type inference
                _, ext = os.path.splitext(file_lower)
                if ext:
                    extension_counts[ext] += 1

                # Search source files for TODO/FIXME
                if file_lower.endswith(_SOURCE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    try:
                        with open(
                            file_path,
                            "r",
                            encoding="utf-8",
                            errors="ignore",
                        ) as source_file:
                            content = source_file.read()
                            results["todo_count"] += content.count("TODO")
                            results["fixme_count"] += content.count("FIXME")
                    except Exception:
                        pass

    results["extensions"] = dict(extension_counts)
    return results