# How-to guides

This section contains task-oriented guides that show how to achieve specific goals. Use these when you know what you want to do and need to find out how.

## By task

### Finding files

| Task                           | Guide                         |
|--------------------------------|-------------------------------|
| Find a single file             | Finding the first match       |
| Find all matching files        | Finding all matches           |
| Track where files came from    | Working with provenance       |

### Pattern matching

| Task                                | Guide                         |
|-------------------------------------|-------------------------------|
| Filter by file patterns             | Using include patterns        |
| Exclude unwanted files              | Using exclude patterns        |
| Load patterns from files            | Loading patterns from files   |
| Use regex or gitignore patterns     | Choosing a pattern matcher    |

### Directory management

| Task                                  | Guide                         |
|---------------------------------------|-------------------------------|
| Build a config cascade                | Config cascades               |
| Handle optional directories           | Optional directories          |
| Filter to existing directories        | Filtering directories         |
| Search subdirectories consistently    | Using with_suffix()           |

### Advanced usage

| Task                                 | Guide                         |
|--------------------------------------|-------------------------------|
| Control deduplication                | Deduplication strategies      |
| Use ancestor pattern files           | Hierarchical patterns         |
| Create custom matchers               | Custom pattern matchers       |

## Planned guides

Finding the first match
:   Find the first file matching a pattern across several directories using [`first()`][searchpath.first].

Finding all matches
:   Find all files matching a pattern with [`all()`][searchpath.all] and control deduplication behavior.

Working with provenance
:   Use [`Match`][searchpath.Match] objects to track which directory each file came from and why it matters.

Using include patterns
:   Filter results to only include files matching specific patterns.

Using exclude patterns
:   Remove unwanted files from results with exclude patterns like `["*.pyc", "__pycache__"]`.

Loading patterns from files
:   Load include and exclude patterns from files using `include_from` and `exclude_from`.

Choosing a pattern matcher
:   Compare [`GlobMatcher`][searchpath.GlobMatcher], [`RegexMatcher`][searchpath.RegexMatcher], and [`GitignoreMatcher`][searchpath.GitignoreMatcher].

Config cascades
:   Build configuration hierarchies where project overrides user overrides system.

Optional directories
:   Handle directories that may not exist using `None` entries and the `existing()` method.

Filtering directories
:   Use `filter()` and `existing()` to narrow a SearchPath to specific directories.

Using with_suffix()
:   Append path components to all directories in a SearchPath for consistent subdirectory access.

Deduplication strategies
:   Control how duplicate relative paths are handled with the `dedupe` parameter.

Hierarchical patterns
:   Load patterns from ancestor directories for gitignore-like behavior with `include_from_ancestors`.

Custom pattern matchers
:   Create a [`PathMatcher`][searchpath.PathMatcher] protocol implementation for custom matching logic.

## Related resources

- **New to searchpath?** Start with the [tutorials](../tutorials/index.md)
- **Want deeper understanding?** Read the [explanations](../explanation/index.md)
- **Looking up API details?** See the [API reference](../reference/api.md)
