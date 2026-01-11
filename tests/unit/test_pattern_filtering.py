from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from searchpath import GlobMatcher, PatternFileError, PatternSyntaxError
from searchpath._traversal import load_patterns

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


class TestLoadPatterns:
    def test_load_patterns_from_file(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="*.py\n*.txt\n")
        patterns = load_patterns("/patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_skip_comments(self, fs: "FakeFilesystem"):
        _ = fs.create_file(
            "/patterns.txt", contents="# comment\n*.py\n# another\n*.txt"
        )
        patterns = load_patterns("/patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_skip_empty_lines(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="*.py\n\n\n*.txt\n")
        patterns = load_patterns("/patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_strip_whitespace(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="  *.py  \n\t*.txt\t\n")
        patterns = load_patterns("/patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_whitespace_only_lines_skipped(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="*.py\n   \n\t\n*.txt")
        patterns = load_patterns("/patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_empty_file_returns_empty_list(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="")
        patterns = load_patterns("/patterns.txt")

        assert patterns == []

    def test_comments_only_returns_empty_list(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="# comment 1\n# comment 2\n")
        patterns = load_patterns("/patterns.txt")

        assert patterns == []

    def test_accepts_string_path(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="*.py")
        patterns = load_patterns("/patterns.txt")

        assert patterns == ["*.py"]

    def test_missing_file_raises_pattern_file_error(self):
        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns(Path("/nonexistent.txt"))

        assert exc_info.value.path == Path("/nonexistent.txt")
        assert "file not found" in exc_info.value.message

    def test_permission_denied_raises_pattern_file_error(self, fs: "FakeFilesystem"):
        _ = fs.create_file("/patterns.txt", contents="*.py")
        fs.chmod("/patterns.txt", 0o000)

        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns("/patterns.txt")

        assert "permission denied" in exc_info.value.message

    def test_is_directory_raises_pattern_file_error(self, fs: "FakeFilesystem"):
        _ = fs.create_dir("/patterns")

        with pytest.raises(PatternFileError) as exc_info:
            _ = load_patterns("/patterns")

        assert "is a directory" in exc_info.value.message

    def test_invalid_encoding_raises_pattern_file_error(self, fs: "FakeFilesystem"):
        # Create a file with invalid UTF-8 bytes
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
