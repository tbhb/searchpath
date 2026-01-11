"""Module-level convenience functions for one-shot searches."""

from typing import TYPE_CHECKING, Literal

from searchpath._searchpath import Entry, SearchPath

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from searchpath._match import Match
    from searchpath._matchers import PathMatcher


def first(  # noqa: PLR0913
    pattern: str = "**",
    *entries: Entry,
    kind: Literal["files", "dirs", "both"] = "files",
    include: "str | Sequence[str] | None" = None,
    include_from: "Path | str | Sequence[Path | str] | None" = None,
    include_from_ancestors: str | None = None,
    exclude: "str | Sequence[str] | None" = None,
    exclude_from: "Path | str | Sequence[Path | str] | None" = None,
    exclude_from_ancestors: str | None = None,
    matcher: "PathMatcher | None" = None,
    follow_symlinks: bool = True,
) -> "Path | None":
    """Find the first matching path across directories.

    Convenience wrapper for SearchPath(*entries).first(pattern, ...).

    Args:
        pattern: Glob pattern for matching paths. Defaults to "**" (all).
        *entries: Directory entries to search, in priority order.
        kind: What to match: "files", "dirs", or "both".
        include: Additional patterns paths must match.
        include_from: Path(s) to files containing include patterns.
        include_from_ancestors: Filename to load include patterns from ancestors.
        exclude: Patterns that reject paths.
        exclude_from: Path(s) to files containing exclude patterns.
        exclude_from_ancestors: Filename to load exclude patterns from ancestors.
        matcher: PathMatcher implementation. Defaults to GlobMatcher.
        follow_symlinks: Whether to follow symbolic links.

    Returns:
        The first matching Path, or None if not found.

    Example:
        ```python
        import tempfile
        from pathlib import Path
        import searchpath

        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp).resolve()
            (d / "config.toml").touch()
            config = searchpath.first("config.toml", d)
            config is not None  # True
        ```
    """
    return SearchPath(*entries).first(
        pattern,
        kind=kind,
        include=include,
        include_from=include_from,
        include_from_ancestors=include_from_ancestors,
        exclude=exclude,
        exclude_from=exclude_from,
        exclude_from_ancestors=exclude_from_ancestors,
        matcher=matcher,
        follow_symlinks=follow_symlinks,
    )


def match(  # noqa: PLR0913
    pattern: str = "**",
    *entries: Entry,
    kind: Literal["files", "dirs", "both"] = "files",
    include: "str | Sequence[str] | None" = None,
    include_from: "Path | str | Sequence[Path | str] | None" = None,
    include_from_ancestors: str | None = None,
    exclude: "str | Sequence[str] | None" = None,
    exclude_from: "Path | str | Sequence[Path | str] | None" = None,
    exclude_from_ancestors: str | None = None,
    matcher: "PathMatcher | None" = None,
    follow_symlinks: bool = True,
) -> "Match | None":
    """Find the first matching path with provenance information.

    Convenience wrapper for SearchPath(*entries).match(pattern, ...).

    Args:
        pattern: Glob pattern for matching paths. Defaults to "**" (all).
        *entries: Directory entries to search, in priority order.
        kind: What to match: "files", "dirs", or "both".
        include: Additional patterns paths must match.
        include_from: Path(s) to files containing include patterns.
        include_from_ancestors: Filename to load include patterns from ancestors.
        exclude: Patterns that reject paths.
        exclude_from: Path(s) to files containing exclude patterns.
        exclude_from_ancestors: Filename to load exclude patterns from ancestors.
        matcher: PathMatcher implementation. Defaults to GlobMatcher.
        follow_symlinks: Whether to follow symbolic links.

    Returns:
        The first Match object, or None if not found.

    Example:
        ```python
        import tempfile
        from pathlib import Path
        import searchpath

        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp).resolve()
            (d / "config.toml").touch()
            m = searchpath.match("*.toml", ("project", d))
            m.scope if m else None  # 'project'
        ```
    """
    return SearchPath(*entries).match(
        pattern,
        kind=kind,
        include=include,
        include_from=include_from,
        include_from_ancestors=include_from_ancestors,
        exclude=exclude,
        exclude_from=exclude_from,
        exclude_from_ancestors=exclude_from_ancestors,
        matcher=matcher,
        follow_symlinks=follow_symlinks,
    )


