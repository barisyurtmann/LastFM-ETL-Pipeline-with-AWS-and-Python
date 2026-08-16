# ADR-0009: Return to a hand-written Python pipeline

**Status:** Accepted
**Date:** 2026-08-15

**Supersedes:** ADR-0007 (Adopt dlt for extraction and raw loading),
ADR-0008 (Transform with dbt on DuckDB instead of Python)

## Context

ADR-0007 and ADR-0008 were both written on 2026-08-15 and replaced the hand-written
extract, raw-load and transform layers with dlt and dbt. Neither was implemented. This
ADR reverses both on the same day, before any code was written against them.

Three facts force the reversal.

**Nine days of work have produced no pipeline.** Between 2026-08-07 and 2026-08-15 the
repository accumulated 31 commits and 9,527 lines of documentation. `src/` contains one
file, `__init__.py`, and it is empty. The two closed steps — repository setup and API
discovery — are the two steps that contain no pipeline code. The stated objective is a
pipeline that runs end to end; the current trajectory does not reach it.

**The project's scope is a fixed external artifact, and dlt/dbt is outside it.** This
project reimplements a reference architecture from a data engineering course: a Python
client, a scheduled Lambda writing raw JSON to S3, an S3-event-driven Lambda writing
Parquet, a Glue Crawler, a Data Catalog and Athena. The project owner's reason for
building it with assistance was never to change that architecture — it was to learn the
professional scaffolding the course omits: `src/` layout, dependency and environment
management, configuration and secrets, error handling, tests, CI, IAM, and cost. dlt and
dbt replace the architecture rather than scaffold it. ADR-0007 and ADR-0008 optimised for
a learning objective the owner had not set.

**The revision that introduced them made the plan larger, not smaller.** The dlt/dbt
roadmap contained 39 sub-steps and required learning two unfamiliar tools in consecutive
steps — a risk ADR-0008 itself recorded. The hand-written plan it replaced was also too
large. Tool choice was never the binding constraint; plan size was.

The technical argument in ADR-0007 remains correct: ingestion frameworks exist because
retry, pagination and incremental state are the same problem everywhere, and current
practice does not hand-write that layer. This ADR does not dispute that. It concludes
that the argument, while true, does not apply to a project whose scope is a fixed
teaching architecture and whose binding constraint is time to a working pipeline.

## Decision

We will write the extract and transform layers **by hand in Python**, using `requests`,
`pandas`, `pyarrow` and `boto3`, targeting the course architecture recorded in ADR-0010.

Specifically:

- The API client, its retry and backoff policy, and the raw write path are written in
  this repository. dlt is not a dependency.
- The transform — flattening, type coercion and the Parquet write at the ADR-0005 grain —
  is Python running in a Lambda. dbt and DuckDB are not dependencies.
- The pipeline is therefore **ETL**, not ELT: the transform runs in its own tier, before
  the data reaches the query engine. The repository name is correct and does not change.
- dbt is **deferred, not rejected.** It is recorded in `ROADMAP.md` under "next round",
  to be taken up once curated Parquet is accumulating in S3 and there is real data for a
  model to sit on. Learning the tool before having the data is the trap this project has
  now fallen into once.

Steps A through E of the previous roadmap are retired and replaced by steps P1 through
P4 — one per part of the course — with 14 sub-steps in total.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Keep ADR-0007 and ADR-0008 and proceed with dlt and dbt | Departs from the reference architecture that defines this project's scope, and introduces two unfamiliar tools on the critical path to a first working run. Also leaves an unresolved feasibility question — packaging dbt into a Lambda — at the deployment step, which ADR-0008 recorded but did not answer. |
| Keep dlt for ingestion, hand-write the transform | Retains the smaller of the two benefits at the full cost of a framework on the critical path. The transform is where this project's learning value is concentrated, and dlt does not touch it. |
| Hand-write everything, but keep the 39-sub-step plan | Tool choice was not the cause of nine days without code. A plan that large fails the same way regardless of what it is built with. |
| Abandon the reference architecture and design a target from scratch | The architecture is the one part of this project that was never in question. Redesigning it converts a scoping problem into a design problem and starts the clock again. |

## Consequences

**Easier.**

- The target is fixed and externally defined. Every remaining sub-step maps to a box in a
  diagram that already exists, so "is this in scope?" has an answer that does not depend
  on judgement.
- Retry, backoff, atomic writes and schema handling are written by hand, which is what
  the project owner asked to learn and what ADR-0007 traded away.
- No new tool sits between the author and a failure. When ingestion breaks, the
  diagnosis starts in code written in this repository.
- The dependency surface is `requests`, `pandas`, `pyarrow` and `boto3` — the same set
  the course uses, minus `spotipy`. Nothing is installed purely to be learned.

**Harder, and accepted.**

- The hand-written surface is smaller than this ADR's first draft assumed. The course's
  extract is about thirty lines; what this project adds on top is configuration, an error
  path, retry and pagination — perhaps a hundred lines that a framework would supply.
  That is the honest size of the trade, and it should be described that way rather than
  as "I built an ingestion layer."
- Hand-written retry, throttling and pagination are the parts most likely to be subtly
  wrong, and there is no framework's test suite behind them. The Last.fm rate limit
  (~5 requests/second, no `RateLimit-*` headers — measured in 1.8) must be respected by
  a client-side counter with nothing to check it against.
- Data quality moves back into Python assertions rather than declarative dbt tests. They
  will exist only where someone remembers to write them, which is a real regression
  against ADR-0008 and the reason P2's completion criteria require the malformed-record
  policy to be written down.
- The lineage graph that `dbt docs` would have generated must now be drawn by hand in the
  README, and will drift from the code unless maintained.
- Three ADRs on this subject have now been written without a line of implementation
  behind any of them. The rule added to `PROJECT_CONTEXT.md` §1b — decisions are recorded
  after the code that justifies them, not before — exists to stop a fourth.

## Why this decision is more stable than the two it supersedes

ADR-0007 and ADR-0008 rested on a judgement about which skills were most worth acquiring.
That judgement was contestable, and it was contested within a day. This ADR rests on a
constraint that is not a judgement: the course architecture is a fixed artifact, and
the pipeline either matches it or does not. Reversing this decision requires changing the
project's scope, not changing an opinion about learning value.
