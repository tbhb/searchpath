# searchpath

[![CI](https://github.com/tbhb/searchpath/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tbhb/searchpath/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/searchpath.svg)](https://pypi.org/project/searchpath/)
[![codecov](https://codecov.io/gh/tbhb/searchpath/branch/main/graph/badge.svg)](https://codecov.io/gh/tbhb/searchpath)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

searchpath finds files across prioritized directories and tracks where each match comes from. Use it for config cascades (project overrides user overrides system), plugin discovery, or any scenario where files might exist in more than one location and you need to know which one you found.

!!! warning "Alpha software"

    This project is in early development. APIs may change without notice. Not yet recommended for production use.

## Installation

```bash
pip install searchpath
```

Requires Python 3.10 or later. See [Installation](install.md) for package manager options and optional dependencies.

## Quick example

```python
# demo
import searchpath
from pathlib import Path

# Find first config file, checking project dir before user dir
config = searchpath.first("config.toml", project_dir, user_dir)

# Find with provenance (which directory did it come from?)
match = searchpath.match("*.toml", ("project", project_dir), ("user", user_dir))
if match:
    print(f"Found {match.relative} in {match.scope} scope")
# Output: Found config.toml in project scope

# Find all Python files, excluding tests
files = searchpath.all("**/*.py", src_dir, exclude=["test_*", "*_test.py"])
```

The key insight: when you need to search several directories in priority order, you also need to know *which* directory each result came from. searchpath gives you both.

## Use cases

searchpath provides the foundation for any code that searches directories in priority order:

<div class="grid" markdown>

:material-cog:{ .lg .middle } __Config cascades__

Project-level config overrides user-level, which overrides system defaults. searchpath finds the first match and tells you which level it came from.

:material-puzzle:{ .lg .middle } __Plugin discovery__

Find plugins across app directories, user plugins, and shared plugins. Deduplicate by filename so user plugins can override built-ins.

:material-palette:{ .lg .middle } __Theme loading__

Search for templates in a custom theme directory first, falling back to the default theme. Know which theme provided each template.

:material-folder:{ .lg .middle } __Asset resolution__

Resolve assets from project directories before falling back to shared resources. Track provenance for caching and debugging.

:material-file-search:{ .lg .middle } __Build systems__

Discover source files across several roots with flexible include/exclude patterns. Filter by gitignore-style rules.

:material-code-tags:{ .lg .middle } __Developer tools__

Linters, formatters, and code generators that target specific file types. Find files matching patterns while respecting project ignore rules.

:material-layers:{ .lg .middle } __Multi-tenant systems__

Tenant-specific files override defaults. Track which tenant level each file comes from for auditing.

</div>

### When to use something else

searchpath is designed for ordered multi-directory searches with provenance tracking. For other use cases, consider:

| If you want to                     | Use instead                                                                                              |
|------------------------------------|----------------------------------------------------------------------------------------------------------|
| Search a single directory tree     | [`pathlib.Path.rglob()`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.rglob)              |
| Search file contents               | [ripgrep](https://github.com/BurntSushi/ripgrep), [grep](https://www.gnu.org/software/grep/)             |
| Watch for changes                  | [watchfiles](https://watchfiles.helpmanual.io/)                                                          |

searchpath shines when you need to search __directories in priority order__ and know which directory each result came from.

## Next steps

Ready to start using searchpath? Choose your path based on how you learn best.

<div class="grid cards" markdown>

-   :material-school:{ .lg .middle } __Tutorials__

    ---

    Learn searchpath step by step with hands-on lessons that teach the fundamentals.

    [:octicons-arrow-right-24: Get started](tutorials/index.md)

-   :material-directions:{ .lg .middle } __How-to guides__

    ---

    Follow practical recipes that show how to achieve specific goals with searchpath.

    [:octicons-arrow-right-24: Find a guide](guides/index.md)

-   :material-book-open-variant:{ .lg .middle } __Reference__

    ---

    Look up technical details about the API, including classes, functions, and configuration.

    [:octicons-arrow-right-24: Browse the API](reference/index.md)

-   :material-lightbulb-on:{ .lg .middle } __Explanation__

    ---

    Understand the concepts, architecture, and design decisions behind searchpath.

    [:octicons-arrow-right-24: Learn more](explanation/index.md)

</div>
