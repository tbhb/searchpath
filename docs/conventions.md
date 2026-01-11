# Conventions

This page explains patterns used throughout the searchpath documentation to help you navigate and understand the examples.

## Code examples

### Running examples

Most code examples are complete and runnable. You can copy them directly into a Python file or interactive session.

```python
# demo
import searchpath
from pathlib import Path

# Find first match across directories
config = searchpath.first("config.toml", project_dir, user_dir)
print(config)  # /project/.config/config.toml or None
```

### Illustrative snippets

Examples marked with `# snippet` show partial code that demonstrates a concept but will not run standalone:

```python
# snippet
def load_config(sp: SearchPath) -> dict:
    ...  # implementation details omitted
```

### Error demonstrations

Examples marked with `# Error!` show code that produces an error condition:

```python
# Error!
from searchpath import GitignoreMatcher
matcher = GitignoreMatcher()  # Raises ImportError if pathspec not installed
```

## Admonitions

The documentation uses colored boxes to highlight different types of information.

!!! note "Notes highlight key information"

    Notes draw attention to important concepts or behaviors you should be aware of.

!!! tip "Tips suggest best practices"

    Tips provide performance advice or recommend preferred approaches.

!!! warning "Warnings flag potential issues"

    Warnings alert you to common pitfalls or behaviors that might be surprising.

??? info "Collapsible boxes contain optional details"

    Click to expand sections that provide additional context you can skip if you're in a hurry.

## Method signatures

Method signatures use Python's type annotation syntax. For example:

```python
def first(
    pattern: str = "**",
    *entries: Entry,
    exclude: str | Sequence[str] | None = None,
) -> Path | None: ...
```

This signature tells you:

- `pattern` accepts a glob pattern string (defaults to `"**"`)
- `*entries` accepts any number of directory entries
- `exclude` accepts a single pattern, sequence of patterns, or None
- The return value is either a `Path` or `None`

## Terminology

Key terms appear throughout the documentation. The [glossary](reference/glossary.md) defines all terminology, including:

- **SearchPath**: An ordered list of directories to search
- **Entry**: A directory specification (path, scoped tuple, or None)
- **Match**: A result object with path, scope, and source information
- **Scope**: A name identifying which directory a match came from

## Documentation sections

The documentation is organized into four sections based on your goals:

[Tutorials](tutorials/index.md)
:   Step-by-step lessons for learning searchpath from scratch.

[Guides](guides/index.md)
:   Task-oriented recipes for accomplishing specific goals.

[Explanation](explanation/index.md)
:   Background information and conceptual discussions.

[Reference](reference/index.md)
:   Technical specifications and API documentation.

## See also

- [Glossary](reference/glossary.md) - Complete list of term definitions
- [API reference](reference/api.md) - Full API documentation
