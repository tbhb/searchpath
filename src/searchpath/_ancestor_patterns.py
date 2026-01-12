"""Ancestor pattern loading for hierarchical pattern files."""

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - needed at runtime for function signatures
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class AncestorPatterns:
    """Patterns collected from ancestor directories.

    Attributes:
        include: Include patterns from ancestor directories.
        exclude: Exclude patterns from ancestor directories.
    """

    include: tuple[str, ...]
    exclude: tuple[str, ...]


def _load_patterns_lenient(
    path: Path,
    cache: dict[Path, list[str]] | None,
) -> list[str]:
    """Load patterns from a file with lenient error handling.

    Unlike load_patterns from _traversal, this function silently returns
    an empty list if the file doesn't exist or can't be read. This supports
    lenient discovery where missing pattern files are simply skipped.

    Args:
        path: Path to the pattern file.
        cache: Optional dict for caching loaded patterns by file path.

    Returns:
        List of patterns from the file, or empty list if file is missing
        or unreadable.
    """
    if cache is not None and path in cache:
        return cache[path]

    patterns: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)
    except (FileNotFoundError, PermissionError, IsADirectoryError, UnicodeDecodeError):
        pass

    if cache is not None:
        cache[path] = patterns

    return patterns


def _collect_ancestor_dirs(file_path: Path, entry_root: Path) -> list[Path]:
    """Collect ancestor directories from entry_root to file's parent.

    Args:
        file_path: The matched file's absolute path.
        entry_root: The search path entry directory (boundary).

    Returns:
        List of directories from entry_root toward file_path.parent,
        in root-to-leaf order. Returns empty list if file_path is not
        under entry_root.
    """
    try:
        relative = file_path.parent.relative_to(entry_root)
    except ValueError:
        return []

    ancestors: list[Path] = [entry_root]
    current = entry_root
    for part in relative.parts:
        current = current / part
        ancestors.append(current)

    return ancestors


def collect_ancestor_patterns(
    file_path: Path,
    entry_root: Path,
    include_filename: str | None,
    exclude_filename: str | None,
    cache: dict[Path, list[str]] | None = None,
) -> AncestorPatterns:
    """Collect patterns from ancestor directories.

    Walks from entry_root toward file_path's parent directory,
    loading pattern files from each ancestor. Patterns from child
    directories appear after parent patterns in the result, which means
    child patterns can override parent patterns (for matchers that support
    negation like GitignoreMatcher).

    Args:
        file_path: The matched file's absolute path.
        entry_root: The search path entry directory (boundary).
        include_filename: Filename to load include patterns from.
        exclude_filename: Filename to load exclude patterns from.
        cache: Optional dict for caching loaded patterns by file path.

    Returns:
        AncestorPatterns with combined include and exclude patterns.
        Patterns are in root-to-leaf order (parent patterns first,
        child patterns last).
    """
    if include_filename is None and exclude_filename is None:
        return AncestorPatterns(include=(), exclude=())

    ancestors = _collect_ancestor_dirs(file_path, entry_root)

    include_patterns: list[str] = []
    exclude_patterns: list[str] = []

    for ancestor_dir in ancestors:
        if include_filename is not None:
            pattern_file = ancestor_dir / include_filename
            include_patterns.extend(_load_patterns_lenient(pattern_file, cache))

        if exclude_filename is not None:
            pattern_file = ancestor_dir / exclude_filename
            exclude_patterns.extend(_load_patterns_lenient(pattern_file, cache))

    return AncestorPatterns(
        include=tuple(include_patterns),
        exclude=tuple(exclude_patterns),
    )


def merge_patterns(
    ancestor_patterns: "Sequence[str]",
    inline_patterns: "Sequence[str]",
) -> list[str]:
    """Merge ancestor patterns with inline patterns.

    Ancestor patterns are prepended to inline patterns, implementing
    the precedence: ancestors (most general) -> inline (most specific).
    Child directories can override parent patterns because they appear
    later in the merged list.

    Args:
        ancestor_patterns: Patterns from ancestor directories.
        inline_patterns: Inline patterns from the search call.

    Returns:
        Merged pattern list with ancestors first, inline patterns last.
    """
    return [*ancestor_patterns, *inline_patterns]
