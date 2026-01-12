from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from searchpath import SearchPath

if TYPE_CHECKING:
    from pytest_codspeed.plugin import BenchmarkFixture

Entry = tuple[str, Path]


def _create_file_tree(root: Path, num_files: int, depth: int = 3) -> None:
    root.mkdir(parents=True, exist_ok=True)
    files_per_level = max(1, num_files // depth)

    for level in range(depth):
        level_dir = root
        for i in range(level):
            level_dir = level_dir / f"dir{i}"
        level_dir.mkdir(parents=True, exist_ok=True)

        for i in range(files_per_level):
            file_path = level_dir / f"file{i}.py"
            file_path.touch()


class TestBenchSearchPathExactLookup:
    def test_first_exact_single_entry(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        (tmp_path / "config.toml").touch()
        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.first("config.toml"))
        assert result is not None

    def test_first_exact_multi_entry(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        dirs: list[Path] = []
        for i in range(5):
            d = tmp_path / f"dir{i}"
            d.mkdir()
            dirs.append(d)

        (dirs[2] / "config.toml").touch()

        entries: list[Entry] = [(f"scope{i}", d) for i, d in enumerate(dirs)]
        sp = SearchPath(*entries)

        result = benchmark(lambda: sp.first("config.toml"))
        assert result is not None

    def test_first_exact_not_found(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        dirs: list[Path] = []
        for i in range(5):
            d = tmp_path / f"dir{i}"
            d.mkdir()
            (d / "other.txt").touch()
            dirs.append(d)

        entries: list[Entry] = [(f"scope{i}", d) for i, d in enumerate(dirs)]
        sp = SearchPath(*entries)

        result = benchmark(lambda: sp.first("config.toml"))
        assert result is None


class TestBenchSearchPathGlobSmall:
    def test_all_glob_100_files(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 100)
        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.all("**/*.py"))
        assert len(result) > 0

    def test_all_glob_500_files(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 500, depth=5)
        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.all("**/*.py"))
        assert len(result) > 0


class TestBenchSearchPathGlobMedium:
    def test_all_glob_1000_files(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 1000, depth=5)
        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.all("**/*.py"))
        assert len(result) > 0

    def test_all_glob_2000_files(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 2000, depth=6)
        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.all("**/*.py"))
        assert len(result) > 0


@pytest.mark.slow
class TestBenchSearchPathGlobLarge:
    def test_all_glob_10000_files(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 10000, depth=8)
        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.all("**/*.py"))
        assert len(result) > 0


class TestBenchSearchPathMultiEntry:
    def test_all_multi_entry_500_files_each(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        entries: list[Entry] = []
        for i in range(3):
            entry_dir = tmp_path / f"entry{i}"
            _create_file_tree(entry_dir, 500, depth=4)
            entries.append((f"scope{i}", entry_dir))

        sp = SearchPath(*entries)

        result = benchmark(lambda: sp.all("**/*.py"))
        assert len(result) > 0

    def test_first_multi_entry_early_hit(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        entries: list[Entry] = []
        for i in range(3):
            entry_dir = tmp_path / f"entry{i}"
            _create_file_tree(entry_dir, 100, depth=3)
            entries.append((f"scope{i}", entry_dir))

        (tmp_path / "entry0" / "target.py").touch()
        sp = SearchPath(*entries)

        result = benchmark(lambda: sp.first("**/target.py"))
        assert result is not None

    def test_first_multi_entry_late_hit(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        entries: list[Entry] = []
        for i in range(3):
            entry_dir = tmp_path / f"entry{i}"
            _create_file_tree(entry_dir, 100, depth=3)
            entries.append((f"scope{i}", entry_dir))

        (tmp_path / "entry2" / "target.py").touch()
        sp = SearchPath(*entries)

        result = benchmark(lambda: sp.first("**/target.py"))
        assert result is not None


class TestBenchSearchPathWithExclude:
    def test_all_with_exclude_pattern(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 500, depth=5)

        test_dir = tmp_path / "__pycache__"
        test_dir.mkdir()
        for i in range(50):
            (test_dir / f"file{i}.pyc").touch()

        sp = SearchPath(("project", tmp_path))

        result = benchmark(lambda: sp.all("**/*.py", exclude=["__pycache__/**"]))
        assert len(result) > 0

    def test_all_with_multiple_excludes(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 500, depth=5)

        for excl in ["__pycache__", ".git", "node_modules"]:
            excl_dir = tmp_path / excl
            excl_dir.mkdir()
            for i in range(20):
                (excl_dir / f"file{i}").touch()

        sp = SearchPath(("project", tmp_path))

        result = benchmark(
            lambda: sp.all(
                "**/*.py",
                exclude=["__pycache__/**", ".git/**", "node_modules/**"],
            )
        )
        assert len(result) > 0


class TestBenchSearchPathDeduplication:
    def test_all_dedupe_overlapping_entries(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        base_dir = tmp_path / "base"
        _create_file_tree(base_dir, 200, depth=3)

        override_dir = tmp_path / "override"
        override_dir.mkdir()
        for f in list(base_dir.rglob("*.py"))[:50]:
            rel = f.relative_to(base_dir)
            target = override_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()

        sp = SearchPath(("override", override_dir), ("base", base_dir))

        result = benchmark(lambda: sp.all("**/*.py", dedupe=True))
        assert len(result) > 0

    def test_all_no_dedupe_overlapping_entries(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        base_dir = tmp_path / "base"
        _create_file_tree(base_dir, 200, depth=3)

        override_dir = tmp_path / "override"
        override_dir.mkdir()
        for f in list(base_dir.rglob("*.py"))[:50]:
            rel = f.relative_to(base_dir)
            target = override_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()

        sp = SearchPath(("override", override_dir), ("base", base_dir))

        result = benchmark(lambda: sp.all("**/*.py", dedupe=False))
        assert len(result) > 0


class TestBenchSearchPathAncestors:
    def test_all_with_exclude_from_ancestors(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        _create_file_tree(tmp_path, 500, depth=5)

        _ = (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        sub_dir = tmp_path / "dir0"
        if sub_dir.exists():
            _ = (sub_dir / ".gitignore").write_text("*.log\n")

        sp = SearchPath(("project", tmp_path))

        result = benchmark(
            lambda: sp.all("**/*.py", exclude_from_ancestors=".gitignore")
        )
        assert len(result) > 0

    def test_all_deep_ancestor_chain(
        self, benchmark: "BenchmarkFixture", tmp_path: Path
    ) -> None:
        depth = 8
        current = tmp_path
        for i in range(depth):
            _ = (current / ".gitignore").write_text(f"ignore{i}.txt\n")
            current = current / f"level{i}"
            current.mkdir()
            (current / f"file{i}.py").touch()

        sp = SearchPath(("project", tmp_path))

        result = benchmark(
            lambda: sp.all("**/*.py", exclude_from_ancestors=".gitignore")
        )
        assert len(result) > 0
