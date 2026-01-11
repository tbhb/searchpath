import os
from typing import TYPE_CHECKING

import pytest

from searchpath import GlobMatcher
from searchpath._traversal import traverse

if TYPE_CHECKING:
    from pathlib import Path


class TestTraverseBasic:
    def test_basic_file_discovery(self, tmp_path: "Path"):
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "file.txt").touch()

        result = sorted(traverse(tmp_path))

        assert result == sorted(
            [
                tmp_path / "file1.py",
                tmp_path / "file2.py",
                tmp_path / "file.txt",
            ]
        )

    def test_directory_discovery_kind_dirs(self, tmp_path: "Path"):
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()
        (tmp_path / "file.txt").touch()

        result = sorted(traverse(tmp_path, kind="dirs"))

        assert result == sorted([tmp_path / "dir1", tmp_path / "dir2"])

    def test_both_discovery_kind_both(self, tmp_path: "Path"):
        (tmp_path / "dir1").mkdir()
        (tmp_path / "file.txt").touch()

        result = sorted(traverse(tmp_path, kind="both"))

        assert result == sorted([tmp_path / "dir1", tmp_path / "file.txt"])

    def test_pattern_matching_star(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "file.txt").touch()

        result = list(traverse(tmp_path, pattern="*.py"))

        assert result == [tmp_path / "file.py"]

    def test_pattern_matching_recursive(self, tmp_path: "Path"):
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").touch()
        (tmp_path / "test.py").touch()
        (tmp_path / "readme.txt").touch()

        result = sorted(traverse(tmp_path, pattern="**/*.py"))

        assert result == sorted([src / "main.py", tmp_path / "test.py"])

    def test_pattern_matching_specific_dir(self, tmp_path: "Path"):
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        src.mkdir()
        tests.mkdir()
        (src / "main.py").touch()
        (tests / "test.py").touch()

        result = list(traverse(tmp_path, pattern="src/*.py"))

        assert result == [src / "main.py"]

    def test_nonexistent_root_yields_nothing(self, tmp_path: "Path"):
        nonexistent = tmp_path / "nonexistent"

        result = list(traverse(nonexistent))

        assert result == []

    def test_file_as_root_yields_nothing(self, tmp_path: "Path"):
        file_path = tmp_path / "file.txt"
        file_path.touch()

        result = list(traverse(file_path))

        assert result == []

    def test_empty_directory_yields_nothing(self, tmp_path: "Path"):
        result = list(traverse(tmp_path))

        assert result == []

    def test_nested_directories(self, tmp_path: "Path"):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "file.py").touch()

        result = list(traverse(tmp_path, pattern="**/*.py"))

        assert result == [deep / "file.py"]

    def test_accepts_string_path(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()

        result = list(traverse(str(tmp_path)))

        assert result == [tmp_path / "file.py"]


class TestTraverseExclude:
    def test_exclude_patterns_filter_files(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()

        result = list(traverse(tmp_path, pattern="*.py", exclude=["test_*"]))

        assert result == [tmp_path / "main.py"]

    def test_exclude_patterns_prune_directories(self, tmp_path: "Path"):
        # Create structure: src/main.py, __pycache__/cache.pyc
        src = tmp_path / "src"
        cache = tmp_path / "__pycache__"
        src.mkdir()
        cache.mkdir()
        (src / "main.py").touch()
        (cache / "cache.pyc").touch()

        result = list(traverse(tmp_path, exclude=["__pycache__"]))

        # __pycache__ should be pruned, so cache.pyc should not appear
        assert tmp_path / "src" / "main.py" in result
        assert tmp_path / "__pycache__" / "cache.pyc" not in result

    def test_exclude_nested_directory(self, tmp_path: "Path"):
        # Create: src/main.py, src/tests/test.py
        src = tmp_path / "src"
        tests = src / "tests"
        src.mkdir()
        tests.mkdir()
        (src / "main.py").touch()
        (tests / "test.py").touch()

        result = list(traverse(tmp_path, exclude=["**/tests"]))

        assert tmp_path / "src" / "main.py" in result
        assert tmp_path / "src" / "tests" / "test.py" not in result

    def test_multiple_exclude_patterns(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "main_test.py").touch()

        result = list(traverse(tmp_path, exclude=["test_*", "*_test.py"]))

        assert result == [tmp_path / "main.py"]


class TestTraverseInclude:
    def test_include_patterns_filter_files(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()

        result = list(traverse(tmp_path, include=["*.py"]))

        assert result == [tmp_path / "main.py"]

    def test_multiple_include_patterns_or_logic(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        result = sorted(traverse(tmp_path, include=["*.py", "*.txt"]))

        assert result == sorted([tmp_path / "main.py", tmp_path / "readme.txt"])

    def test_include_with_pattern_combined(self, tmp_path: "Path"):
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").touch()
        (src / "test.py").touch()
        (tmp_path / "root.py").touch()
        (tmp_path / "test_root.py").touch()

        # pattern=src/*.py combines with include as OR logic
        result = list(traverse(tmp_path, pattern="src/*.py", include=["test_*"]))

        # Should match: src/*.py OR test_*
        # src/main.py matches src/*.py -> YES
        # src/test.py matches src/*.py -> YES
        # root.py matches neither -> NO
        # test_root.py matches test_* -> YES
        expected = sorted([src / "main.py", src / "test.py", tmp_path / "test_root.py"])
        assert sorted(result) == expected


class TestTraverseSymlinks:
    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    def test_follow_symlinks_true_follows_symlinks(self, tmp_path: "Path"):
        # Create: real_dir/file.py and symlink -> real_dir
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        (real_dir / "file.py").touch()
        symlink = tmp_path / "symlink"
        symlink.symlink_to(real_dir)

        result = sorted(traverse(tmp_path, follow_symlinks=True))

        # Should find file.py in both real_dir and through symlink
        assert tmp_path / "real_dir" / "file.py" in result
        assert tmp_path / "symlink" / "file.py" in result

    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    def test_follow_symlinks_false_does_not_follow(self, tmp_path: "Path"):
        # Create: real_dir/file.py and symlink -> real_dir
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()
        (real_dir / "file.py").touch()
        symlink = tmp_path / "symlink"
        symlink.symlink_to(real_dir)

        result = list(traverse(tmp_path, follow_symlinks=False))

        # Should only find file.py in real_dir, not through symlink
        assert tmp_path / "real_dir" / "file.py" in result
        assert tmp_path / "symlink" / "file.py" not in result

    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    def test_symlink_to_file(self, tmp_path: "Path"):
        # Create: real_file.py and symlink.py -> real_file.py
        real_file = tmp_path / "real_file.py"
        real_file.touch()
        symlink = tmp_path / "symlink.py"
        symlink.symlink_to(real_file)

        result = sorted(traverse(tmp_path, pattern="*.py"))

        # Both should appear as files
        assert result == sorted([real_file, symlink])

    @pytest.mark.skipif(
        os.name == "nt", reason="Symlinks not always available on Windows"
    )
    def test_broken_symlink_skipped_gracefully(self, tmp_path: "Path"):
        (tmp_path / "file.txt").touch()
        broken_link = tmp_path / "broken_link"
        broken_link.symlink_to(tmp_path / "nonexistent_file")

        result = list(traverse(tmp_path))

        assert tmp_path / "file.txt" in result
        # broken_link should be skipped or handled gracefully, not raise


@pytest.mark.skipif(os.name == "nt", reason="Permission model differs on Windows")
class TestTraversePermissions:
    def test_permission_denied_directory_skipped(self, tmp_path: "Path"):
        restricted = tmp_path / "restricted"
        restricted.mkdir()
        (restricted / "secret.txt").touch()
        (tmp_path / "accessible.txt").touch()

        restricted.chmod(0o000)
        try:
            result = list(traverse(tmp_path))
            # Should include accessible file, skip restricted dir silently
            assert tmp_path / "accessible.txt" in result
            assert restricted / "secret.txt" not in result
        finally:
            restricted.chmod(0o755)  # Cleanup for test teardown


class TestTraverseWithMatcher:
    def test_custom_matcher(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "file.txt").touch()

        matcher = GlobMatcher()
        result = list(traverse(tmp_path, pattern="*.py", matcher=matcher))

        assert result == [tmp_path / "file.py"]

    def test_default_matcher_is_glob(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()

        # Without explicit matcher, should use GlobMatcher
        result = list(traverse(tmp_path, pattern="*.py"))

        assert result == [tmp_path / "file.py"]
