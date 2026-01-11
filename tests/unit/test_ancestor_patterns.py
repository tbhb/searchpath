from pathlib import Path  # noqa: TC003 - needed at runtime for tmp_path fixture

import pytest

from searchpath._ancestor_patterns import (
    AncestorPatterns,
    collect_ancestor_patterns,
    merge_patterns,
)


class TestMergePatterns:
    def test_merges_in_order(self):
        result = merge_patterns(["a", "b"], ["c", "d"])

        assert result == ["a", "b", "c", "d"]

    def test_empty_ancestor_returns_inline(self):
        result = merge_patterns([], ["a", "b"])

        assert result == ["a", "b"]

    def test_empty_inline_returns_ancestor(self):
        result = merge_patterns(["a", "b"], [])

        assert result == ["a", "b"]

    def test_both_empty_returns_empty(self):
        result = merge_patterns([], [])

        assert result == []

    def test_works_with_tuples(self):
        result = merge_patterns(("a", "b"), ("c",))

        assert result == ["a", "b", "c"]


class TestCollectAncestorDirs:
    def test_file_at_root_returns_only_root(self, tmp_path: Path):
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=None,
            exclude_filename=None,
        )

        assert result == AncestorPatterns(include=(), exclude=())

    def test_file_not_under_root_returns_empty(self, tmp_path: Path):
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        (other_dir / "file.py").touch()

        entry_root = tmp_path / "project"
        entry_root.mkdir()

        result = collect_ancestor_patterns(
            other_dir / "file.py",
            entry_root,
            include_filename=".include",
            exclude_filename=None,
        )

        assert result == AncestorPatterns(include=(), exclude=())


class TestCollectAncestorPatterns:
    def test_no_filenames_returns_empty(self, tmp_path: Path):
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=None,
            exclude_filename=None,
        )

        assert result == AncestorPatterns(include=(), exclude=())

    def test_loads_include_from_root(self, tmp_path: Path):
        _ = (tmp_path / ".include").write_text("*.py\n", encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".include",
            exclude_filename=None,
        )

        assert result.include == ("*.py",)
        assert result.exclude == ()

    def test_loads_exclude_from_root(self, tmp_path: Path):
        _ = (tmp_path / ".exclude").write_text("*.pyc\n", encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=None,
            exclude_filename=".exclude",
        )

        assert result.include == ()
        assert result.exclude == ("*.pyc",)

    def test_loads_both_include_and_exclude(self, tmp_path: Path):
        _ = (tmp_path / ".include").write_text("*.py\n", encoding="utf-8")
        _ = (tmp_path / ".exclude").write_text("test_*\n", encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".include",
            exclude_filename=".exclude",
        )

        assert result.include == ("*.py",)
        assert result.exclude == ("test_*",)

    def test_collects_from_nested_ancestors(self, tmp_path: Path):
        subdir = tmp_path / "src"
        subdir.mkdir()
        _ = (tmp_path / ".exclude").write_text("*.log\n", encoding="utf-8")
        _ = (subdir / ".exclude").write_text("*.tmp\n", encoding="utf-8")
        (subdir / "file.py").touch()

        result = collect_ancestor_patterns(
            subdir / "file.py",
            tmp_path,
            include_filename=None,
            exclude_filename=".exclude",
        )

        assert result.exclude == ("*.log", "*.tmp")

    def test_deeply_nested_collects_all_levels(self, tmp_path: Path):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        _ = (tmp_path / ".pat").write_text("root\n", encoding="utf-8")
        _ = (tmp_path / "a" / ".pat").write_text("a\n", encoding="utf-8")
        _ = (tmp_path / "a" / "b" / ".pat").write_text("b\n", encoding="utf-8")
        (deep / "file.py").touch()

        result = collect_ancestor_patterns(
            deep / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ("root", "a", "b")

    def test_missing_pattern_file_skipped(self, tmp_path: Path):
        subdir = tmp_path / "src"
        subdir.mkdir()
        _ = (subdir / ".exclude").write_text("*.tmp\n", encoding="utf-8")
        (subdir / "file.py").touch()

        result = collect_ancestor_patterns(
            subdir / "file.py",
            tmp_path,
            include_filename=None,
            exclude_filename=".exclude",
        )

        assert result.exclude == ("*.tmp",)

    def test_uses_cache_for_repeated_calls(self, tmp_path: Path):
        _ = (tmp_path / ".pat").write_text("cached\n", encoding="utf-8")
        (tmp_path / "file.py").touch()
        cache: dict[Path, list[str]] = {}

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
            cache=cache,
        )

        assert result.include == ("cached",)
        assert tmp_path / ".pat" in cache
        assert cache[tmp_path / ".pat"] == ["cached"]

        cache[tmp_path / ".pat"] = ["modified"]

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
            cache=cache,
        )

        assert result.include == ("modified",)

    def test_strips_whitespace_and_ignores_comments(self, tmp_path: Path):
        content = """# comment
*.py
  *.txt
# another comment

*.json
"""
        _ = (tmp_path / ".pat").write_text(content, encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ("*.py", "*.txt", "*.json")

    def test_empty_pattern_file_returns_empty(self, tmp_path: Path):
        _ = (tmp_path / ".pat").write_text("", encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ()

    def test_whitespace_only_pattern_file_returns_empty(self, tmp_path: Path):
        _ = (tmp_path / ".pat").write_text("   \n\t\n  \n", encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ()

    def test_comments_only_pattern_file_returns_empty(self, tmp_path: Path):
        content = "# comment 1\n# comment 2\n"
        _ = (tmp_path / ".pat").write_text(content, encoding="utf-8")
        (tmp_path / "file.py").touch()

        result = collect_ancestor_patterns(
            tmp_path / "file.py",
            tmp_path,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ()


class TestAncestorPatternsDataclass:
    def test_is_frozen(self):
        ap = AncestorPatterns(include=("a",), exclude=("b",))

        with pytest.raises(AttributeError):
            ap.include = ("c",)  # pyright: ignore[reportAttributeAccessIssue]

    def test_equality(self):
        ap1 = AncestorPatterns(include=("a",), exclude=("b",))
        ap2 = AncestorPatterns(include=("a",), exclude=("b",))

        assert ap1 == ap2

    def test_empty_patterns(self):
        ap = AncestorPatterns(include=(), exclude=())

        assert not ap.include
        assert not ap.exclude
