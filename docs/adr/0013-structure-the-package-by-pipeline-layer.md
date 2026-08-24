# ADR-0013: Structure the package by pipeline layer

**Status:** Accepted
**Date:** 2026-08-24

## Context

Until P2.1 the package held a single module, `config.py`. The first real pipeline code
needed a home, and the layout chosen now is the one every later module inherits.

Three facts constrained the choice:

1. **The architecture is fixed and small** (ADR-0010): read from an API, reshape nested
   JSON into two tables, write Parquet to S3. Three responsibilities, known in advance —
   not a guess about future growth.
2. **The same code runs twice**, locally in P2 and inside two Lambdas in P3 (ROADMAP P3.1
   and P3.2). The extract Lambda must be able to import the extraction path without
   dragging in pandas, pyarrow, or anything the transform path needs. A layout that makes
   that separation visible makes the packaging step mechanical.
3. **Cold start bills import time.** Every name re-exported from a package `__init__.py`
   is imported when the package is imported, on every cold start.

The course this project follows keeps everything in one file per Lambda, which is why the
alternative had to be examined rather than dismissed.

## Decision

We will structure `src/lastfm_etl/` by pipeline layer, one package per layer, with the
module inside named after the *kind of source or sink* it talks to:

```
src/lastfm_etl/
    config.py            shared: read once from the environment
    extract/
        __init__.py      public surface of the layer
        api.py           Last.fm HTTP API
    transform/           (P2.3)
    load/                (P2.2)
```

Dependencies flow one way: every layer may import `config`; no layer imports another
layer. Composition happens in the entrypoint, which does not exist yet and will be
created in P2.4 when there is something to compose.

Each layer's `__init__.py` re-exports its public names — including its exception types,
because the module that raises does not import them, the caller that catches does.
Re-exports are kept minimal for the cold-start reason above.

## Alternatives considered

| Option | Why rejected |
|---|---|
| **One module per layer** (`extract.py`, `transform.py`) | Works today, and would be the right call if each layer had exactly one source. But `extract` already has a second source in the plan — the transform Lambda reads from S3 (P3.2) — and splitting a module into a package later means rewriting every import that names it. The package costs one `__init__.py` now and nothing later |
| **Split by data domain** (`tracks/`, `artists/`) | The two domains are produced by the *same* API call and separated by the *same* flattening pass. A domain split would put two halves of one function in two directories, and every change would touch both |
| **A single module, as the course does** | Defensible for a script that is pasted into a console. Here it removes the boundary that P3 depends on: the extract Lambda would import the transform layer's dependencies, and the packaged zip would carry pandas for a function that never calls it |
| **`extract/lastfm.py` instead of `extract/api.py`** | The package is already `lastfm_etl`; `lastfm_etl.extract.lastfm` repeats itself. Naming by source *type* leaves room for `extract/s3.py` without a second naming convention |

## Consequences

**Easier:**

- The P3 packaging step is mechanical: each Lambda's zip contains `config` plus one layer.
  Nothing has to be untangled first.
- A file can be renamed or split without touching call sites, because callers import from
  the layer, not from the module inside it.
- The dependency rule is checkable by reading imports. A layer importing another layer is
  a visible violation, not a judgement call.

**Harder:**

- Four files where one would run. For a pipeline this small the structure is carried for
  the sake of P3, not for today's code — a cost paid in advance against a benefit that is
  planned but not yet realised.
- Every layer needs an `__init__.py` decision: what is public, what is not. That is one
  more thing to get wrong, and getting it wrong is silent — an over-broad re-export shows
  up as cold-start latency, not as an error.
- The rule "no layer imports another layer" has no enforcement. Until an import-linter
  runs in CI (ROADMAP → next round) it holds only by discipline.

**Standing:** Layer-based layout for small pipelines is a common convention, not a
published standard; domain-based layouts are equally common and win at larger scale, where
one team owns one domain end to end. The deciding factor here was P3's packaging boundary,
which is specific to this project.
