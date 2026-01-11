# Explanation

This section provides understanding-oriented discussions of concepts, architecture, and design decisions. These pages answer "why" questions: why searchpath exists, why it makes certain design choices, and how to think about file discovery in prioritized directory searches.

Unlike tutorials (which guide you through tasks) or reference documentation (which lists every API detail), explanations help you build mental models. Reading these pages will deepen your understanding of searchpath and help you make better decisions when building file discovery logic.

## How to use this section

Each page explores a concept in depth. You don't need to read them in order, though the architecture overview provides useful context for the others. If you're trying to do something specific, start with the [tutorials](../tutorials/index.md) or [how-to guides](../guides/index.md) instead.

## Planned topics

Architecture overview
:   Why searchpath exists, how its components work together, and the reasoning behind key design decisions. Start here to understand the library's structure.

Pattern matching
:   How pattern matching works in searchpath. Understand the differences between glob, regex, and gitignore-style patterns, and when to use each.

Provenance tracking
:   Why knowing where files come from matters. Understand the problem searchpath solves and how Match objects provide provenance information.

Error handling
:   Searchpath's lenient-by-default philosophy for discovery operations, and when exceptions are raised. Understand the difference between discovery failures (silent) and programmer errors (exceptions).

## Related resources

- **Want hands-on practice?** Start with the [tutorials](../tutorials/index.md)
- **Need to do specific tasks?** Use the [how-to guides](../guides/index.md)
- **Looking up API details?** See the [API reference](../reference/api.md)
