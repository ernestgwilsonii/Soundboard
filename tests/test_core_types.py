import subprocess

import pytest


def test_core_modules_type_hints():
    """
    Verify that core modules have complete type hints.
    We enforce this by running mypy with --disallow-untyped-defs.
    """
    target_files = [
        "app/models.py",
        "app/utils/audio.py",
        "app/utils/importer.py",
        "app/utils/packager.py",
    ]

    command = [
        "venv/bin/mypy",
        "--disallow-untyped-defs",
        "--ignore-missing-imports",  # Keep this to avoid failures from missing stubs for external libs
    ] + target_files

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        # Filter errors to only those in target_files
        errors = []
        for line in result.stdout.splitlines():
            for target in target_files:
                if line.startswith(target):
                    errors.append(line)
                    break

        if errors:
            pytest.fail(
                "Mypy found missing type hints in target files:\n" + "\n".join(errors)
            )
