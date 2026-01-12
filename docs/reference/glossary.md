# Glossary

Definitions of key terms used throughout the searchpath documentation. Terms appear in alphabetical order. Each term links to its primary explanation page and relevant API reference.

Config cascade { #config-cascade }
:   A pattern where configuration files load from directories in priority order. Higher-priority directories (like project-level) override lower-priority ones (like user or system level). searchpath is designed for this use case.

    **Learn more:** [Config cascades guide](../guides/index.md)

Deduplication { #deduplication }
:   The process of removing duplicate matches based on their relative path. When `dedupe=True` (the default for `all()` and `matches()`), only the first occurrence of each relative path is kept, allowing higher-priority directories to override lower-priority ones.

    **API:** [`SearchPath.all()`][searchpath.SearchPath.all], [`SearchPath.matches()`][searchpath.SearchPath.matches]

Entry { #entry }
:   A specification for a directory to include in a SearchPath. Can be:
    - A tuple `(scope_name, path)` for explicit scope naming
    - A bare `Path` or `str` (auto-named as "dir0," "dir1," and so on)
    - `None` (silently ignored, useful for optional directories)

    **API:** [`Entry`][searchpath.Entry]

Exclude pattern { #exclude-pattern }
:   A pattern that rejects matching paths. After include patterns select candidates, exclude patterns filter them out. Common examples: `["*.pyc", "__pycache__"]`.

    **API:** [`SearchPath.first()`][searchpath.SearchPath.first] `exclude` parameter

GitignoreMatcher { #gitignore-matcher }
:   A pattern matcher using the pathspec library for full gitignore compatibility. Supports negation (`!pattern`), directory-only (`pattern/`), and anchored (`/pattern`) patterns. Requires the optional `pathspec` dependency.

    **API:** [`GitignoreMatcher`][searchpath.GitignoreMatcher]

Glob pattern { #glob-pattern }
:   A pattern using wildcard characters to match file paths. Common syntax: `*` (any characters except `/`), `**` (any characters including `/`), `?` (single character), `[abc]` (character class).

    **API:** [`GlobMatcher`][searchpath.GlobMatcher]

GlobMatcher { #glob-matcher }
:   The default pattern matcher using glob-style patterns. Supports `*`, `**`, `?`, and character classes. Does not support negation or directory-only patterns.

    **API:** [`GlobMatcher`][searchpath.GlobMatcher]

Include pattern { #include-pattern }
:   A pattern that paths must match to be included in results. When include patterns are specified, only matching paths are returned. When empty (the default), all paths are candidates.

    **API:** [`SearchPath.first()`][searchpath.SearchPath.first] `include` parameter

Match { #match }
:   A result object containing a matched path with provenance information. Includes the absolute `path`, the `scope` name, the `source` directory, and a `relative` property for the path relative to source.

    **API:** [`Match`][searchpath.Match]

PathMatcher { #path-matcher }
:   A protocol defining the interface for pattern matching implementations. Custom matchers can be created by implementing this protocol.

    **API:** [`PathMatcher`][searchpath.PathMatcher]

Provenance { #provenance }
:   Information about where a match came from. The `Match` object provides provenance through its `scope` (the name identifying the directory) and `source` (the actual directory path) attributes.

    **API:** [`Match`][searchpath.Match]

RegexMatcher { #regex-matcher }
:   A pattern matcher using Python regular expressions. Provides full regex syntax for complex matching needs. Patterns are matched against the entire path using `fullmatch()`.

    **API:** [`RegexMatcher`][searchpath.RegexMatcher]

Scope { #scope }
:   A string name identifying a directory in a SearchPath. Scopes provide semantic meaning to matches (for example, "project," "user," or "system") and are included in Match objects for provenance tracking.

    **API:** [`SearchPath`][searchpath.SearchPath], [`Match.scope`][searchpath.Match.scope]

SearchPath { #searchpath }
:   An ordered list of directories to search. Directories are searched in order, with earlier directories having higher priority. Each directory can have a scope name for provenance tracking.

    **API:** [`SearchPath`][searchpath.SearchPath]

Source { #source }
:   The directory that a match came from. Available as `Match.source`, this is the actual directory path from the SearchPath entry.

    **API:** [`Match.source`][searchpath.Match.source]
