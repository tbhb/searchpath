import os
from typing import TYPE_CHECKING, Literal

import pytest

from searchpath import GlobMatcher
from searchpath._traversal import traverse

from tests.conftest import Symlink

if TYPE_CHECKING:
    from tests.conftest import TreeFactory


class TestTraverseBasic:
    def test_basic_file_discovery(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file1.py": "",
                "file2.py": "",
                "file.txt": "",
            }
        )

        result = sorted(traverse(root))

        assert result == sorted(
            [
                root / "file1.py",
                root / "file2.py",
                root / "file.txt",
            ]
        )

    @pytest.mark.parametrize(
        ("kind", "expected_names"),
        [
            pytest.param("dirs", ["dir1", "dir2"], id="kind-dirs-returns-directories"),
            pytest.param(
                "both", ["dir1", "dir2", "file.txt"], id="kind-both-returns-all"
            ),
        ],
    )
    def test_kind_filtering(
        self,
        tmp_tree: "TreeFactory",
        kind: Literal["dirs", "both"],
        expected_names: list[str],
    ):
        root = tmp_tree(
            {
                "dir1": {},
                "dir2": {},
                "file.txt": "",
            }
        )

        result = sorted(traverse(root, kind=kind))

        expected = sorted([root / name for name in expected_names])
        assert result == expected

    def test_pattern_matching_star(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file.py": "",
                "file.txt": "",
            }
        )

        result = list(traverse(root, pattern="*.py"))

        assert result == [root / "file.py"]

    def test_pattern_matching_recursive(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "src": {
                    "main.py": "",
                },
                "test.py": "",
                "readme.txt": "",
            }
        )

        result = sorted(traverse(root, pattern="**/*.py"))

        assert result == sorted([root / "src" / "main.py", root / "test.py"])

    def test_pattern_matching_specific_dir(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "src": {
                    "main.py": "",
                },
                "tests": {
                    "test.py": "",
                },
            }
        )

        result = list(traverse(root, pattern="src/*.py"))

        assert result == [root / "src" / "main.py"]

    def test_nonexistent_root_yields_nothing(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({})
        nonexistent = root / "nonexistent"

        result = list(traverse(nonexistent))

        assert result == []

    def test_file_as_root_yields_nothing(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file.txt": "",
            }
        )

        result = list(traverse(root / "file.txt"))

        assert result == []

    def test_empty_directory_yields_nothing(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({})

        result = list(traverse(root))

        assert result == []

    def test_nested_directories(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "a": {
                    "b": {
                        "c": {
                            "file.py": "",
                        },
                    },
                },
            }
        )

        result = list(traverse(root, pattern="**/*.py"))

        assert result == [root / "a" / "b" / "c" / "file.py"]

    def test_accepts_string_path(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file.py": "",
            }
        )

        result = list(traverse(str(root)))

        assert result == [root / "file.py"]


class TestTraverseExclude:
    def test_exclude_patterns_filter_files(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "test_main.py": "",
            }
        )

        result = list(traverse(root, pattern="*.py", exclude=["test_*"]))

        assert result == [root / "main.py"]

    def test_exclude_patterns_prune_directories(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "src": {
                    "main.py": "",
                },
                "__pycache__": {
                    "cache.pyc": "",
                },
            }
        )

        result = list(traverse(root, exclude=["__pycache__"]))

        # __pycache__ should be pruned, so cache.pyc should not appear
        assert root / "src" / "main.py" in result
        assert root / "__pycache__" / "cache.pyc" not in result

    def test_exclude_nested_directory(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "src": {
                    "main.py": "",
                    "tests": {
                        "test.py": "",
                    },
                },
            }
        )

        result = list(traverse(root, exclude=["**/tests"]))

        assert root / "src" / "main.py" in result
        assert root / "src" / "tests" / "test.py" not in result

    def test_multiple_exclude_patterns(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "test_main.py": "",
                "main_test.py": "",
            }
        )

        result = list(traverse(root, exclude=["test_*", "*_test.py"]))

        assert result == [root / "main.py"]


