from typing import TYPE_CHECKING

from searchpath._traversal import load_patterns, traverse

if TYPE_CHECKING:
    from pathlib import Path


class TestPatternFileLoading:
    def test_load_patterns_from_real_file(self, tmp_path: "Path"):
        pattern_file = tmp_path / "patterns.txt"
        _ = pattern_file.write_text("*.py\n*.txt\n", encoding="utf-8")

        patterns = load_patterns(pattern_file)

        assert patterns == ["*.py", "*.txt"]

    def test_load_patterns_preserves_order(self, tmp_path: "Path"):
        pattern_file = tmp_path / "patterns.txt"
        _ = pattern_file.write_text("first\nsecond\nthird\n", encoding="utf-8")

        patterns = load_patterns(pattern_file)

        assert patterns == ["first", "second", "third"]

    def test_comment_and_empty_line_handling(self, tmp_path: "Path"):
        pattern_file = tmp_path / "patterns.txt"
        content = (
            "# This is a header comment\n"
            "*.py\n"
            "\n"
            "# Another comment\n"
            "  \n"
            "*.txt\n"
            "# Trailing comment\n"
        )
        _ = pattern_file.write_text(content, encoding="utf-8")

        patterns = load_patterns(pattern_file)

        assert patterns == ["*.py", "*.txt"]

    def test_integration_with_traverse_using_loaded_patterns(self, tmp_path: "Path"):
        # Create files
        (tmp_path / "main.py").touch()
        (tmp_path / "test.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        # Create pattern file for includes
        include_file = tmp_path / ".include"
        _ = include_file.write_text("*.py\n*.txt\n", encoding="utf-8")

        include_patterns = load_patterns(include_file)
        result = sorted(traverse(tmp_path, include=include_patterns))

        expected = sorted(
            [
                tmp_path / "main.py",
                tmp_path / "test.py",
                tmp_path / "readme.txt",
            ]
        )
        # Filter out .include file which is not matched
        result_filtered = [p for p in result if p.name != ".include"]
        assert result_filtered == expected

    def test_integration_with_traverse_exclude_patterns(self, tmp_path: "Path"):
        # Create files
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "conftest.py").touch()

        # Create pattern file for excludes
        exclude_file = tmp_path / ".exclude"
        _ = exclude_file.write_text("test_*\nconftest.py\n", encoding="utf-8")

        exclude_patterns = load_patterns(exclude_file)
        result = list(traverse(tmp_path, pattern="*.py", exclude=exclude_patterns))

        assert result == [tmp_path / "main.py"]

    def test_patterns_with_special_characters(self, tmp_path: "Path"):
        pattern_file = tmp_path / "patterns.txt"
        _ = pattern_file.write_text(
            "*.py\n**/*.test.js\n[0-9]*.log\n", encoding="utf-8"
        )

        patterns = load_patterns(pattern_file)

        assert patterns == ["*.py", "**/*.test.js", "[0-9]*.log"]

    def test_patterns_with_leading_and_trailing_whitespace(self, tmp_path: "Path"):
        pattern_file = tmp_path / "patterns.txt"
        _ = pattern_file.write_text(
            "  *.py  \n\t*.txt\t\n  **/*.md  ", encoding="utf-8"
        )

        patterns = load_patterns(pattern_file)

        assert patterns == ["*.py", "*.txt", "**/*.md"]

    def test_gitignore_style_patterns(self, tmp_path: "Path"):
        # Test loading gitignore-style patterns
        pattern_file = tmp_path / ".gitignore"
        content = (
            "# Build artifacts\n"
            "*.pyc\n"
            "__pycache__/\n"
            "dist/\n"
            "\n"
            "# Editor files\n"
            ".vscode/\n"
            "*.swp\n"
        )
        _ = pattern_file.write_text(content, encoding="utf-8")

        patterns = load_patterns(pattern_file)

        assert patterns == ["*.pyc", "__pycache__/", "dist/", ".vscode/", "*.swp"]
