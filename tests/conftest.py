from pathlib import Path
from typing import cast

import pytest

_DIRECTORY_MARKERS: dict[str, str] = {
    "benchmarks": "benchmark",
    "examples": "example",
    "fuzz": "fuzz",
    "integration": "integration",
    "properties": "property",
    "unit": "unit",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    tests_dir = Path(__file__).parent

    for item in items:
        item_path = Path(item.fspath)

        try:
            relative = item_path.relative_to(tests_dir)
            if relative.parts:
                subdir = relative.parts[0]
                if marker_name := _DIRECTORY_MARKERS.get(subdir):
                    marker = cast(
                        "pytest.MarkDecorator", getattr(pytest.mark, marker_name)
                    )
                    item.add_marker(marker)
        except ValueError:
            pass
