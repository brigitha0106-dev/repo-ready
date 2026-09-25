import os
import zipfile
import tempfile


def analyze_project(zip_file):
    """
    Analyze an uploaded project ZIP file.
    Returns a dictionary containing project information.
    """

    results = {
        "files": [],
        "directories": [],
        "readme": False,
        "dependencies": [],
        "tests": [],
        "todo_count": 0,
        "fixme_count": 0,
    }

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:

        # Extract the ZIP
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Scan the extracted project
        for root, dirs, files in os.walk(temp_dir):

            for directory in dirs:
                results["directories"].append(directory)

            for file in files:
                results["files"].append(file)

                file_lower = file.lower()

                # Check for README
                if file_lower.startswith("readme"):
                    results["readme"] = True

                # Check dependency files
                if file_lower in [
                    "package.json",
                    "requirements.txt",
                    "pyproject.toml",
                    "pom.xml",
                    "build.gradle"
                ]:
                    results["dependencies"].append(file)

                # Check test files/folders
                if (
                    "test" in file_lower
                    or "spec" in file_lower
                ):
                    results["tests"].append(file)

                # Search source files for TODO/FIXME
                source_extensions = (
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".cpp",
                    ".c",
                    ".cs"
                )

                if file_lower.endswith(source_extensions):

                    file_path = os.path.join(root, file)

                    try:
                        with open(
                            file_path,
                            "r",
                            encoding="utf-8",
                            errors="ignore"
                        ) as source_file:

                            content = source_file.read()

                            results["todo_count"] += content.count("TODO")
                            results["fixme_count"] += content.count("FIXME")

                    except Exception:
                        pass

    return results