# searchpath

<!-- vale off -->
[![PyPI](https://img.shields.io/pypi/v/searchpath)](https://pypi.org/project/searchpath/)
[![CI](https://github.com/tbhb/searchpath/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tbhb/searchpath/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/tbhb/searchpath/branch/main/graph/badge.svg)](https://codecov.io/gh/tbhb/searchpath)
[![CodSpeed Badge](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/tbhb/searchpath)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
<!-- vale on -->

searchpath finds files across prioritized directories and tracks where each match comes from. Use it for config cascades (project overrides user overrides system), plugin discovery, or any scenario where files might exist in more than one location and you need to know which one you found.

> [!NOTE]
> This package is under active development. The API may change before the 1.0 release.

## Features

- **Search across directories with priority**: Find files in config cascades, plugin directories, or any ordered set of paths
- **Track where matches come from**: Every match includes provenance, telling you exactly which directory contains the file
- **Filter with powerful patterns**: Use glob patterns (default), full regex, or gitignore-style rules with negation (using [pathspec][pathspec])
- **Load patterns from files**: Support hierarchical pattern files that cascade like `.gitignore`
- **Simple one-liners for common cases**: `searchpath.first("config.toml", project_dir, user_dir)`
- **Minimal footprint**: Only requires `typing-extensions` on Python < 3.12; `pathspec` optional for gitignore support
- **Safe for concurrent use**: Immutable objects with no global state

## Installation

**pip:**

```bash
pip install searchpath

# With gitignore-style pattern support via pathspec
pip install searchpath[gitignore]
```

**poetry:**

```bash
poetry add searchpath

# With gitignore-style pattern support via pathspec
poetry add searchpath[gitignore]
```

**uv:**

```bash
uv add searchpath

# With gitignore-style pattern support via pathspec
uv add searchpath[gitignore]
```

## Quick start

```python
import searchpath

# Find the first config.toml in project or user directories
config = searchpath.first("config.toml", "/project", "~/.config")

# Find all Python files
py_files = searchpath.all("**/*.py", "/src")

# Get match with provenance information
match = searchpath.match("settings.json", ("project", "/project"), ("user", "~/.config"))
if match:
    print(f"Found in {match.scope}: {match.path}")
```

## Usage

### The `SearchPath` class

```python
from searchpath import SearchPath

# Create with named scopes
sp = SearchPath(
    ("project", "/project/.config"),
    ("user", "~/.config/myapp"),
    ("system", "/etc/myapp"),
)

# Find first matching file
config = sp.first("config.toml")

# Find all matching files with provenance
matches = sp.matches("**/*.toml")
for m in matches:
    print(f"{m.scope}: {m.relative}")
```

### Pattern filtering

```python
# Include/exclude patterns
sp.all("**/*.py", exclude=["test_*", "**/tests/**"])

# Load patterns from files
sp.all(exclude_from="exclude_patterns.txt")

# Ancestor pattern files (like gitignore cascading)
sp.all(exclude_from_ancestors=".searchignore")
```

### Manipulating search paths

```python
# Append path components
config_sp = sp.with_suffix(".config", "myapp")

# Concatenate search paths
combined = project_sp + user_sp

# Filter to existing directories
sp.existing()
```

### Custom matchers

```python
from searchpath import RegexMatcher, GitignoreMatcher

# Regex patterns
sp.all(r".*\.py$", matcher=RegexMatcher())

# Gitignore-style patterns (requires pathspec)
sp.all(exclude=["*.pyc", "__pycache__/"], matcher=GitignoreMatcher())
```

## API

### Module-level functions

```python
def first(
    pattern: str = "**",
    *entries: Entry,
    kind: Literal["files", "dirs", "both"] = "files",
    include: str | Sequence[str] | None = None,
    include_from: Path | str | Sequence[Path | str] | None = None,
    include_from_ancestors: str | None = None,
    exclude: str | Sequence[str] | None = None,
    exclude_from: Path | str | Sequence[Path | str] | None = None,
    exclude_from_ancestors: str | None = None,
    matcher: PathMatcher | None = None,
    follow_symlinks: bool = True,
) -> Path | None
```

Find the first matching path across directories. Returns `Path` or `None`.

```python
def match(...) -> Match | None  # Same parameters as first()
```

Find the first matching path with provenance information.

```python
def all(
    pattern: str = "**",
    *entries: Entry,
    kind: Literal["files", "dirs", "both"] = "files",
    dedupe: bool = True,  # Additional parameter
    include: ...,  # Same as first()
    ...
) -> list[Path]
```

Find all matching paths across directories.

```python
def matches(...) -> list[Match]  # Same parameters as all()
```

Find all matching paths with provenance information.

### The `SearchPath` class

```python
class SearchPath:
    def __init__(self, *entries: Entry) -> None: ...

    @property
    def dirs(self) -> list[Path]: ...

    @property
    def scopes(self) -> list[str]: ...

    def first(self, pattern: str = "**", ...) -> Path | None: ...
    def match(self, pattern: str = "**", ...) -> Match | None: ...
    def all(self, pattern: str = "**", ...) -> list[Path]: ...
    def matches(self, pattern: str = "**", ...) -> list[Match]: ...

    def with_suffix(self, *parts: str) -> SearchPath: ...
    def filter(self, predicate: Callable[[Path], bool]) -> SearchPath: ...
    def existing(self) -> SearchPath: ...
    def items(self) -> Iterator[tuple[str, Path]]: ...
```

### Match dataclass

```python
@dataclass(frozen=True, slots=True)
class Match:
    path: Path      # Absolute path to the matched file
    scope: str      # Scope name (e.g., "user", "project")
    source: Path    # The search path directory

    @property
    def relative(self) -> Path: ...  # Path relative to source
```

### Entry type

```python
Entry = tuple[str, Path | str | None] | Path | str | None
```

### Pattern matchers

- `GlobMatcher` - Default glob-style patterns (`*`, `**`, `?`, `[abc]`)
- `RegexMatcher` - Full Python regex syntax
- `GitignoreMatcher` - Full gitignore compatibility (requires `pathspec`)

### Exceptions

```python
SearchPathError          # Base exception
├── PatternError         # Pattern-related errors
│   ├── PatternSyntaxError(pattern, message, position)
│   └── PatternFileError(path, message, line_number)
└── ConfigurationError   # Invalid configuration
```

## Development

```bash
# Clone and install
git clone https://github.com/tbhb/searchpath
cd searchpath
just install

# Common commands
just test          # Run tests
just lint          # Run linters
just format        # Format code
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## AI disclosure

The development of this library involved AI language models, specifically [Claude][claude]. AI tools contributed to drafting code, tests, and documentation. Human authors made all design decisions and final implementations, and they reviewed, edited, and validated AI-generated content. The authors take full responsibility for the correctness of this software.

## Acknowledgments

This library optionally uses the [pathspec][pathspec] library by Caleb P. Burns for gitignore-compatible pattern matching.

## License

MIT License. See [LICENSE](LICENSE) for details.

[claude]: https://claude.ai
[pathspec]: https://github.com/cpburnz/python-pathspec
