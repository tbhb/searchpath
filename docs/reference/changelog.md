---
toc_depth: 1
---

# Changelog

## Unreleased

This section tracks features and changes in development. For the authoritative changelog, see [CHANGELOG.md](https://github.com/tbhb/searchpath/blob/main/CHANGELOG.md) in the repository.

### Added

#### Core features

- `SearchPath` class for ordered directory searching with scope names
- Module-level convenience functions: `first()`, `match()`, `all()`, `matches()`
- `Match` dataclass with provenance information (`path`, `scope`, `source`, `relative`)
- `Entry` type alias for flexible directory specification

#### Pattern matching

- `PathMatcher` protocol for pluggable pattern matching
- `GlobMatcher` with glob-style patterns (default)
- `RegexMatcher` with Python regular expressions
- `GitignoreMatcher` with full gitignore compatibility (requires pathspec)

#### Filtering

- Include/exclude patterns for filtering results
- `include_from`/`exclude_from` for loading patterns from files
- `include_from_ancestors`/`exclude_from_ancestors` for hierarchical pattern cascades

#### Options

- `kind` parameter for matching files, directories, or both
- `dedupe` parameter for deduplication by relative path
- `follow_symlinks` parameter for symlink handling

#### Exception hierarchy

- `SearchPathError` base exception
- `PatternError` for pattern-related errors
- `PatternSyntaxError` for invalid pattern syntax
- `PatternFileError` for pattern file read errors
- `ConfigurationError` for invalid configuration

### Python version support

- Python 3.10, 3.11, 3.12, 3.13, 3.14, and 3.14t (free-threaded)
