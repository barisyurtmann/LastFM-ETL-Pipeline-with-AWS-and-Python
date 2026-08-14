# ADR-0006: Limit ingestion to the top 100 chart positions

**Status:** Accepted
**Date:** 2026-08-13

## Context

`chart.getTopTracks` exposes 10000 chart positions. Ingesting all of them daily is a
scope decision, not a technical default, and it reaches into the extract layer (step 3),
the raw layer (step 4) and the execution environment (9.7). It has to be decided
explicitly.

Measurements constrain the choice.

**`limit` is a request parameter that reshapes pagination.** The same endpoint returns
different pagination metadata depending on what the client asks for:

| Request | `@attr.perPage` | `@attr.totalPages` | `@attr.total` | records |
|---|---|---|---|---|
| `limit=20` | `20` | `500` | `10000` | 20 |
| `limit=100` | `100` | `100` | `10000` | 100 |

`totalPages` is therefore `total / perPage`, and `total` is a constant ceiling rather
than a real count. This closes an open question recorded in 1.5, where `total: 10000`
against `totalPages: 500` at `perPage: 20` was suspected of being an exact product rather
than a measured figure. It is.

**Data quality is position-dependent.** Measured in 1.5 and 1.6:

| | page 1 (positions 1-20) | page 500 (positions 9981-10000) |
|---|---|---|
| records returned | 20 | 19 |
| `mbid` key absent | 0 | 4 |
| `duration == 0` | 0 | 2 |
| distinct artists | 6 | 19 |

The head of the chart is the best-curated part of it. The tail is both the least
interesting to this project and the least reliable.

**Request cost.** The Last.fm terms of service document a limit of 5 requests per second
per originating IP address, averaged over a five-minute period, and state that sustained
per-second traffic or call spikes are grounds for suspending an API account. A full daily
crawl is 500 requests; a head-only crawl is a handful. No `Retry-After` or `RateLimit-*`
response headers are returned (measured), so a client cannot learn its remaining quota at
runtime and must stay conservative by construction.

**Irreversibility.** `chart.getTopTracks` accepts no date parameter. A day that is not
fetched cannot be fetched later. Whatever is excluded here is excluded permanently, not
merely deferred — the same constraint ADR-0005 records for the grain.

## Decision

We will ingest **the top 100 chart positions** for each daily snapshot.

We will fetch them with a **paginated loop bounded by a target record count**, not by a
fixed page count and not by a single large `limit`:

- The loop stops when the target count is reached or when the source reports no further
  pages, whichever comes first.
- The page size is a configuration value (step 2), defaulting to 20 to match the recorded
  fixtures.
- `rank` is computed per page from `@attr.page` and `@attr.perPage` as recorded in 1.7.
  The page size is never hardcoded in the rank calculation.
- Reaching the end of the pages before reaching the target count is an error condition,
  not a silent short result.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Ingest all 10000 positions | 500 requests per day for data the project has no question about, and the excluded portion is also the lowest-quality portion. The cost is paid daily and forever; the benefit is hypothetical. |
| A single request with `limit=100` | Works today, measured. But it makes correctness depend on a server-side parameter we do not control: if Last.fm caps `limit` below the requested value the response is silently short and no error is raised. It also removes pagination from the pipeline entirely, so the code path that would detect the change does not exist. |
| A fixed loop of 5 pages at `limit=20` | Correct only while `perPage` is 20. It encodes the page-size assumption in a second place, so a config change to the page size silently changes how many records are ingested. |
| Ingest the top 100 but keep `limit` at the server default | The default is not documented and was not measured; depending on an unmeasured default is the same class of mistake as the single-request option. |

## Consequences

**Easier.**

- Daily volume is ~100 rows instead of ~10000.
- Request volume sits far below the documented rate limit, so throttling (3.6) becomes
  insurance rather than a bottleneck, and Lambda feasibility (9.7) no longer depends on
  measured request latency.
- The pagination loop runs several times per normal run, so it is exercised continuously
  instead of being dead code that first executes when someone changes a configuration
  value.
- The target-count bound makes the pipeline correct under any `perPage` the server
  chooses to return, including a value it has never returned before.

**Harder, and accepted.**

- The tail of the chart is never observed, and because the endpoint takes no date
  parameter, that history cannot be reconstructed later. If a long-tail question ever
  arises, the answer is not "reprocess" — it is "start collecting now".
- `rank` is meaningful only within the ingested range. Any analysis phrased as "position
  within the full chart" is out of scope by construction, and any comparison against an
  external top-10000 list is invalid.
- The recorded fixture `chart_gettoptracks_edge_cases.json` (page 500) contains records
  that production will no longer produce: absent `mbid` keys and zero durations. The tests
  built on it in 7.4 remain in place. This is deliberate — it is cheaper to keep handling
  a case that stopped occurring than to discover a case that was never covered. The
  fixture is documentation of a real API behaviour, not a simulation of current traffic.
- A pagination loop is more code than a single request, and it introduces partial-failure
  semantics: page 3 can fail after pages 1 and 2 succeeded. The retry policy (3.4, 3.5)
  therefore applies per page, and the raw layer (step 4) must record pages individually
  so that `rank` remains recoverable.