def all(  # noqa: A001, PLR0913
    pattern: str = "**",
    *entries: Entry,
    kind: Literal["files", "dirs", "both"] = "files",
    dedupe: bool = True,
    include: "str | Sequence[str] | None" = None,
    include_from: "Path | str | Sequence[Path | str] | None" = None,
    include_from_ancestors: str | None = None,
    exclude: "str | Sequence[str] | None" = None,
    exclude_from: "Path | str | Sequence[Path | str] | None" = None,
    exclude_from_ancestors: str | None = None,
    matcher: "PathMatcher | None" = None,
    follow_symlinks: bool = True,
) -> list["Path"]:
    """Find all matching paths across directories.

    Convenience wrapper for SearchPath(*entries).all(pattern, ...).

    Args:
        pattern: Glob pattern for matching paths. Defaults to "**" (all).
        *entries: Directory entries to search, in priority order.
        kind: What to match: "files", "dirs", or "both".
        dedupe: If True, keep only first occurrence per relative path.
        include: Additional patterns paths must match.
        include_from: Path(s) to files containing include patterns.
        include_from_ancestors: Filename to load include patterns from ancestors.
        exclude: Patterns that reject paths.
        exclude_from: Path(s) to files containing exclude patterns.
        exclude_from_ancestors: Filename to load exclude patterns from ancestors.
        matcher: PathMatcher implementation. Defaults to GlobMatcher.
        follow_symlinks: Whether to follow symbolic links.

    Returns:
        List of matching Path objects.

    Example:
        ```python
        import tempfile
        from pathlib import Path
        import searchpath

        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp).resolve()
            (d / "main.py").touch()
            (d / "test_main.py").touch()
            files = searchpath.all("*.py", d)
            len(files) >= 2  # True
        ```
    """
    return SearchPath(*entries).all(
        pattern,
        kind=kind,
        dedupe=dedupe,
        include=include,
        include_from=include_from,
        include_from_ancestors=include_from_ancestors,
        exclude=exclude,
        exclude_from=exclude_from,
        exclude_from_ancestors=exclude_from_ancestors,
        matcher=matcher,
        follow_symlinks=follow_symlinks,
    )


def matches(  # noqa: PLR0913
    pattern: str = "**",
    *entries: Entry,
    kind: Literal["files", "dirs", "both"] = "files",
    dedupe: bool = True,
    include: "str | Sequence[str] | None" = None,
    include_from: "Path | str | Sequence[Path | str] | None" = None,
    include_from_ancestors: str | None = None,
    exclude: "str | Sequence[str] | None" = None,
    exclude_from: "Path | str | Sequence[Path | str] | None" = None,
    exclude_from_ancestors: str | None = None,
    matcher: "PathMatcher | None" = None,
    follow_symlinks: bool = True,
) -> list["Match"]:
    """Find all matching paths with provenance information.

    Convenience wrapper for SearchPath(*entries).matches(pattern, ...).

    Args:
        pattern: Glob pattern for matching paths. Defaults to "**" (all).
        *entries: Directory entries to search, in priority order.
        kind: What to match: "files", "dirs", or "both".
        dedupe: If True, keep only first occurrence per relative path.
        include: Additional patterns paths must match.
        include_from: Path(s) to files containing include patterns.
        include_from_ancestors: Filename to load include patterns from ancestors.
        exclude: Patterns that reject paths.
        exclude_from: Path(s) to files containing exclude patterns.
        exclude_from_ancestors: Filename to load exclude patterns from ancestors.
        matcher: PathMatcher implementation. Defaults to GlobMatcher.
        follow_symlinks: Whether to follow symbolic links.

    Returns:
        List of Match objects.

    Example:
        ```python
        import tempfile
        from pathlib import Path
        import searchpath

        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp).resolve()
            (d / "config.toml").touch()
            results = searchpath.matches("*.toml", ("proj", d))
            len(results) >= 1 and results[0].scope == "proj"  # True
        ```
    """
    return SearchPath(*entries).matches(
        pattern,
        kind=kind,
        dedupe=dedupe,
        include=include,
        include_from=include_from,
        include_from_ancestors=include_from_ancestors,
        exclude=exclude,
        exclude_from=exclude_from,
        exclude_from_ancestors=exclude_from_ancestors,
        matcher=matcher,
        follow_symlinks=follow_symlinks,
    )
