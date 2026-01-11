"""Match dataclass for search path results."""

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - needed at runtime for dataclass


@dataclass(frozen=True, slots=True)
class Match:
    """Result of a search path lookup.

    A Match represents a file or directory found during a search path lookup.
    It includes the absolute path to the match, the scope name identifying
    which search path entry it came from, and the source directory.

    Attributes:
        path: Absolute path to the matched file or directory.
        scope: Scope name of the search path entry (e.g., "user", "project").
        source: The search path directory this match came from.

    Example:
        >>> from pathlib import Path
        >>> match = Match(
        ...     path=Path("/home/user/.config/myapp/config.toml"),
        ...     scope="user",
        ...     source=Path("/home/user/.config/myapp"),
        ... )
        >>> match.relative
        PosixPath('config.toml')
    """

    path: Path
    """Absolute path to the matched file or directory."""

    scope: str
    """Scope name of the search path entry (e.g., "user", "project")."""

    source: Path
    """The search path directory this match came from."""

    @property
    def relative(self) -> Path:
        """Path relative to the source directory.

        Returns:
            The path of this match relative to its source directory.
        """
        return self.path.relative_to(self.source)
