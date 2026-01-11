"""Pattern matchers for searchpath."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, final

from searchpath._exceptions import PatternSyntaxError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pathspec import GitIgnoreSpec


@final
@dataclass(frozen=True, slots=True)
class _CompiledPattern:
    """A compiled pattern ready for matching (internal).

    Attributes:
        regex: The compiled regular expression.
        pattern: The original pattern string.
    """

    regex: re.Pattern[str]
    pattern: str


class PathMatcher(Protocol):  # pragma: no cover
    """Protocol for pattern matching implementations.

    Path matchers check if paths match include/exclude pattern lists.
    Each matcher handles pattern compilation internally.

    Example:
        ```python
        matcher = GlobMatcher()
        matcher.matches("src/main.py", include=["**/*.py"])  # True
        matcher.matches("src/main.py", exclude=["**/test_*"])  # True
        ```
    """

    @property
    def supports_negation(self) -> bool:
        """Whether this matcher supports negation patterns (e.g., !pattern)."""
        ...

    @property
    def supports_dir_only(self) -> bool:
        """Whether this matcher supports directory-only patterns (e.g., pattern/)."""
        ...

    def matches(
        self,
        path: str,
        *,
        is_dir: bool = False,
        include: "Sequence[str]" = (),
        exclude: "Sequence[str]" = (),
    ) -> bool:
        """Check if path matches the include/exclude patterns.

        A path matches if:
        - It matches at least one include pattern (or include is empty), AND
        - It does not match any exclude pattern

        Args:
            path: Relative path from search root (forward slashes).
            is_dir: Whether the path represents a directory.
            include: Patterns the path must match (empty = match all).
            exclude: Patterns that reject the path.

        Returns:
            True if the path should be included in results.
        """
        ...


@final
class GlobMatcher:
    """Path matcher using glob-style patterns.

    Patterns are translated to regular expressions internally. The **
    pattern is only treated as recursive when it appears as a complete
    path component (e.g., **/, foo/**/bar), matching gitignore semantics.

    Supports:
        - ``*``: Matches any characters except ``/``
        - ``**``: Matches any characters including ``/`` (when complete component)
        - ``?``: Matches any single character except ``/``
        - ``[abc]``: Matches any character in the set
        - ``[!abc]`` or ``[^abc]``: Matches any character not in the set
        - ``[a-z]``: Matches any character in the range

    Does not support:
        - Negation patterns (``!pattern``)
        - Directory-only patterns (``pattern/``)
        - Anchored patterns (``/pattern``)

    Example:
        ```python
        matcher = GlobMatcher()
        matcher.matches("src/main.py", include=["**/*.py"])  # True
        matcher.matches("test_main.py", exclude=["test_*"])  # False
        ```
    """

    __slots__ = ("_cache",)

    def __init__(self) -> None:
        """Initialize the matcher with an empty pattern cache."""
        self._cache: dict[str, _CompiledPattern] = {}

    @property
    def supports_negation(self) -> bool:
        """Whether this matcher supports negation patterns.

        Returns:
            Always False for GlobMatcher.
        """
        return False

    @property
    def supports_dir_only(self) -> bool:
        """Whether this matcher supports directory-only patterns.

        Returns:
            Always False for GlobMatcher.
        """
        return False

    def matches(
        self,
        path: str,
        *,
        is_dir: bool = False,
        include: "Sequence[str]" = (),
        exclude: "Sequence[str]" = (),
    ) -> bool:
        """Check if path matches the include/exclude patterns.

        A path matches if:
        - It matches at least one include pattern (or include is empty), AND
        - It does not match any exclude pattern

        Args:
            path: Relative path from search root (forward slashes).
            is_dir: Whether the path represents a directory (ignored by GlobMatcher).
            include: Patterns the path must match (empty = match all).
            exclude: Patterns that reject the path.

        Returns:
            True if the path should be included in results.

        Raises:
            PatternSyntaxError: If any pattern has invalid syntax.

        Example:
            ```python
            matcher = GlobMatcher()
            matcher.matches("main.py", include=["*.py"])  # True
            matcher.matches("main.py", exclude=["main.*"])  # False
            ```
        """
        del is_dir  # Unused by GlobMatcher (no dir_only support)

        # Check include patterns (empty = match all)
        if include:
            included = any(self._match_pattern(path, p) for p in include)
            if not included:
                return False

        # Check exclude patterns
        if exclude:
            excluded = any(self._match_pattern(path, p) for p in exclude)
            if excluded:
                return False

        return True

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Test if a path matches a single pattern.

        Args:
            path: Relative path from search root.
            pattern: Glob pattern to match against.

        Returns:
            True if the path matches the pattern.
        """
        compiled = self._compile(pattern)
        return compiled.regex.fullmatch(path) is not None

    def _compile(self, pattern: str) -> _CompiledPattern:
        """Compile a glob pattern (with caching).

        Args:
            pattern: The glob pattern string to compile.

        Returns:
            A compiled pattern ready for matching.

        Raises:
            PatternSyntaxError: If the pattern is empty or has unclosed brackets.
        """
        if pattern in self._cache:
            return self._cache[pattern]

        if not pattern:
            raise PatternSyntaxError(pattern, "empty pattern")

        regex_str = self._glob_to_regex(pattern)
        regex = re.compile(regex_str)

        compiled = _CompiledPattern(regex=regex, pattern=pattern)
        self._cache[pattern] = compiled
        return compiled

    def _glob_to_regex(self, pattern: str) -> str:
        """Translate a glob pattern to a regex string.

        Args:
            pattern: The glob pattern to translate.

        Returns:
            A regex string equivalent to the glob pattern.

        Raises:
            PatternSyntaxError: If the pattern has unclosed brackets.
        """
        result: list[str] = []
        i = 0
        n = len(pattern)

        while i < n:
            c = pattern[i]

            if c == "*":
                i = self._translate_star(pattern, i, n, result)
            elif c == "?":
                result.append("[^/]")
                i += 1
            elif c == "[":
                i = self._translate_bracket(pattern, i, n, result)
            else:
                self._translate_literal(c, result)
                i += 1

        return "".join(result)

    def _translate_star(self, pattern: str, i: int, n: int, result: list[str]) -> int:
        """Translate * or ** glob pattern to regex.

        Gitignore-style semantics: ** is only recursive when it's a complete
        path component (bounded by / or string start/end). Otherwise ** is
        treated as a single * (matches anything except /).
        """
        # Single star - matches anything except /
        if i + 1 >= n or pattern[i + 1] != "*":
            result.append("[^/]*")
            return i + 1

        # Double star - check if it's a complete path component
        return self._translate_double_star(pattern, i, n, result)

    def _translate_double_star(
        self, pattern: str, i: int, n: int, result: list[str]
    ) -> int:
        """Translate ** pattern, checking if it's a complete path component."""
        next_pos = i + 2
        at_start = i == 0
        at_end = next_pos >= n
        after_slash = i > 0 and pattern[i - 1] == "/"
        before_slash = next_pos < n and pattern[next_pos] == "/"

        is_component = (at_start or after_slash) and (at_end or before_slash)

        if not is_component:
            # ** not a complete component (e.g., a**b) - treat as single *
            result.append("[^/]*")
            return next_pos

        # ** as complete path component - recursive match
        if before_slash:
            # **/ - match zero or more path segments including trailing slash
            result.append("(?:.*/)?")
            return next_pos + 1
        # ** at end - match anything (zero or more of any char)
        result.append(".*")
        return next_pos

    def _translate_literal(self, c: str, result: list[str]) -> None:
        """Translate a literal character, escaping regex metacharacters."""
        if c in r"\.+^${}()|":
            result.append("\\")
        result.append(c)

    def _translate_bracket(
        self, pattern: str, i: int, n: int, result: list[str]
    ) -> int:
        """Translate a character class [...] to regex.

        Args:
            pattern: The full pattern string.
            i: Current position (pointing to '[').
            n: Length of pattern.
            result: List to append regex parts to.

        Returns:
            New position after the closing ']'.

        Raises:
            PatternSyntaxError: If the bracket is unclosed.
        """
        bracket_start = i
        i += 1

        if i >= n:
            raise PatternSyntaxError(
                pattern, "unclosed bracket", position=bracket_start
            )

        # Check for negation at start
        # Gitignore-style: negated classes should also exclude /
        if pattern[i] in "!^":
            result.append("[^/")
            i += 1
        else:
            result.append("[")

        if i >= n:
            raise PatternSyntaxError(
                pattern, "unclosed bracket", position=bracket_start
            )

        # Handle ] as first character in class (literal ])
        if pattern[i] == "]":
            result.append("]")
            i += 1

        # Collect characters until closing ]
        i = self._collect_bracket_contents(pattern, i, n, result)

        if i >= n:
            raise PatternSyntaxError(
                pattern, "unclosed bracket", position=bracket_start
            )

        result.append("]")
        return i + 1

    def _collect_bracket_contents(
        self, pattern: str, i: int, n: int, result: list[str]
    ) -> int:
        """Collect contents of a character class until closing ']'."""
        while i < n and pattern[i] != "]":
            char = pattern[i]
            if char == "\\":
                i = self._handle_bracket_escape(pattern, i, n, result)
            elif char == "-":
                result.append("-")
                i += 1
            else:
                self._handle_bracket_char(char, result)
                i += 1
        return i

    def _handle_bracket_escape(
        self, pattern: str, i: int, n: int, result: list[str]
    ) -> int:
        """Handle backslash escape inside bracket expression."""
        result.append("\\")
        i += 1
        if i < n:
            result.append(pattern[i])
            i += 1
        return i

    def _handle_bracket_char(self, char: str, result: list[str]) -> None:
        """Handle a regular character inside bracket expression."""
        if char in r"\^-]":
            result.append("\\")
        result.append(char)


