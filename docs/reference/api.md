<!-- vale off -->

# API reference

Complete reference for all public classes and functions in the searchpath library. This reference is auto-generated from source docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

## Contents

- [Module-level functions](#module-level-functions) - One-liner convenience functions
- [SearchPath class](#searchpath-class) - Core class for ordered directory searching
- [Match class](#match-class) - Result object with provenance information
- [Entry type](#entry-type) - Type alias for directory entries
- [Pattern matchers](#pattern-matchers) - Pluggable pattern matching implementations
- [Exceptions](#exceptions) - Error hierarchy

---

## Module-level functions

Convenience functions for one-shot searches without creating a SearchPath instance.

::: searchpath
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - first
        - match
        - all
        - matches

---

## SearchPath class

The core class representing an ordered list of directories to search.

::: searchpath.SearchPath
    options:
      show_root_heading: true
      heading_level: 3
      members_order: source

---

## Match class

Result object containing a matched path with provenance information.

::: searchpath.Match
    options:
      show_root_heading: true
      heading_level: 3

---

## Entry type

Type alias for SearchPath entry arguments.

::: searchpath.Entry
    options:
      show_root_heading: true
      heading_level: 3

---

## Pattern matchers

### PathMatcher protocol

Protocol defining the interface for pattern matching implementations.

::: searchpath.PathMatcher
    options:
      show_root_heading: true
      heading_level: 4

### GlobMatcher

Default pattern matcher using glob-style patterns.

::: searchpath.GlobMatcher
    options:
      show_root_heading: true
      heading_level: 4

### RegexMatcher

Pattern matcher using Python regular expressions.

::: searchpath.RegexMatcher
    options:
      show_root_heading: true
      heading_level: 4

### GitignoreMatcher

Pattern matcher using gitignore-style patterns via the pathspec library.

::: searchpath.GitignoreMatcher
    options:
      show_root_heading: true
      heading_level: 4

---

## Exceptions

### Base exception

::: searchpath.SearchPathError
    options:
      show_root_heading: true
      heading_level: 4

### Pattern exceptions

::: searchpath.PatternError
    options:
      show_root_heading: true
      heading_level: 4

::: searchpath.PatternSyntaxError
    options:
      show_root_heading: true
      heading_level: 4

::: searchpath.PatternFileError
    options:
      show_root_heading: true
      heading_level: 4

### Configuration exceptions

::: searchpath.ConfigurationError
    options:
      show_root_heading: true
      heading_level: 4

<!-- vale on -->
