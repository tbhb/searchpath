"""SearchPath class for ordered directory searching."""

from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, final

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing_extensions import Self

from typing_extensions import override

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
