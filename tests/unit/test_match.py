from pathlib import Path

import pytest

from searchpath import Match


@pytest.mark.parametrize(
    ("source", "relative_parts", "expected"),
    [
        pytest.param(
            Path("/home/user/.config/myapp"),
            ("settings", "config.toml"),
            Path("settings/config.toml"),
            id="nested-path",
        ),
        pytest.param(
            Path("/project"),
            ("pyproject.toml",),
            Path("pyproject.toml"),
            id="direct-child",
        ),
        pytest.param(
            Path("/var/lib/app"),
            ("data", "cache", "temp", "file.txt"),
            Path("data/cache/temp/file.txt"),
            id="deeply-nested",
        ),
    ],
)
def test_relative_computes_path_relative_to_source(
    source: Path, relative_parts: tuple[str, ...], expected: Path
):
    path = source.joinpath(*relative_parts)
    match = Match(path=path, scope="test", source=source)
    assert match.relative == expected
