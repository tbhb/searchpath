from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeAlias, cast

import pytest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem

_DIRECTORY_MARKERS: dict[str, str] = {
    "benchmarks": "benchmark",
    "examples": "example",
    "fuzz": "fuzz",
    "integration": "integration",
    "properties": "property",
    "unit": "unit",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Automatically mark tests based on their directory location."""
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


@dataclass(frozen=True, slots=True)
class Symlink:
    """A symbolic link pointing to a target path.

    The target is relative to the root of the tree being created.

    Example:
        >>> tree = {
        ...     "src": {"main.py": "print('hello')"},
        ...     "link_to_src": Symlink("src"),
        ... }
    """

    target: str


TreeEntry: TypeAlias = "str | Symlink | TreeSpec"
TreeSpec: TypeAlias = dict[str, TreeEntry]


class TreeFactory(Protocol):
    """Protocol for tree factory functions.

    Factory functions take a tree specification and optionally a root path,
    and create the corresponding directory structure.
    """

    def __call__(self, spec: TreeSpec, root: Path | str | None = None) -> Path: ...


def _create_file(path: Path, content: str) -> None:
    """Create a file with the given content."""
    _ = path.write_text(content)


def _create_symlink(path: Path, target: Path, fake_fs: "FakeFilesystem | None") -> None:
    """Create a symbolic link."""
    if fake_fs is not None:
        _ = fake_fs.create_symlink(str(path), str(target))
    else:
        path.symlink_to(target)


def _create_directory(
    path: Path,
    contents: "TreeSpec",
    root: Path,
    fake_fs: "FakeFilesystem | None",
) -> None:
    """Create a directory with the given contents."""
    if fake_fs is not None:
        _ = fake_fs.create_dir(str(path))
    else:
        path.mkdir(parents=True, exist_ok=True)
    for child_name, child_entry in contents.items():
        _create_tree_entry(path, child_name, child_entry, root, fake_fs=fake_fs)


def _create_tree_entry(
    base: Path,
    name: str,
    entry: TreeEntry,
    root: Path,
    *,
    fake_fs: "FakeFilesystem | None" = None,
) -> None:
    """Create a single tree entry (file, directory, or symlink)."""
    path = base / name

    if isinstance(entry, str):
        _create_file(path, entry)
    elif isinstance(entry, Symlink):
        _create_symlink(path, root / entry.target, fake_fs)
    else:
        _create_directory(path, entry, root, fake_fs)


@pytest.fixture
def fake_tree(fs: "FakeFilesystem") -> TreeFactory:
    """Create a fake file tree for unit tests using pyfakefs.

    Returns a factory function that takes a tree specification and creates
    the corresponding directory structure in the fake filesystem.

    Example:
        >>> def test_something(fake_tree):
        ...     root = fake_tree(
        ...         {
        ...             "src": {
        ...                 "main.py": "print('hello')",
        ...                 "utils": {
        ...                     "__init__.py": "",
        ...                 },
        ...             },
        ...             "README.md": "# My Project",
        ...             "link_to_src": Symlink("src"),
        ...         }
        ...     )
        ...     assert (root / "src" / "main.py").exists()
    """

    def create(spec: TreeSpec, root: Path | str | None = None) -> Path:
        if root is None:
            root_path = Path("/")
        elif isinstance(root, str):
            root_path = Path(root)
        else:
            root_path = root

        _ = fs.create_dir(str(root_path))

        for name, entry in spec.items():
            _create_tree_entry(root_path, name, entry, root_path, fake_fs=fs)

        return root_path

    return create


@pytest.fixture
def tmp_tree(tmp_path: Path) -> TreeFactory:
    """Create a temporary file tree for integration tests.

    Returns a factory function that takes a tree specification and creates
    the corresponding directory structure under pytest's tmp_path.

    Example:
        >>> def test_something(tmp_tree):
        ...     root = tmp_tree(
        ...         {
        ...             "src": {
        ...                 "main.py": "print('hello')",
        ...             },
        ...             "config.toml": "[settings]\\nkey = 'value'",
        ...         }
        ...     )
        ...     assert (root / "src" / "main.py").read_text() == "print('hello')"
    """

    def create(spec: TreeSpec, root: Path | str | None = None) -> Path:
        if root is None:
            root_path = tmp_path
        elif isinstance(root, str):
            root_path = tmp_path / root
            root_path.mkdir(parents=True, exist_ok=True)
        else:
            root_path = root
            root_path.mkdir(parents=True, exist_ok=True)

        for name, entry in spec.items():
            _create_tree_entry(root_path, name, entry, root_path)

        return root_path

    return create
