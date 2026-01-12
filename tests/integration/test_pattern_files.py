from typing import TYPE_CHECKING

import pytest

from searchpath._traversal import load_patterns, traverse

if TYPE_CHECKING:
    from conftest import TreeFactory


class TestPatternFileLoading:
    def test_load_patterns_from_real_file(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"patterns.txt": "*.py\n*.txt\n"})

        patterns = load_patterns(root / "patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_load_patterns_preserves_order(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"patterns.txt": "first\nsecond\nthird\n"})

        patterns = load_patterns(root / "patterns.txt")

        assert patterns == ["first", "second", "third"]

    def test_comment_and_empty_line_handling(self, tmp_tree: "TreeFactory"):
        content = (
            "# This is a header comment\n"
            "*.py\n"
            "\n"
            "# Another comment\n"
            "  \n"
            "*.txt\n"
            "# Trailing comment\n"
        )
        root = tmp_tree({"patterns.txt": content})

        patterns = load_patterns(root / "patterns.txt")

        assert patterns == ["*.py", "*.txt"]

    def test_integration_with_traverse_using_loaded_patterns(
        self, tmp_tree: "TreeFactory"
    ):
        root = tmp_tree(
            {
                "main.py": "",
                "test.py": "",
                "readme.txt": "",
                "config.json": "",
                ".include": "*.py\n*.txt\n",
            }
        )

        include_patterns = load_patterns(root / ".include")
        result = sorted(traverse(root, include=include_patterns))

        expected = sorted(
            [
                root / "main.py",
                root / "test.py",
                root / "readme.txt",
            ]
        )
        # Filter out .include file which is not matched
        result_filtered = [p for p in result if p.name != ".include"]
        assert result_filtered == expected

    def test_integration_with_traverse_exclude_patterns(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "test_main.py": "",
                "conftest.py": "",
                ".exclude": "test_*\nconftest.py\n",
            }
        )

        exclude_patterns = load_patterns(root / ".exclude")
        result = list(traverse(root, pattern="*.py", exclude=exclude_patterns))

        assert result == [root / "main.py"]

    @pytest.mark.parametrize(
        ("pattern_content", "expected_patterns"),
        [
            pytest.param(
                "*.py\n**/*.test.js\n[0-9]*.log\n",
                ["*.py", "**/*.test.js", "[0-9]*.log"],
                id="special-characters",
            ),
            pytest.param(
                "  *.py  \n\t*.txt\t\n  **/*.md  ",
                ["*.py", "*.txt", "**/*.md"],
                id="leading-and-trailing-whitespace",
            ),
        ],
    )
    def test_patterns_with_special_cases(
        self,
        tmp_tree: "TreeFactory",
        pattern_content: str,
        expected_patterns: list[str],
    ):
        root = tmp_tree({"patterns.txt": pattern_content})

        patterns = load_patterns(root / "patterns.txt")

        assert patterns == expected_patterns

    def test_gitignore_style_patterns(self, tmp_tree: "TreeFactory"):
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
        root = tmp_tree({".gitignore": content})

        patterns = load_patterns(root / ".gitignore")

        assert patterns == ["*.pyc", "__pycache__/", "dist/", ".vscode/", "*.swp"]
