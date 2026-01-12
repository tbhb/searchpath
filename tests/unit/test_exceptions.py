from pathlib import Path

from searchpath import (
    PatternFileError,
    PatternSyntaxError,
)


class TestPatternSyntaxError:
    def test_format_with_position(self):
        exc = PatternSyntaxError(
            pattern="[invalid",
            message="unclosed bracket",
            position=0,
        )

        assert str(exc) == "Invalid pattern '[invalid' at position 0: unclosed bracket"

    def test_format_without_position(self):
        exc = PatternSyntaxError(
            pattern="**[",
            message="unexpected end of pattern",
        )

        assert str(exc) == "Invalid pattern '**[': unexpected end of pattern"

    def test_attributes_accessible(self):
        position = 4
        exc = PatternSyntaxError(
            pattern="test*",
            message="test error",
            position=position,
        )

        assert exc.pattern == "test*"
        assert exc.message == "test error"
        assert exc.position == position


class TestPatternFileError:
    def test_format_with_line_number(self):
        exc = PatternFileError(
            path=Path("/config/.gitignore"),
            message="invalid pattern",
            line_number=42,
        )

        expected = "Error in pattern file /config/.gitignore:42: invalid pattern"
        assert str(exc) == expected

    def test_format_without_line_number(self):
        exc = PatternFileError(
            path=Path("/config/.gitignore"),
            message="file not found",
        )

        assert str(exc) == "Error in pattern file /config/.gitignore: file not found"

    def test_attributes_accessible(self):
        path = Path("/some/file")
        line_number = 10
        exc = PatternFileError(
            path=path,
            message="test error",
            line_number=line_number,
        )

        assert exc.path == path
        assert exc.message == "test error"
        assert exc.line_number == line_number
