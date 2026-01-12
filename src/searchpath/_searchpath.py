"""SearchPath class for ordered directory searching."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeAlias, final

from searchpath._ancestor_patterns import (
    AncestorPatterns,
    collect_ancestor_patterns,
    merge_patterns,
)
from searchpath._match import Match
from searchpath._matchers import GlobMatcher
from searchpath._traversal import TraversalKind, load_patterns, traverse

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override  # pyright: ignore[reportUnreachable]

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from typing_extensions import Self

    from searchpath._matchers import PathMatcher

Entry: TypeAlias = "tuple[str, Path | str | None] | Path | str | None"
"""Type alias for SearchPath entry arguments."""


@final
class SearchPath:
    """An ordered list of directories to search.

    SearchPath represents an ordered sequence of directories that can be
    searched for files. Each directory is associated with a scope name
    that identifies where matches came from (e.g., "user", "project").

    Entries can be specified as:
    - A tuple of (scope_name, path): Explicit scope naming
    - A bare Path or str: Auto-named as "dir0", "dir1", etc.
    - None: Silently ignored (useful for optional directories)

    Attributes:
        dirs: List of directories in the search path.
        scopes: List of scope names corresponding to each directory.

    Example:
        >>> from pathlib import Path
        >>> sp = SearchPath(
        ...     ("project", Path("/project/.config")),
        ...     ("user", Path.home() / ".config"),
        ... )
        >>> len(sp)
        2
        >>> list(sp)  # doctest: +SKIP
        [PosixPath('/project/.config'), PosixPath('/home/user/.config')]
    """

    __slots__ = ("_entries",)

    def __init__(
        self,
        *entries: tuple[str, Path | str | None] | Path | str | None,
    ) -> None:
        """Initialize a SearchPath with the given entries.

        Args:
            *entries: Directory entries to include in the search path.
                Each entry can be:
                - A tuple of (scope_name, path): Explicit scope naming
                - A bare Path or str: Auto-named as "dir0", "dir1", etc.
                - None: Silently ignored
        """
        bare_paths = [e for e in entries if e is not None and not isinstance(e, tuple)]
        auto_names = {id(p): f"dir{i}" for i, p in enumerate(bare_paths)}

        self._entries: list[tuple[str, Path]] = []
        for entry in entries:
            parsed = self._parse_entry(entry, auto_names)
            if parsed is not None:
                self._entries.append(parsed)

    def __add__(self, other: object) -> "Self":
        """Concatenate two search paths.

        Creates a new SearchPath containing all entries from this search
        path followed by all entries from the other search path.

        Args:
            other: Another SearchPath to concatenate.

        Returns:
            A new SearchPath with entries from both.

        Raises:
            TypeError: If other is not a SearchPath.

        Example:
            >>> sp1 = SearchPath(("a", Path("/a")))
            >>> sp2 = SearchPath(("b", Path("/b")))
            >>> combined = sp1 + sp2
            >>> list(combined.scopes)
            ['a', 'b']
        """
        if not isinstance(other, SearchPath):
            return NotImplemented  # type: ignore[return-value]
        new_entries = self._entries + other._entries
        return self._from_entries(new_entries)

    def __bool__(self) -> bool:
        """Return True if the search path has any directories."""
        return len(self._entries) > 0

    def __iter__(self) -> "Iterator[Path]":
        """Iterate over directories in the search path.

        Yields:
            Each directory Path in order.
        """
        for _, path in self._entries:
            yield path

    def __len__(self) -> int:
        """Return the number of directories in the search path."""
        return len(self._entries)

    @override
    def __repr__(self) -> str:
        """Return a detailed string representation.

        Returns:
            A string showing the SearchPath constructor call.
        """
        if not self._entries:
            return "SearchPath()"
        entries_repr = ", ".join(
            f"({scope!r}, {path!r})" for scope, path in self._entries
        )
        return f"SearchPath({entries_repr})"

    @override
    def __str__(self) -> str:
        """Return a human-readable string representation.

        Format suitable for error messages showing scope: path pairs.

        Returns:
            A string like "project: /project/.config, user: ~/.config"
        """
        if not self._entries:
            return "(empty)"
        return ", ".join(f"{scope}: {path}" for scope, path in self._entries)

    @classmethod
    def _from_entries(cls, entries: list[tuple[str, Path]]) -> "Self":
        """Create a SearchPath from a pre-built entry list.

        This is an internal constructor used by methods that need to
        create SearchPath instances without re-parsing entries.

        Args:
            entries: List of (scope, path) tuples.

        Returns:
            A new SearchPath instance.
        """
        instance = cls.__new__(cls)
        instance._entries = entries  # noqa: SLF001
        return instance

    @staticmethod
    def _parse_entry(
        entry: tuple[str, Path | str | None] | Path | str | None,
        auto_names: dict[int, str],
    ) -> tuple[str, Path] | None:
        """Parse a single entry into (scope, path) or None.

        Args:
            entry: The entry to parse.
            auto_names: Mapping from bare path id to auto-generated scope name.

        Returns:
            A tuple of (scope, path) or None if entry should be skipped.
        """
        if entry is None:
            return None

        if isinstance(entry, tuple):
            scope, path = entry
            if path is None:
                return None
            resolved_path = Path(path) if isinstance(path, str) else path
            return (scope, resolved_path)

        resolved_path = Path(entry) if isinstance(entry, str) else entry
        return (auto_names[id(entry)], resolved_path)

    @property
    def dirs(self) -> list[Path]:
        """List of directories in the search path.

        Returns:
            A list of directory Paths in order.
        """
        return [path for _, path in self._entries]

    @property
    def scopes(self) -> list[str]:
        """List of scope names in the search path.

        Returns:
            A list of scope name strings in order.
        """
        return [scope for scope, _ in self._entries]

    def with_suffix(self, *parts: str) -> "Self":
        """Create a new SearchPath with path components appended.

        Appends the given path components to each directory in this
        search path, creating a new SearchPath.

        Args:
            *parts: Path components to append to each directory.

        Returns:
            A new SearchPath with the path components appended.

        Example:
            >>> sp = SearchPath(("user", Path("/home/user")))
            >>> sp2 = sp.with_suffix(".config", "myapp")
            >>> list(sp2)
            [PosixPath('/home/user/.config/myapp')]
        """
        new_entries = [(scope, path.joinpath(*parts)) for scope, path in self._entries]
        return self._from_entries(new_entries)

    def filter(self, predicate: "Callable[[Path], bool]") -> "Self":
        """Create a new SearchPath with entries filtered by a predicate.

        Args:
            predicate: A function that takes a Path and returns True to
                keep the entry or False to exclude it.

        Returns:
            A new SearchPath containing only entries for which the
            predicate returned True.

        Example:
            >>> sp = SearchPath(("a", Path("/exists")), ("b", Path("/missing")))
            >>> filtered = sp.filter(lambda p: p.exists())  # doctest: +SKIP
        """
        new_entries = [
            (scope, path) for scope, path in self._entries if predicate(path)
        ]
        return self._from_entries(new_entries)

    def existing(self) -> "Self":
        """Create a new SearchPath with only existing directories.

        This is a shorthand for `filter(lambda p: p.exists())`.

        Returns:
            A new SearchPath containing only directories that exist.

        Example:
            >>> import tempfile
            >>> from pathlib import Path
            >>> with tempfile.TemporaryDirectory() as tmp:
            ...     sp = SearchPath(
            ...         ("exists", Path(tmp)),
            ...         ("missing", Path("/no/such/dir")),
            ...     )
            ...     existing_sp = sp.existing()
            ...     len(existing_sp)
            1
        """
        return self.filter(lambda p: p.exists())

    def items(self) -> "Iterator[tuple[str, Path]]":
        """Iterate over (scope, path) pairs in the search path.

        Yields:
            Tuples of (scope_name, directory_path) in order.

        Example:
            >>> sp = SearchPath(("user", Path("/user")), ("system", Path("/sys")))
            >>> list(sp.items())
            [('user', PosixPath('/user')), ('system', PosixPath('/sys'))]
        """
        yield from self._entries

    @staticmethod
    def _normalize_pattern_arg(
        patterns: "str | Sequence[str] | None",
    ) -> "Sequence[str]":
        """Normalize pattern argument to a sequence of strings.

        Args:
            patterns: A single pattern string, sequence of patterns, or None.

        Returns:
            A sequence of pattern strings (empty if None).
        """
        if patterns is None:
            return ()
        if isinstance(patterns, str):
            return (patterns,)
        return patterns

    @staticmethod
    def _normalize_path_arg(
        paths: "Path | str | Sequence[Path | str] | None",
    ) -> "Sequence[Path]":
        """Normalize path argument to a sequence of Paths.

        Args:
            paths: A single path, sequence of paths, or None.

        Returns:
            A sequence of Path objects (empty if None).
        """
        if paths is None:
            return ()
        if isinstance(paths, (str, Path)):
            return (Path(paths),)
        return tuple(Path(p) for p in paths)

    @staticmethod
    def _load_pattern_files(paths: "Sequence[Path]") -> list[str]:
        """Load patterns from multiple pattern files.

        Args:
            paths: Sequence of paths to pattern files.

        Returns:
            Combined list of patterns from all files.

        Raises:
            PatternFileError: If any file cannot be read.
        """
        patterns: list[str] = []
        for path in paths:
            patterns.extend(load_patterns(path))
        return patterns

    def _build_patterns(
        self,
        include: "str | Sequence[str] | None",
        include_from: "Path | str | Sequence[Path | str] | None",
        exclude: "str | Sequence[str] | None",
        exclude_from: "Path | str | Sequence[Path | str] | None",
    ) -> tuple[list[str], list[str]]:
        """Build effective include and exclude pattern lists from all sources.

        Args:
            include: Inline include patterns.
            include_from: Path(s) to load additional include patterns from.
            exclude: Inline exclude patterns.
            exclude_from: Path(s) to load additional exclude patterns from.

        Returns:
            Tuple of (include_patterns, exclude_patterns).

        Raises:
            PatternFileError: If any pattern file cannot be read.
        """
        include_patterns = list(self._normalize_pattern_arg(include))
        include_paths = self._normalize_path_arg(include_from)
        if include_paths:
            include_patterns.extend(self._load_pattern_files(include_paths))

        exclude_patterns = list(self._normalize_pattern_arg(exclude))
        exclude_paths = self._normalize_path_arg(exclude_from)
        if exclude_paths:
            exclude_patterns.extend(self._load_pattern_files(exclude_paths))

        return (include_patterns, exclude_patterns)

    @staticmethod
    def _dedupe_matches(matches: "Iterable[Match]") -> "Iterator[Match]":
        """Deduplicate matches by relative path, keeping first occurrence.

        Args:
            matches: Iterable of Match objects.

        Yields:
            Match objects with unique relative paths.
        """
        seen: set[str] = set()
        for match in matches:
            key = match.relative.as_posix()
            if key not in seen:
                seen.add(key)
                yield match

    def _should_include_with_ancestors(  # noqa: PLR0913
        self,
        path: Path,
        source_resolved: Path,
        ancestors: AncestorPatterns,
        include: "Sequence[str]",
        exclude: "Sequence[str]",
        matcher: "PathMatcher",
    ) -> bool:
        """Check if a path should be included when using ancestor patterns.

        Returns True if the path passes the merged ancestor + inline patterns.
        """
        rel_path = path.relative_to(source_resolved).as_posix()
        is_dir = path.is_dir()

        merged_include = merge_patterns(ancestors.include, include)
        merged_exclude = merge_patterns(ancestors.exclude, exclude)

        if not merged_include and not merged_exclude:
            return True

        return matcher.matches(
            rel_path, is_dir=is_dir, include=merged_include, exclude=merged_exclude
        )

    def _iter_matches(  # noqa: PLR0913
        self,
        pattern: str,
        *,
        kind: TraversalKind,
        include: "Sequence[str]",
        exclude: "Sequence[str]",
        include_from_ancestors: str | None,
        exclude_from_ancestors: str | None,
        matcher: "PathMatcher | None",
        follow_symlinks: bool,
    ) -> "Iterator[Match]":
        """Core iteration logic yielding Match objects for all matching paths.

        Args:
            pattern: Glob pattern for matching paths.
            kind: What to yield: "files", "dirs", or "both".
            include: Additional patterns paths must match.
            exclude: Patterns that reject paths.
            include_from_ancestors: Filename to load include patterns from
                ancestor directories.
            exclude_from_ancestors: Filename to load exclude patterns from
                ancestor directories.
            matcher: PathMatcher implementation.
            follow_symlinks: Whether to follow symbolic links.

        Yields:
            Match objects for all matching paths across all entries.
        """
        use_ancestors = (
            include_from_ancestors is not None or exclude_from_ancestors is not None
        )

        if not use_ancestors:
            yield from self._iter_matches_simple(
                pattern,
                kind,
                include,
                exclude,
                matcher,
                follow_symlinks=follow_symlinks,
            )
            return

        yield from self._iter_matches_with_ancestors(
            pattern,
            kind,
            include,
            exclude,
            include_from_ancestors,
            exclude_from_ancestors,
            matcher,
            follow_symlinks=follow_symlinks,
        )

    def _iter_matches_simple(  # noqa: PLR0913
        self,
        pattern: str,
        kind: TraversalKind,
        include: "Sequence[str]",
        exclude: "Sequence[str]",
        matcher: "PathMatcher | None",
        *,
        follow_symlinks: bool,
    ) -> "Iterator[Match]":
        """Iterate matches without ancestor pattern handling."""
        for scope, source in self._entries:
            for path in traverse(
                source,
                pattern=pattern,
                kind=kind,
                include=include,
                exclude=exclude,
                matcher=matcher,
                follow_symlinks=follow_symlinks,
            ):
                yield Match(path=path, scope=scope, source=source)

    def _iter_matches_with_ancestors(  # noqa: PLR0913
        self,
        pattern: str,
        kind: TraversalKind,
        include: "Sequence[str]",
        exclude: "Sequence[str]",
        include_from_ancestors: str | None,
        exclude_from_ancestors: str | None,
        matcher: "PathMatcher | None",
        *,
        follow_symlinks: bool,
    ) -> "Iterator[Match]":
        """Iterate matches with ancestor pattern handling."""
        ancestor_cache: dict[Path, list[str]] = {}
        resolved_matcher = matcher if matcher is not None else GlobMatcher()
        traverse_include = () if include_from_ancestors is not None else include

        for scope, source in self._entries:
            source_resolved = source.resolve()
            for path in traverse(
                source,
                pattern=pattern,
                kind=kind,
                include=traverse_include,
                exclude=exclude,
                matcher=matcher,
                follow_symlinks=follow_symlinks,
            ):
                ancestors = collect_ancestor_patterns(
                    file_path=path,
                    entry_root=source_resolved,
                    include_filename=include_from_ancestors,
                    exclude_filename=exclude_from_ancestors,
                    cache=ancestor_cache,
                )

                if self._should_include_with_ancestors(
                    path,
                    source_resolved,
                    ancestors,
                    include,
                    exclude,
                    resolved_matcher,
                ):
                    yield Match(path=path, scope=scope, source=source)

    def first(  # noqa: PLR0913
        self,
        pattern: str = "**",
        *,
        kind: Literal["files", "dirs", "both"] = "files",
        include: "str | Sequence[str] | None" = None,
        include_from: "Path | str | Sequence[Path | str] | None" = None,
        include_from_ancestors: str | None = None,
        exclude: "str | Sequence[str] | None" = None,
        exclude_from: "Path | str | Sequence[Path | str] | None" = None,
        exclude_from_ancestors: str | None = None,
        matcher: "PathMatcher | None" = None,
        follow_symlinks: bool = True,
    ) -> Path | None:
        """Find the first matching path in the search path.

        Searches directories in order and returns the first path that matches
        the pattern and filter criteria. Returns None if no match is found.

        Args:
            pattern: Glob pattern for matching paths. Defaults to "**" (all).
            kind: What to match: "files", "dirs", or "both".
            include: Additional patterns paths must match.
            include_from: Path(s) to files containing include patterns.
            include_from_ancestors: Filename to load include patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            exclude: Patterns that reject paths.
            exclude_from: Path(s) to files containing exclude patterns.
            exclude_from_ancestors: Filename to load exclude patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            matcher: PathMatcher implementation. Defaults to GlobMatcher.
            follow_symlinks: Whether to follow symbolic links.

        Returns:
            The first matching Path, or None if not found.

        Example:
            >>> import tempfile
            >>> from pathlib import Path
            >>> with tempfile.TemporaryDirectory() as tmp:
            ...     d = Path(tmp)
            ...     (d / "config.toml").touch()
            ...     sp = SearchPath(("dir", d))
            ...     result = sp.first("*.toml")
            ...     result is not None
            True
        """
        result = self.match(
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
        return result.path if result is not None else None

    def match(  # noqa: PLR0913
        self,
        pattern: str = "**",
        *,
        kind: Literal["files", "dirs", "both"] = "files",
        include: "str | Sequence[str] | None" = None,
        include_from: "Path | str | Sequence[Path | str] | None" = None,
        include_from_ancestors: str | None = None,
        exclude: "str | Sequence[str] | None" = None,
        exclude_from: "Path | str | Sequence[Path | str] | None" = None,
        exclude_from_ancestors: str | None = None,
        matcher: "PathMatcher | None" = None,
        follow_symlinks: bool = True,
    ) -> Match | None:
        """Find the first matching path with provenance information.

        Like first(), but returns a Match object containing the path along
        with the scope name and source directory. Returns None if no match.

        Args:
            pattern: Glob pattern for matching paths. Defaults to "**" (all).
            kind: What to match: "files", "dirs", or "both".
            include: Additional patterns paths must match.
            include_from: Path(s) to files containing include patterns.
            include_from_ancestors: Filename to load include patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            exclude: Patterns that reject paths.
            exclude_from: Path(s) to files containing exclude patterns.
            exclude_from_ancestors: Filename to load exclude patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            matcher: PathMatcher implementation. Defaults to GlobMatcher.
            follow_symlinks: Whether to follow symbolic links.

        Returns:
            The first Match object, or None if not found.

        Example:
            >>> import tempfile
            >>> from pathlib import Path
            >>> with tempfile.TemporaryDirectory() as tmp:
            ...     d = Path(tmp)
            ...     (d / "config.toml").touch()
            ...     sp = SearchPath(("project", d))
            ...     m = sp.match("*.toml")
            ...     m is not None and m.scope == "project"
            True
        """
        include_patterns, exclude_patterns = self._build_patterns(
            include, include_from, exclude, exclude_from
        )

        for m in self._iter_matches(
            pattern,
            kind=kind,
            include=include_patterns,
            exclude=exclude_patterns,
            include_from_ancestors=include_from_ancestors,
            exclude_from_ancestors=exclude_from_ancestors,
            matcher=matcher,
            follow_symlinks=follow_symlinks,
        ):
            return m

        return None

    def all(  # noqa: PLR0913
        self,
        pattern: str = "**",
        *,
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
    ) -> list[Path]:
        """Find all matching paths in the search path.

        Searches all directories and returns paths matching the pattern and
        filter criteria. By default, deduplicates by relative path, keeping
        the first occurrence (from higher priority directories).

        Args:
            pattern: Glob pattern for matching paths. Defaults to "**" (all).
            kind: What to match: "files", "dirs", or "both".
            dedupe: If True, keep only first occurrence per relative path.
            include: Additional patterns paths must match.
            include_from: Path(s) to files containing include patterns.
            include_from_ancestors: Filename to load include patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            exclude: Patterns that reject paths.
            exclude_from: Path(s) to files containing exclude patterns.
            exclude_from_ancestors: Filename to load exclude patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            matcher: PathMatcher implementation. Defaults to GlobMatcher.
            follow_symlinks: Whether to follow symbolic links.

        Returns:
            List of matching Path objects.

        Example:
            >>> import tempfile
            >>> from pathlib import Path
            >>> with tempfile.TemporaryDirectory() as tmp:
            ...     d = Path(tmp)
            ...     (d / "a.py").touch()
            ...     (d / "b.py").touch()
            ...     sp = SearchPath(("dir", d))
            ...     len(sp.all("*.py")) >= 2
            True
        """
        match_list = self.matches(
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
        return [m.path for m in match_list]

    def matches(  # noqa: PLR0913
        self,
        pattern: str = "**",
        *,
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
    ) -> list[Match]:
        """Find all matching paths with provenance information.

        Like all(), but returns Match objects containing paths along with
        scope names and source directories.

        Args:
            pattern: Glob pattern for matching paths. Defaults to "**" (all).
            kind: What to match: "files", "dirs", or "both".
            dedupe: If True, keep only first occurrence per relative path.
            include: Additional patterns paths must match.
            include_from: Path(s) to files containing include patterns.
            include_from_ancestors: Filename to load include patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            exclude: Patterns that reject paths.
            exclude_from: Path(s) to files containing exclude patterns.
            exclude_from_ancestors: Filename to load exclude patterns from
                ancestor directories. Patterns are collected from the search
                entry root toward each file's parent directory.
            matcher: PathMatcher implementation. Defaults to GlobMatcher.
            follow_symlinks: Whether to follow symbolic links.

        Returns:
            List of Match objects.

        Example:
            >>> import tempfile
            >>> from pathlib import Path
            >>> with tempfile.TemporaryDirectory() as tmp:
            ...     d = Path(tmp)
            ...     (d / "config.toml").touch()
            ...     sp = SearchPath(("project", d))
            ...     matches = sp.matches("*.toml")
            ...     len(matches) >= 1 and matches[0].scope == "project"
            True
        """
        include_patterns, exclude_patterns = self._build_patterns(
            include, include_from, exclude, exclude_from
        )

        all_matches = self._iter_matches(
            pattern,
            kind=kind,
            include=include_patterns,
            exclude=exclude_patterns,
            include_from_ancestors=include_from_ancestors,
            exclude_from_ancestors=exclude_from_ancestors,
            matcher=matcher,
            follow_symlinks=follow_symlinks,
        )

        if dedupe:
            return list(self._dedupe_matches(all_matches))
        return list(all_matches)
