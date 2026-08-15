# Architecture Decision Records

An ADR captures a single architectural decision, the context that forced it, and the
consequences we accept by making it. The practice comes from Michael Nygard's 2011 post
*"Documenting Architecture Decisions"*.

## Why this exists

Code shows *what* was built. It never shows what was considered and rejected, or why.
Six months later that reasoning is gone, and someone — often the original author —
undoes a deliberate decision because it looked arbitrary.

## Rules

- One decision per file. If a file needs the word "also", it is two ADRs.
- Numbered sequentially, never renumbered: `0001-`, `0002-`, ...
- Filename is a short imperative phrase: `0002-use-src-layout.md`.
- ADRs are **immutable**. A decision that changes is not edited — a new ADR supersedes it,
  and the old one is marked `Superseded by ADR-00XX`.
- Written in English. This directory is part of the portfolio.

## Status values

| Status | Meaning |
|---|---|
| `Proposed` | Under discussion |
| `Accepted` | In effect |
| `Superseded by ADR-00XX` | Replaced by a later decision |
| `Deprecated` | No longer relevant, not replaced |

## Template

```markdown
# ADR-00XX: <short imperative title>

**Status:** Accepted
**Date:** YYYY-MM-DD

## Context

What forces are at play? What constraint, requirement, or problem made a decision
necessary? Facts only — no conclusions yet.

## Decision

What we will do, stated in the active voice: "We will ...".

## Alternatives considered

| Option | Why rejected |
|---|---|

## Consequences

What becomes easier, and what becomes harder. Include the costs honestly — an ADR with
only upsides was not a real decision.
```

## Index

| # | Title | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-use-src-layout.md) | Use a src layout for the package | Accepted |
| [0003](0003-use-uv-for-environment-and-dependency-management.md) | Use uv for environment and dependency management | Accepted |
| [0004](0004-store-recorded-api-payloads-as-test-fixtures.md) | Store recorded API payloads as test fixtures | Accepted |
| [0005](0005-define-the-data-grain-as-a-daily-chart-snapshot.md) | Define the data grain as a daily chart snapshot | Accepted |
| [0006](0006-limit-ingestion-to-the-top-100-chart-positions.md) | Limit ingestion to the top 100 chart positions | Accepted |
| [0007](0007-adopt-dlt-for-extraction-and-raw-loading.md) | Adopt dlt for extraction and raw loading | Accepted |
| [0008](0008-transform-with-dbt-on-duckdb.md) | Transform with dbt on DuckDB instead of Python | Accepted |
