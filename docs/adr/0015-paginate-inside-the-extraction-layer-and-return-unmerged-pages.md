# ADR-0015: Paginate inside the extraction layer and return unmerged pages

**Status:** Accepted
**Date:** 2026-08-25

## Context

ADR-0006 limits ingestion to the top 100 chart positions and rejects a single
`limit=100` request: Last.fm may honour a smaller page size than the one requested, and
when it does the response is short but carries HTTP 200 and no error document. The
shortfall is therefore invisible to the caller. A loop that keeps asking until the
target is met was the accepted answer, but ADR-0006 did not say where that loop lives.

Three constraints were already on record before the loop was written:

- Rank is not a field in the payload. It is derived from `@attr` (`page`, `perPage`)
  plus a record's position inside its page, so page boundaries and page metadata must
  survive into the raw layer (P2.2).
- The extraction layer's contract, stated in `extract/__init__.py`, is that nothing in
  it reshapes data — it returns what the API sent.
- `requests.Session` only amortises its TCP connection when the same object serves
  every request in a run.

## Decision

We will paginate inside `extract/api.py`, in a function that returns
`list[dict[str, Any]]` — one whole, verbatim page payload per element, in request order.

The loop stops on the number of records actually received, never on arithmetic over the
requested page size, and is bounded by three independent conditions: the accumulated
record count reaching the target, a page arriving with no records, and a page ceiling
that is never expected to bind.

The default page size is set below the target (50 against 100) so that the pagination
path executes on every run rather than only on the day the server truncates a page.

The returned list may hold more tracks than the target. Trimming is reshaping and
belongs to the transform layer.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Loop in the caller (the raw-loading code of P2.2) | Pagination is a property of this source's transport, not of the pipeline. It would tie the raw layer to Last.fm and force `requests.Session` — and therefore the `requests` dependency — across the layer boundary |
| One request with `limit=100`, no loop | Cancels ADR-0006 without refuting it. Measured to work today, but silently returns short data the day the server caps the page |
| Merge the pages into one payload or one track list | Destroys the per-page `@attr` that rank is derived from, and breaks the layer's own contract that payloads are returned untouched |
| Yield pages from a generator | Correct at a scale we do not have. It trades atomicity for memory: a failure mid-iteration leaves the caller having already persisted part of a run. Revisit if a source ever exceeds memory |
| Stop on `totalPages` from `@attr` | `total` is a fixed ceiling of 10000, not a count, so `totalPages` is derived from it and never signals exhaustion |

## Consequences

- The raw layer receives a list it can persist page by page, each with its `@attr`
  intact, satisfying the constraint that rank stays recoverable.
- Callers never learn that this source paginates. A source that pages differently later
  changes one module.
- Two HTTP requests per run instead of one. Against a documented ceiling of five
  requests per second this is not a cost, and it buys daily execution of the loop.
- The transform layer inherits a documented obligation: the input may exceed 100 tracks
  and must be trimmed by rank there.
- A run that hits the page ceiling logs a warning and returns what it has rather than
  raising. The caller sees fewer tracks than the target; the loud failure is in the log,
  not in an exception. This is a deliberate asymmetry and should be revisited when the
  pipeline gains alerting.
