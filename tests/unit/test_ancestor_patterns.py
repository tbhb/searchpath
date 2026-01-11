from typing import TYPE_CHECKING

import pytest

from searchpath._ancestor_patterns import (
    AncestorPatterns,
    collect_ancestor_patterns,
    merge_patterns,
)

if TYPE_CHECKING:
    from pathlib import Path

    from conftest import TreeFactory


class TestMergePatterns:
    def test_merges_in_order(self):
        result = merge_patterns(["a", "b"], ["c", "d"])

        assert result == ["a", "b", "c", "d"]

    @pytest.mark.parametrize(
        ("ancestor", "inline", "expected"),
        [
            pytest.param(
                [], ["a", "b"], ["a", "b"], id="empty-ancestor-returns-inline"
            ),
            pytest.param(
                ["a", "b"], [], ["a", "b"], id="empty-inline-returns-ancestor"
            ),
            pytest.param([], [], [], id="both-empty-returns-empty"),
        ],
    )
    def test_merge_empty_cases(
        self, ancestor: list[str], inline: list[str], expected: list[str]
    ):
        result = merge_patterns(ancestor, inline)
        assert result == expected

    def test_works_with_tuples(self):
        result = merge_patterns(("a", "b"), ("c",))

        assert result == ["a", "b", "c"]


class TestCollectAncestorDirs:
    def test_file_at_root_returns_only_root(self, fake_tree: "TreeFactory"):
        root = fake_tree({"file.py": ""})

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=None,
            exclude_filename=None,
        )

        assert result == AncestorPatterns(include=(), exclude=())

    def test_file_not_under_root_returns_empty(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                "other": {"file.py": ""},
                "project": {},
            }
        )

        result = collect_ancestor_patterns(
            root / "other" / "file.py",
            root / "project",
            include_filename=".include",
            exclude_filename=None,
        )

        assert result == AncestorPatterns(include=(), exclude=())


class TestCollectAncestorPatterns:
    def test_no_filenames_returns_empty(self, fake_tree: "TreeFactory"):
        root = fake_tree({"file.py": ""})

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=None,
            exclude_filename=None,
        )

        assert result == AncestorPatterns(include=(), exclude=())

    def test_loads_include_from_root(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                ".include": "*.py\n",
                "file.py": "",
            }
        )

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=".include",
            exclude_filename=None,
        )

        assert result.include == ("*.py",)
        assert result.exclude == ()

    def test_loads_exclude_from_root(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                ".exclude": "*.pyc\n",
                "file.py": "",
            }
        )

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=None,
            exclude_filename=".exclude",
        )

        assert result.include == ()
        assert result.exclude == ("*.pyc",)

    def test_loads_both_include_and_exclude(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                ".include": "*.py\n",
                ".exclude": "test_*\n",
                "file.py": "",
            }
        )

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=".include",
            exclude_filename=".exclude",
        )

        assert result.include == ("*.py",)
        assert result.exclude == ("test_*",)

    def test_collects_from_nested_ancestors(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                ".exclude": "*.log\n",
                "src": {
                    ".exclude": "*.tmp\n",
                    "file.py": "",
                },
            }
        )

        result = collect_ancestor_patterns(
            root / "src" / "file.py",
            root,
            include_filename=None,
            exclude_filename=".exclude",
        )

        assert result.exclude == ("*.log", "*.tmp")

    def test_deeply_nested_collects_all_levels(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                ".pat": "root\n",
                "a": {
                    ".pat": "a\n",
                    "b": {
                        ".pat": "b\n",
                        "c": {
                            "file.py": "",
                        },
                    },
                },
            }
        )

        result = collect_ancestor_patterns(
            root / "a" / "b" / "c" / "file.py",
            root,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ("root", "a", "b")

    def test_missing_pattern_file_skipped(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                "src": {
                    ".exclude": "*.tmp\n",
                    "file.py": "",
                },
            }
        )

        result = collect_ancestor_patterns(
            root / "src" / "file.py",
            root,
            include_filename=None,
            exclude_filename=".exclude",
        )

        assert result.exclude == ("*.tmp",)

    def test_uses_cache_for_repeated_calls(self, fake_tree: "TreeFactory"):
        root = fake_tree(
            {
                ".pat": "cached\n",
                "file.py": "",
            }
        )
        cache: dict[Path, list[str]] = {}

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=".pat",
            exclude_filename=None,
            cache=cache,
        )

        assert result.include == ("cached",)
        assert root / ".pat" in cache
        assert cache[root / ".pat"] == ["cached"]

        cache[root / ".pat"] = ["modified"]

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=".pat",
            exclude_filename=None,
            cache=cache,
        )

        assert result.include == ("modified",)

    def test_strips_whitespace_and_ignores_comments(self, fake_tree: "TreeFactory"):
        content = """# comment
*.py
  *.txt
# another comment

*.json
"""
        root = fake_tree(
            {
                ".pat": content,
                "file.py": "",
            }
        )

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ("*.py", "*.txt", "*.json")

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param("", id="empty-file"),
            pytest.param("   \n\t\n  \n", id="whitespace-only"),
            pytest.param("# comment 1\n# comment 2\n", id="comments-only"),
        ],
    )
    def test_pattern_file_returns_empty(self, fake_tree: "TreeFactory", content: str):
        root = fake_tree(
            {
                ".pat": content,
                "file.py": "",
            }
        )

        result = collect_ancestor_patterns(
            root / "file.py",
            root,
            include_filename=".pat",
            exclude_filename=None,
        )

        assert result.include == ()
