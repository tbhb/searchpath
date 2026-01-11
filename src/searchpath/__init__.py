"""Filesystem path discovery and pattern matching."""

from importlib.metadata import version

from searchpath._exceptions import (
    ConfigurationError,
    PatternError,
    PatternFileError,
    PatternSyntaxError,
    SearchPathError,
)
from searchpath._functions import all, first, match, matches  # noqa: A004
from searchpath._match import Match
from searchpath._matchers import (
    GitignoreMatcher,
    GlobMatcher,
    PathMatcher,
    RegexMatcher,
)
from searchpath._searchpath import Entry, SearchPath

__version__ = version("searchpath")

__all__ = [
    "ConfigurationError",
    "Entry",
    "GitignoreMatcher",
    "GlobMatcher",
    "Match",
    "PathMatcher",
    "PatternError",
    "PatternFileError",
    "PatternSyntaxError",
    "RegexMatcher",
    "SearchPath",
    "SearchPathError",
    "__version__",
    "all",
    "first",
    "match",
    "matches",
]
