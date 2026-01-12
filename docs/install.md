# Installation

searchpath requires Python 3.10 or later.

## Basic installation

=== "pip"

    ```bash
    pip install searchpath
    ```

=== "uv"

    ```bash
    uv add searchpath
    ```

=== "Poetry"

    ```bash
    poetry add searchpath
    ```

## Dependencies

searchpath has minimal dependencies to keep your dependency tree lean:

| Package                                                        | Purpose                                                |
|----------------------------------------------------------------|--------------------------------------------------------|
| [typing-extensions](https://typing-extensions.readthedocs.io/) | Backports of typing features for Python < 3.12         |

## Optional dependencies

### gitignore patterns

For full [gitignore-style pattern matching](reference/api.md#searchpath.GitignoreMatcher) via the `GitignoreMatcher` class, install with the extra:

=== "pip"

    ```bash
    pip install 'searchpath[gitignore]'
    ```

=== "uv"

    ```bash
    uv add 'searchpath[gitignore]'
    ```

=== "Poetry"

    ```bash
    poetry add 'searchpath[gitignore]'
    ```

This adds the [pathspec](https://python-path-specification.readthedocs.io/) library, which provides full gitignore compatibility including negation patterns (`!pattern`), directory-only patterns (`pattern/`), and anchored patterns (`/pattern`).

!!! tip "When to use GitignoreMatcher"

    The default `GlobMatcher` handles most use cases. Use `GitignoreMatcher` when you need:

    - Negation patterns to un-ignore previously matched paths
    - Directory-only patterns that match only directories
    - Anchored patterns that match from the root only
    - Full gitignore file compatibility

## Install from repository

To install the latest development version directly from GitHub:

=== "pip"

    ```bash
    pip install git+https://github.com/tbhb/searchpath.git
    ```

=== "uv"

    ```bash
    uv add git+https://github.com/tbhb/searchpath.git
    ```

=== "Poetry"

    ```bash
    poetry add git+https://github.com/tbhb/searchpath.git
    ```
