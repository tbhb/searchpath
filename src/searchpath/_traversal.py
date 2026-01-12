"""Directory traversal with pattern filtering."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from searchpath._exceptions import PatternFileError
from searchpath._matchers import GlobMatcher

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from searchpath._matchers import PathMatcher

TraversalKind = Literal["files", "dirs", "both"]


def load_patterns(path: Path | str) -> list[str]:
    """Load patterns from a file, one pattern per line.

    Reads a pattern file with UTF-8 encoding. Lines starting with # are
    treated as comments and ignored. Empty lines and whitespace-only lines
    are also ignored. Whitespace is stripped from each pattern.

    Args:
        path: Path to the pattern file.

    Returns:
        List of patterns from the file.

    Raises:
        PatternFileError: If the file cannot be read (not found, permission
            denied, is a directory, or has invalid encoding).

    Example:
        >>> patterns = load_patterns("patterns.txt")
        >>> # File contents:
        >>> # # Comment line
        >>> # *.py
        >>> # *.txt
        >>> patterns
        ['*.py', '*.txt']
    """
    path = Path(path)

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise PatternFileError(path, "file not found") from e
    except PermissionError as e:
        raise PatternFileError(path, "permission denied") from e
    except IsADirectoryError as e:
        raise PatternFileError(path, "is a directory") from e
    except UnicodeDecodeError as e:
        raise PatternFileError(path, f"invalid encoding: {e}") from e

    patterns: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)

    return patterns


@dataclass(frozen=True, slots=True)
class _TraversalContext:
    """Internal context for directory traversal operations."""

    root_path: Path
    kind: TraversalKind
    include: "Sequence[str]"
    exclude: "Sequence[str]"
    matcher: "PathMatcher"


def traverse(  # noqa: PLR0913
    root: Path | str,
    *,
    pattern: str = "**",
    kind: TraversalKind = "files",
    include: "Sequence[str]" = (),
    exclude: "Sequence[str]" = (),
    matcher: "PathMatcher | None" = None,
    follow_symlinks: bool = True,
) -> "Iterator[Path]":
    """Traverse a directory tree yielding matching paths.

    Walks the directory tree rooted at `root`, yielding paths that match
    the pattern filters. The traversal is lenient: missing or inaccessible
    directories are silently skipped.

    Args:
        root: Root directory to traverse.
        pattern: Glob pattern for matching paths. Defaults to "**" (all files).
        kind: What to yield: "files", "dirs", or "both".
        include: Additional patterns paths must match (OR logic with pattern).
        exclude: Patterns that reject paths.
        matcher: PathMatcher implementation. Defaults to GlobMatcher().
        follow_symlinks: Whether to follow symbolic links during traversal.

    Yields:
        Absolute Path objects for matching files/directories.

    Example:
        >>> for path in traverse("/project", pattern="**/*.py", exclude=["test_*"]):
        ...     print(path)
        /project/src/main.py
        /project/src/utils.py
    """
    root_path = Path(root).resolve()

    # Lenient: non-existent or non-directory root yields nothing
    if not root_path.exists() or not root_path.is_dir():
        return

    resolved_matcher = matcher if matcher is not None else GlobMatcher()

    # Build effective include patterns
    # Pattern is added to include unless it's the default "**"
    effective_include = list(include) if pattern == "**" else [pattern, *include]

    ctx = _TraversalContext(
        root_path=root_path,
        kind=kind,
        include=effective_include,
        exclude=exclude,
        matcher=resolved_matcher,
    )

    yield from _walk_tree(ctx, follow_symlinks=follow_symlinks)


def _walk_tree(
    ctx: _TraversalContext,
    *,
    follow_symlinks: bool,
) -> "Iterator[Path]":
    """Internal walker that yields matching paths from directory tree."""
    for dirpath, dirnames, filenames in os.walk(
        ctx.root_path, followlinks=follow_symlinks, onerror=None
    ):
        current_dir = Path(dirpath)
        rel_posix = current_dir.relative_to(ctx.root_path).as_posix()
        # relative_to returns "." for the root directory, normalize to empty string
        current_rel = "" if rel_posix == "." else rel_posix

        # Early pruning: remove excluded directories before descending
        _prune_excluded_dirs(dirnames, current_rel, ctx)

        # Yield directories if requested
        if ctx.kind in ("dirs", "both"):
            yield from _yield_matching_entries(
                dirnames, current_dir, current_rel, ctx, is_dir=True
            )

        # Yield files if requested
        if ctx.kind in ("files", "both"):
            yield from _yield_matching_entries(
                filenames, current_dir, current_rel, ctx, is_dir=False
            )


def _prune_excluded_dirs(
    dirnames: list[str],
    current_rel: str,
    ctx: _TraversalContext,
) -> None:
    """Remove excluded directories from dirnames in-place to prevent descending."""
    if not ctx.exclude:
        return

    dirnames[:] = [
        dirname
        for dirname in dirnames
        if ctx.matcher.matches(
            f"{current_rel}/{dirname}" if current_rel else dirname,
            is_dir=True,
            include=(),
            exclude=ctx.exclude,
        )
    ]


def _yield_matching_entries(
    names: list[str],
    current_dir: Path,
    current_rel: str,
    ctx: _TraversalContext,
    *,
    is_dir: bool,
) -> "Iterator[Path]":
    """Yield entries that match the include/exclude patterns."""
    for name in names:
        rel_path = f"{current_rel}/{name}" if current_rel else name

        if ctx.matcher.matches(
            rel_path, is_dir=is_dir, include=ctx.include, exclude=ctx.exclude
        ):
            yield current_dir / name
