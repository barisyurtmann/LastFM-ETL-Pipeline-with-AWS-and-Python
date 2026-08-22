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
| [0007](0007-adopt-dlt-for-extraction-and-raw-loading.md) | Adopt dlt for extraction and raw loading | Superseded by 0009 |
| [0008](0008-transform-with-dbt-on-duckdb.md) | Transform with dbt on DuckDB instead of Python | Superseded by 0009 |
| [0009](0009-return-to-a-hand-written-python-pipeline.md) | Return to a hand-written Python pipeline | Accepted |
| [0010](0010-adopt-the-course-architecture-as-the-project-scope.md) | Adopt the course architecture as the project scope | Accepted |
| [0011](0011-deploy-all-resources-in-eu-central-1.md) | Deploy all resources in eu-central-1 | Accepted |
| [0012](0012-separate-raw-and-transformed-data-into-two-buckets.md) | Separate raw and transformed data into two S3 buckets | Accepted |

## When is a decision an ADR?

Added 2026-08-15, after three ADRs on the same subject were written and two of them
superseded without a line of implementation behind any of them.

An ADR is warranted when **reversing the decision later would be expensive** — when it
shapes the directory layout, the data contract, the dependency set, or something already
deployed. If a choice can be undone with `git revert` and no downstream rework, it is a
commit message, not an ADR.

An ADR is written **after the code that justifies it works**, not before. A decision
recorded ahead of its implementation records a prediction; this repository's history
shows what that costs.