@final
class RegexMatcher:
    r"""Path matcher using Python regular expressions.

    Uses the re module for full regex syntax. Patterns are matched against
    the entire path using fullmatch() for consistency with GlobMatcher.

    Supports:
        - Full Python regex syntax (re module)
        - Character classes, quantifiers, alternation, groups

    Does not support:
        - Negation patterns (``!pattern``)
        - Directory-only patterns (``pattern/``)

    Example:
        ```python
        matcher = RegexMatcher()
        matcher.matches("src/main.py", include=[r".*\.py"])  # True
        matcher.matches("test_main.py", exclude=[r"test_.*"])  # False
        ```
    """

    __slots__ = ("_cache",)

    def __init__(self) -> None:
        """Initialize the matcher with an empty pattern cache."""
        self._cache: dict[str, _CompiledPattern] = {}

    @property
    def supports_negation(self) -> bool:
        """Whether this matcher supports negation patterns.

        Returns:
            Always False for RegexMatcher.
        """
        return False

    @property
    def supports_dir_only(self) -> bool:
        """Whether this matcher supports directory-only patterns.

        Returns:
            Always False for RegexMatcher.
        """
        return False

    def matches(
        self,
        path: str,
        *,
        is_dir: bool = False,
        include: "Sequence[str]" = (),
        exclude: "Sequence[str]" = (),
    ) -> bool:
        """Check if path matches the include/exclude patterns.

        A path matches if:
        - It matches at least one include pattern (or include is empty), AND
        - It does not match any exclude pattern

        Args:
            path: Relative path from search root (forward slashes).
            is_dir: Whether the path represents a directory (ignored by RegexMatcher).
            include: Patterns the path must match (empty = match all).
            exclude: Patterns that reject the path.

        Returns:
            True if the path should be included in results.

        Raises:
            PatternSyntaxError: If any pattern has invalid regex syntax.
        """
        del is_dir  # Unused by RegexMatcher (no dir_only support)

        # Check include patterns (empty = match all)
        if include:
            included = any(self._match_pattern(path, p) for p in include)
            if not included:
                return False

        # Check exclude patterns
        if exclude:
            excluded = any(self._match_pattern(path, p) for p in exclude)
            if excluded:
                return False

        return True

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Test if a path matches a single pattern.

        Args:
            path: Relative path from search root.
            pattern: Regex pattern to match against.

        Returns:
            True if the path matches the pattern.
        """
        compiled = self._compile(pattern)
        return compiled.regex.fullmatch(path) is not None

    def _compile(self, pattern: str) -> _CompiledPattern:
        """Compile a regex pattern (with caching).

        Args:
            pattern: The regex pattern string to compile.

        Returns:
            A compiled pattern ready for matching.

        Raises:
            PatternSyntaxError: If the pattern is empty or has invalid syntax.
        """
        if pattern in self._cache:
            return self._cache[pattern]

        if not pattern:
            raise PatternSyntaxError(pattern, "empty pattern")

        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise PatternSyntaxError(pattern, str(e)) from e

        compiled = _CompiledPattern(regex=regex, pattern=pattern)
        self._cache[pattern] = compiled
        return compiled


@final
class GitignoreMatcher:
    """Path matcher using gitignore-style patterns via pathspec library.

    Provides full gitignore compatibility including:
        - ``*``: Matches any characters except ``/``
        - ``**``: Recursive directory matching
        - ``?``: Matches any single character except ``/``
        - ``[abc]``: Character classes
        - ``!pattern``: Negation (un-ignores previously matched paths)
        - ``pattern/``: Directory-only patterns
        - ``/pattern``: Anchored patterns (match from root only)

    Requires the optional ``pathspec`` package. Install with::

        pip install searchpath[gitignore]

    Example:
        ```python
        matcher = GitignoreMatcher()
        matcher.matches("src/main.py", include=["*.py"])  # True
        matcher.matches("test_main.py", exclude=["test_*"])  # False
        ```
    """

    __slots__ = ("_spec_cache",)

    def __init__(self) -> None:
        """Initialize the matcher, checking for pathspec availability."""
        try:
            import pathspec  # noqa: F401, PLC0415  # pyright: ignore[reportUnusedImport]
        except ImportError as e:  # pragma: no cover
            msg = (
                "GitignoreMatcher requires the 'pathspec' package. "
                "Install it with: pip install searchpath[gitignore]"
            )
            raise ImportError(msg) from e
        self._spec_cache: dict[tuple[str, ...], GitIgnoreSpec] = {}

    @property
    def supports_negation(self) -> bool:
        """Whether this matcher supports negation patterns.

        Returns:
            Always True for GitignoreMatcher.
        """
        return True

    @property
    def supports_dir_only(self) -> bool:
        """Whether this matcher supports directory-only patterns.

        Returns:
            Always True for GitignoreMatcher.
        """
        return True

    def matches(
        self,
        path: str,
        *,
        is_dir: bool = False,
        include: "Sequence[str]" = (),
        exclude: "Sequence[str]" = (),
    ) -> bool:
        """Check if path matches the include/exclude patterns.

        Uses gitignore semantics where patterns are evaluated in order and
        negation patterns (!pattern) can re-include previously excluded paths.

        Args:
            path: Relative path from search root (forward slashes).
            is_dir: Whether the path represents a directory.
            include: Patterns the path must match (empty = match all).
            exclude: Patterns that reject the path.

        Returns:
            True if the path should be included in results.

        Raises:
            PatternSyntaxError: If any pattern has invalid syntax.
        """
        del is_dir  # Unused by GitignoreMatcher currently

        # Check include patterns (empty = match all)
        if include and not self._matches_spec(path, include):
            return False

        # Check exclude patterns - return False if matches, True otherwise
        return not (exclude and self._matches_spec(path, exclude))

    def _matches_spec(self, path: str, patterns: "Sequence[str]") -> bool:
        """Check if path matches gitignore spec built from patterns.

        Args:
            path: Relative path from search root.
            patterns: Gitignore-style patterns.

        Returns:
            True if the path matches the pattern spec.

        Raises:
            PatternSyntaxError: If any pattern is empty or invalid.
        """
        self._validate_patterns(patterns)
        spec = self._build_spec(patterns)
        return spec.match_file(path)

    def _validate_patterns(self, patterns: "Sequence[str]") -> None:
        """Validate that all patterns are non-empty.

        Args:
            patterns: Patterns to validate.

        Raises:
            PatternSyntaxError: If any pattern is empty.
        """
        for p in patterns:
            if not p:
                raise PatternSyntaxError(p, "empty pattern")

    def _build_spec(self, patterns: "Sequence[str]") -> "GitIgnoreSpec":
        """Build a GitIgnoreSpec from patterns.

        Args:
            patterns: Gitignore-style patterns.

        Returns:
            Compiled GitIgnoreSpec.

        Raises:
            PatternSyntaxError: If patterns have invalid syntax.
        """
        cache_key = tuple(patterns)
        if cache_key in self._spec_cache:
            return self._spec_cache[cache_key]

        from pathspec import GitIgnoreSpec  # noqa: PLC0415

        try:
            spec = GitIgnoreSpec.from_lines(patterns)
        except Exception as e:
            raise PatternSyntaxError(str(patterns), str(e)) from e

        self._spec_cache[cache_key] = spec
        return spec
