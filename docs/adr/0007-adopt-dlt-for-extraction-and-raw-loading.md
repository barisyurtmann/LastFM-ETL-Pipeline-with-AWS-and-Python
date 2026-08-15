# ADR-0007: Adopt dlt for extraction and raw loading

**Status:** Accepted
**Date:** 2026-08-15

## Context

The roadmap up to this point specified a hand-written extract layer (step 3) and a
hand-written raw layer (step 4): a `requests.Session` wrapper, a custom exception
hierarchy, retry with exponential backoff and jitter, a throttle, a pagination loop
bounded by a target record count, a path builder, and atomic temp-then-rename writes.
That is roughly 300 lines of infrastructure code before a single row of analysis exists.

Two facts changed the calculation.

**The behavioural knowledge that code was meant to produce has already been produced.**
Step 1 measured the API by hand rather than by reading documentation: error codes and
their HTTP statuses (1.3, correcting a wrong assumption in `PROJECT_CONTEXT.md`), payload
anatomy and type traps (1.5), the data grain (ADR-0005), the effect of `limit` on
pagination metadata and the absence of `RateLimit-*` headers (ADR-0006, 1.8). Writing a
client encodes that knowledge a second time; it does not create it.

**The project owner's learning objective has a deadline.** The stated goal is to reach
data modelling, dbt and warehouse work. Time spent reimplementing an ingestion framework
is time not spent on the modelling layer, which is both the actual objective and the part
of this project a reader would judge.

Separately: this layer is not written by hand in current practice. Ingestion frameworks
(dlt, Airbyte, Fivetran, Meltano) exist precisely because retry, pagination, incremental
state and schema evolution are the same problem in every pipeline.

## Decision

We will use **dlt** for extraction and raw loading: a `rest_api` source against the
Last.fm endpoint and a `filesystem` destination writing partitioned files to local `data/`
and later to `s3://`.

We will treat dlt's behaviour as something to be **read and recorded**, not merely
consumed. Specifically, A.3 and A.6 require documenting how dlt's retry and pagination
defaults relate to the behaviour measured in 1.3 and 1.8, and A.5 requires choosing the
write disposition ourselves rather than accepting the default.

Steps 2, 3 and 4 of the previous roadmap are retired and replaced by step A.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Hand-write the client and raw layer as originally planned | The knowledge it would teach was already obtained by measurement in step 1. The remaining yield is implementation practice, at a cost of several sessions on the critical path to the modelling work that is the actual objective. |
| Hand-write it first, then replace it with dlt | Doubles the work on this layer to produce a comparison that can be obtained by reading dlt's configuration surface. Also creates a repository whose history shows a rewrite with no functional change. |
| Airbyte or Meltano | Both are heavier: a server and connector runtime rather than a Python library. Neither fits a single-file Lambda deployment (E.6), which is the stated cloud target. |
| Fivetran | Managed and paid. The project runs on a personal budget and one of its explicit goals is understanding cost, not outsourcing it. |
| `requests` plus `tenacity` | A middle option: keeps the pipeline hand-written but removes the retry loop. Rejected because retry is the smallest part of the layer — pagination, state, schema inference and the raw write path are the bulk, and `tenacity` addresses none of them. |

## Consequences

**Easier.**

- Extraction, pagination, retry, load state and raw file layout are configuration rather
  than code, which removes the largest block of work between here and the modelling layer.
- The local-to-S3 migration (E.3) becomes a destination configuration change. The
  storage abstraction that step 9.3 was going to require of us is supplied by the tool,
  and E.3 becomes a test of whether we configured it correctly rather than a rewrite.
- dlt's load metadata (`_dlt_loads`, load ids, stored schemas) provides lineage that the
  old 4.6 would have had to invent.
- The interview answer is stronger than either extreme: the API's failure and rate-limit
  behaviour was measured first-hand, and the framework was then chosen with that
  measurement in view.

**Harder, and accepted.**

- We no longer control the failure path directly. When ingestion misbehaves, the
  diagnosis starts in someone else's code. A.6 exists to make that first encounter happen
  deliberately, with a deliberately broken key, rather than in production.
- ADR-0006 remains binding as a **requirement** but its stated implementation is
  obsolete. Three of its clauses must be re-verified against dlt's paginator rather than
  assumed: that the loop stops at a target record count, that page size is never
  hardcoded in the `rank` calculation, and that running out of pages before the target is
  an error rather than a silent short result. If dlt cannot express the third, that gap
  must be recorded, not ignored.
- The exception hierarchy, backoff and atomic-write implementations are no longer written
  in this project. That practice is genuinely forgone, not deferred.
- A dependency now sits on the critical path. Its version is pinned in `uv.lock`, and a
  breaking change in it is a project risk that hand-written code would not have had.
