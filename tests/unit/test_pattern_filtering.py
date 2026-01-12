from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from searchpath import GlobMatcher, PatternFileError, PatternSyntaxError
from searchpath._traversal import load_patterns

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem

    from tests.conftest import TreeFactory


class TestLoadPatterns:
    def test_load_patterns_from_file(self, fake_tree: "TreeFactory"):
        root = fake_tree({"patterns.txt": "*.py\n*.txt\n"})
        patterns = load_patterns(root / "patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param("# comment\n*.py\n# another\n*.txt", id="skip-comments"),
            pytest.param("*.py\n\n\n*.txt\n", id="skip-empty-lines"),
            pytest.param("  *.py  \n\t*.txt\t\n", id="strip-whitespace"),
            pytest.param("*.py\n   \n\t\n*.txt", id="whitespace-only-lines-skipped"),
        ],
    )
    def test_load_patterns_filtering(self, fake_tree: "TreeFactory", content: str):
        root = fake_tree({"patterns.txt": content})
        patterns = load_patterns(root / "patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param("", id="empty-file"),
            pytest.param("# comment 1\n# comment 2\n", id="comments-only"),
        ],
    )
    def test_load_patterns_empty_result(self, fake_tree: "TreeFactory", content: str):
        root = fake_tree({"patterns.txt": content})
        patterns = load_patterns(root / "patterns.txt")

        assert patterns == []

    def test_accepts_string_path(self, fake_tree: "TreeFactory"):
        root = fake_tree({"patterns.txt": "*.py"})
        patterns = load_patterns(str(root / "patterns.txt"))

        assert patterns == ["*.py"]

    def test_missing_file_raises_pattern_file_error(self):
        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns(Path("/nonexistent.txt"))

        assert exc_info.value.path == Path("/nonexistent.txt")
        assert "file not found" in exc_info.value.message

    def test_permission_denied_raises_pattern_file_error(
        self, fake_tree: "TreeFactory", fs: "FakeFilesystem"
    ):
        # Uses raw fs fixture for chmod() which fake_tree doesn't support
        root = fake_tree({"patterns.txt": "*.py"})
        fs.chmod(str(root / "patterns.txt"), 0o000)

        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns(root / "patterns.txt")

        assert "permission denied" in exc_info.value.message

    def test_is_directory_raises_pattern_file_error(self, fake_tree: "TreeFactory"):
        root = fake_tree({"patterns": {}})

        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns(root / "patterns")

        assert "is a directory" in exc_info.value.message

    def test_invalid_encoding_raises_pattern_file_error(self, fs: "FakeFilesystem"):
        # Uses raw fs fixture for bytes content which fake_tree doesn't support
        _ = fs.create_file("/patterns.txt", contents=b"\xff\xfe")

        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns("/patterns.txt")

        assert "invalid encoding" in exc_info.value.message


class TestPatternFiltering:
    def test_include_empty_matches_all(self):
        matcher = GlobMatcher()

        assert matcher.matches("file.py", include=(), exclude=())
        assert matcher.matches("any/path/file.txt", include=(), exclude=())

    def test_include_filters_matching_paths(self):
        matcher = GlobMatcher()

        assert matcher.matches("file.py", include=["*.py"])
        assert not matcher.matches("file.txt", include=["*.py"])

    def test_exclude_filters_matching_paths(self):
        matcher = GlobMatcher()

        assert not matcher.matches("test_file.py", exclude=["test_*"])
        assert matcher.matches("main.py", exclude=["test_*"])

    def test_include_and_exclude_combined(self):
        matcher = GlobMatcher()

        # Match *.py but not test_*
        assert matcher.matches("main.py", include=["*.py"], exclude=["test_*"])
        assert not matcher.matches("test_main.py", include=["*.py"], exclude=["test_*"])
        assert not matcher.matches("main.txt", include=["*.py"], exclude=["test_*"])

    def test_multiple_include_patterns_or_logic(self):
        matcher = GlobMatcher()

        assert matcher.matches("file.py", include=["*.py", "*.txt"])
        assert matcher.matches("file.txt", include=["*.py", "*.txt"])
        assert not matcher.matches("file.md", include=["*.py", "*.txt"])

    def test_multiple_exclude_patterns_or_logic(self):
        matcher = GlobMatcher()

        assert not matcher.matches("test_file.py", exclude=["test_*", "*_test.py"])
        assert not matcher.matches("file_test.py", exclude=["test_*", "*_test.py"])
        assert matcher.matches("file.py", exclude=["test_*", "*_test.py"])

    def test_pattern_syntax_error_propagates(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError):
            _ = matcher.matches("file.py", include=["[unclosed"])

    def test_pattern_syntax_error_in_exclude_propagates(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError):
            _ = matcher.matches("file.py", exclude=["[unclosed"])

    def test_recursive_glob_matches_nested_paths(self):
        matcher = GlobMatcher()

        assert matcher.matches("src/main.py", include=["**/*.py"])
        assert matcher.matches("a/b/c/file.py", include=["**/*.py"])
        assert not matcher.matches("src/main.txt", include=["**/*.py"])

    def test_directory_pattern_matching(self):
        matcher = GlobMatcher()

        assert matcher.matches("src/test", include=["src/*"], is_dir=True)
        assert matcher.matches("src/test", include=["src/*"], is_dir=False)