class TestTraverseInclude:
    def test_include_patterns_filter_files(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "readme.txt": "",
            }
        )

        result = list(traverse(root, include=["*.py"]))

        assert result == [root / "main.py"]

    def test_multiple_include_patterns_or_logic(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "readme.txt": "",
                "config.json": "",
            }
        )

        result = sorted(traverse(root, include=["*.py", "*.txt"]))

        assert result == sorted([root / "main.py", root / "readme.txt"])

    def test_include_with_pattern_combined(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "src": {
                    "main.py": "",
                    "test.py": "",
                },
                "root.py": "",
                "test_root.py": "",
            }
        )

        # pattern=src/*.py combines with include as OR logic
        result = list(traverse(root, pattern="src/*.py", include=["test_*"]))

        # Should match: src/*.py OR test_*
        # src/main.py matches src/*.py -> YES
        # src/test.py matches src/*.py -> YES
        # root.py matches neither -> NO
        # test_root.py matches test_* -> YES
        expected = sorted(
            [
                root / "src" / "main.py",
                root / "src" / "test.py",
                root / "test_root.py",
            ]
        )
        assert sorted(result) == expected


class TestTraverseSymlinks:
    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    @pytest.mark.parametrize(
        ("follow_symlinks", "expect_link_content"),
        [
            pytest.param(True, True, id="follow-symlinks-true-follows-symlinks"),
            pytest.param(False, False, id="follow-symlinks-false-does-not-follow"),
        ],
    )
    def test_follow_symlinks_behavior(
        self,
        tmp_tree: "TreeFactory",
        *,
        follow_symlinks: bool,
        expect_link_content: bool,
    ):
        root = tmp_tree(
            {
                "real_dir": {
                    "file.py": "",
                },
                "symlink": Symlink("real_dir"),
            }
        )

        result = sorted(traverse(root, follow_symlinks=follow_symlinks))

        assert root / "real_dir" / "file.py" in result
        if expect_link_content:
            assert root / "symlink" / "file.py" in result
        else:
            assert root / "symlink" / "file.py" not in result

    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    def test_symlink_to_file(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "real_file.py": "",
                "symlink.py": Symlink("real_file.py"),
            }
        )

        result = sorted(traverse(root, pattern="*.py"))

        # Both should appear as files
        assert result == sorted([root / "real_file.py", root / "symlink.py"])

    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    def test_broken_symlink_skipped_gracefully(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file.txt": "",
                "broken_link": Symlink("nonexistent_file"),
            }
        )

        result = list(traverse(root))

        assert root / "file.txt" in result
        # broken_link should be skipped or handled gracefully, not raise


@pytest.mark.skipif(os.name == "nt", reason="Permission model differs on Windows")
class TestTraversePermissions:
    def test_permission_denied_directory_skipped(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "restricted": {
                    "secret.txt": "",
                },
                "accessible.txt": "",
            }
        )

        restricted = root / "restricted"
        restricted.chmod(0o000)
        try:
            result = list(traverse(root))
            # Should include accessible file, skip restricted dir silently
            assert root / "accessible.txt" in result
            assert restricted / "secret.txt" not in result
        finally:
            restricted.chmod(0o755)  # Cleanup for test teardown


class TestTraverseWithMatcher:
    def test_custom_matcher(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file.py": "",
                "file.txt": "",
            }
        )

        matcher = GlobMatcher()
        result = list(traverse(root, pattern="*.py", matcher=matcher))

        assert result == [root / "file.py"]

    def test_default_matcher_is_glob(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "file.py": "",
            }
        )

        # Without explicit matcher, should use GlobMatcher
        result = list(traverse(root, pattern="*.py"))

        assert result == [root / "file.py"]
