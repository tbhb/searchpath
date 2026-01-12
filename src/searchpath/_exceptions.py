"""Exception hierarchy for searchpath."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class SearchPathError(Exception):
    """Base exception for all searchpath errors."""


class PatternError(SearchPathError):
    """Base exception for pattern-related errors."""


class PatternSyntaxError(PatternError):
    """Raised when a pattern has invalid syntax.

    Attributes:
        pattern: The pattern that failed to parse.
        message: Description of the syntax error.
        position: Character position where the error occurred, or None.
    """

    pattern: str
    message: str
    position: int | None

    def __init__(
        self,
        pattern: str,
        message: str,
        position: int | None = None,
    ) -> None:
        """Initialize a PatternSyntaxError.

        Args:
            pattern: The pattern that failed to parse.
            message: Description of the syntax error.
            position: Character position where the error occurred, or None.
        """
        self.pattern = pattern
        self.message = message
        self.position = position

        if position is not None:
            error_msg = f"Invalid pattern {pattern!r} at position {position}: {message}"
        else:
            error_msg = f"Invalid pattern {pattern!r}: {message}"

        super().__init__(error_msg)


class PatternFileError(PatternError):
    """Raised when a pattern file cannot be read or parsed.

    Attributes:
        path: Path to the pattern file.
        message: Description of the error.
        line_number: Line number where the error occurred, or None.
    """

    path: "Path"
    message: str
    line_number: int | None

    def __init__(
        self,
        path: "Path",
        message: str,
        line_number: int | None = None,
    ) -> None:
        """Initialize a PatternFileError.

        Args:
            path: Path to the pattern file.
            message: Description of the error.
            line_number: Line number where the error occurred, or None.
        """
        self.path = path
        self.message = message
        self.line_number = line_number

        if line_number is not None:
            error_msg = f"Error in pattern file {path}:{line_number}: {message}"
        else:
            error_msg = f"Error in pattern file {path}: {message}"

        super().__init__(error_msg)


class ConfigurationError(SearchPathError):
    """Raised when SearchPath configuration is invalid."""
