# Roadmap

This document outlines planned features and enhancements for searchpath, organized by theme rather than strict priority order.

## Pattern matching enhancements

### More matcher implementations

More pattern matching options for specialized use cases.

**Goals:**

- Glob pattern extensions (extended glob, brace expansion)
- Performance-optimized matchers for large directory trees
- Compiled pattern sets for repeated searches

**Use cases:**

- High-performance file discovery in build systems
- Complex pattern matching beyond standard glob

### Pattern validation and diagnostics

Better tooling for understanding why patterns match or don't match.

**Goals:**

- Pattern syntax validation with helpful error messages
- Debug mode showing which patterns matched/rejected each path
- Pattern coverage analysis

**Use cases:**

- Debugging complex include/exclude pattern sets
- Understanding unexpected search results
- Validating pattern configurations

## SearchPath enhancements

### Caching and performance

Optimize repeated searches over the same directories.

**Goals:**

- Optional result caching with configurable invalidation
- Lazy directory enumeration for large trees
- Parallel directory traversal

**Use cases:**

- Build systems with repeated file lookups
- Long-running applications with stable directory structures

## API enhancements

### Async support

Asynchronous versions of search operations.

**Goals:**

- Async versions of `first()`, `all()`, `match()`, `matches()`
- Integration with `asyncio` and `trio`
- Non-blocking directory traversal

**Use cases:**

- Web applications with async request handling
- Concurrent file discovery operations

### Streaming results

Iterator-based APIs for memory-efficient large result sets.

**Goals:**

- Generator-based versions of `all()` and `matches()`
- Early termination support
- Memory-bounded result processing

**Use cases:**

- Processing large directory trees
- Streaming results to external systems
