from pathlib import Path

import pytest

from searchpath import (
    PatternFileError,
    PatternSyntaxError,
)


class TestPatternSyntaxError:
    @pytest.mark.parametrize(
        ("pattern", "message", "position", "expected"),
        [
            pytest.param(
                "[invalid",
                "unclosed bracket",
                0,
                "Invalid pattern '[invalid' at position 0: unclosed bracket",
                id="with-position",
            ),
            pytest.param(
                "**[",
                "unexpected end of pattern",
                None,
                "Invalid pattern '**[': unexpected end of pattern",
                id="without-position",
            ),
        ],
    )
    def test_format(
        self, pattern: str, message: str, position: int | None, expected: str
    ):
        exc = PatternSyntaxError(
            pattern=pattern,
            message=message,
            position=position,
        )

        assert str(exc) == expected

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
    @pytest.mark.parametrize(
        ("path", "message", "line_number", "expected"),
        [
            pytest.param(
                Path("/config/.gitignore"),
                "invalid pattern",
                42,
                "Error in pattern file /config/.gitignore:42: invalid pattern",
                id="with-line-number",
            ),
            pytest.param(
                Path("/config/.gitignore"),
                "file not found",
                None,
                "Error in pattern file /config/.gitignore: file not found",
                id="without-line-number",
            ),
        ],
    )
    def test_format(
        self, path: Path, message: str, line_number: int | None, expected: str
    ):
        exc = PatternFileError(
            path=path,
            message=message,
            line_number=line_number,
        )

        assert str(exc) == expected

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
