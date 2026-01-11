from pathlib import Path

from searchpath import Match


def test_relative_computes_path_relative_to_source():
    source = Path("/home/user/.config/myapp")
    path = source / "settings" / "config.toml"
    match = Match(path=path, scope="user", source=source)

    assert match.relative == Path("settings/config.toml")


def test_relative_for_direct_child():
    source = Path("/project")
    path = source / "pyproject.toml"
    match = Match(path=path, scope="project", source=source)

    assert match.relative == Path("pyproject.toml")


def test_relative_for_deeply_nested_path():
    source = Path("/var/lib/app")
    path = source / "data" / "cache" / "temp" / "file.txt"
    match = Match(path=path, scope="system", source=source)

    assert match.relative == Path("data/cache/temp/file.txt")
