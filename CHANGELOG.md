# Changelog

This file documents all notable changes to this project.

This format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [PEP 440](https://peps.python.org/pep-0440/).

## [Unreleased]

## [0.1.0] - 2026-01-12

Initial release.

### Added

- `SearchPath` class for ordered directory searching with scope names for provenance tracking
- Module-level functions `first()`, `all()`, `match()`, and `matches()` for one-liner searches
- `Match` dataclass with path, scope, source, and relative path properties
- Pattern matching with glob patterns (default), regex patterns, and gitignore-style patterns
- Include/exclude filtering with `include`, `exclude`, and their `_from` variants
- Hierarchical pattern files via `include_from_ancestors` and `exclude_from_ancestors`
- `GlobMatcher`, `RegexMatcher`, and `GitignoreMatcher` pattern matchers
- `SearchPath.with_suffix()` for appending path components
- `SearchPath.filter()` and `SearchPath.existing()` for filtering entries
- `SearchPath` concatenation with `+` operator
- Exception hierarchy: `SearchPathError`, `PatternError`, `PatternSyntaxError`, `PatternFileError`, `ConfigurationError`
- Optional `pathspec` dependency for full gitignore compatibility
- Python 3.10+ support

[Unreleased]: https://github.com/tbhb/searchpath/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/tbhb/searchpath/releases/tag/v0.1.0
