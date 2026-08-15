# ADR-0008: Transform with dbt on DuckDB instead of Python

**Status:** Accepted
**Date:** 2026-08-15

## Context

Step 5 of the previous roadmap specified a Python transform layer: Pydantic models
validating each record at the boundary, flattening and type coercion in pandas, audit
columns, quality checks, and a Parquet write. That layer is what makes this project an
ETL pipeline — the transform runs in a separate processing tier before the data reaches
the query engine.

The transform is small. The target schema drafted in 1.7 is a flat table derived from one
nested `artist` object and a handful of scalar fields, at the grain fixed by ADR-0005.
Expressed in SQL it is a short `SELECT`.

The project owner's next subject is data modelling with dbt and a cloud warehouse. The
skills that transfer to that work are layering (staging and marts), grain enforcement,
materialization strategy, and data tests — none of which are practised by writing pandas
code, and all of which are the everyday surface of dbt.

DuckDB reads Parquet in place. It does not need the raw layer to be loaded into a
database first, so introducing it does not add a storage tier or a service to run.

## Decision

We will transform with **dbt** using the **dbt-duckdb** adapter, reading the raw Parquet
written by dlt (ADR-0007) directly from the filesystem.

The model layer is split into **staging** (one model per source, flattening, typing and
renaming only) and **mart** (the fact table enforcing the ADR-0005 grain). Data quality
moves from Python assertions to dbt tests: `not_null`, `unique` on the grain key,
`accepted_values`, and at least one singular test.

This makes the pipeline **ELT**: the T runs inside the query engine, expressed in that
engine's language, after the data has landed.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Python transform with Pydantic and pandas, as originally planned | Teaches a boundary-validation pattern the project owner already applies, and teaches nothing about layering, materialization or data tests. It also produces a transform that must be rewritten to move to a warehouse, which is the stated next destination. |
| dbt against Athena (`dbt-athena`) from the start | Puts an AWS account, credentials and per-query cost between the author and every iteration of a model. Model development is the step that needs the fastest feedback loop, so it belongs on a local engine. Athena arrives in step E, over the same Parquet. |
| DuckDB SQL scripts without dbt | Runs the same SQL, but omits `ref` and the resulting DAG, materialization strategies, tests and documentation — that is, everything the tool was chosen for. |
| SQLMesh | A credible competitor with real advantages in incremental semantics. Rejected on employability grounds rather than technical ones: dbt is what the next project and the job postings use. |
| Keep the Python transform and add dbt as a second layer on top | Two transform layers for a table with a single-digit column count. The grain would be enforced in two places, which is the same "two sources of truth" failure the documentation structure was designed to avoid. |

## Consequences

**Easier.**

- The modelling concepts that are the actual objective — staging/mart separation,
  fact grain, surrogate keys, materializations, data tests, lineage docs — are practised
  in the tool that a subsequent warehouse project uses unchanged.
- Data quality checks become declarative and run on every build, instead of assertions
  that exist only where someone remembered to write them.
- `dbt docs` generates the lineage graph, so the architecture diagram in the README is
  derived from the code rather than drawn by hand and left to drift.
- The same SQL moves to Athena or Snowflake by changing an adapter and a profile, which
  is the migration this project is a rehearsal for.

**Harder, and accepted.**

- The repository name and `PROJECT_CONTEXT.md` describe an ETL pipeline. Both are now
  wrong and must be corrected; the distinction between ETL and ELT is exactly the kind of
  thing a reader will ask about, and getting it wrong in the README is worse than not
  mentioning it.
- Two unfamiliar tools are introduced in consecutive steps. When a run breaks, isolating
  whether dlt or dbt caused it is harder than debugging one hand-written pipeline. Step A
  must be fully closed before step B begins.
- Record-level validation is weaker than Pydantic would have been. dbt tests assert over
  a table after it is built; they do not reject a single malformed record at the boundary.
  A bad row is caught, but later and in aggregate. For this project's grain and volume
  that is an acceptable trade; for a pipeline feeding a downstream system it might not be.
- Where dbt runs in the cloud is now an open question with a real constraint behind it —
  packaging dbt into a Lambda is not obviously feasible. E.6 records this as unresolved
  rather than assuming it away.
