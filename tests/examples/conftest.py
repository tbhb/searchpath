"""Configuration for documentation example tests."""

import sys


def check_version_skip(source: str) -> str | None:
    """Check if example should be skipped based on Python version markers.

    Args:
        source: The source code of the example.

    Returns:
        Skip reason if example should be skipped, None otherwise.
    """
    version = sys.version_info[:2]

    # Check for version-specific markers in comments
    if "# Python 3.11+" in source and version < (3, 11):
        return "Requires Python 3.11+"
    if "# Python 3.12+" in source and version < (3, 12):
        return "Requires Python 3.12+"

    return None
