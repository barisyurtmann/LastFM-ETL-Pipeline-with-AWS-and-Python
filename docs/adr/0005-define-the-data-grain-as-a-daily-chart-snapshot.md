# ADR-0005: Define the data grain as a daily chart snapshot

**Status:** Accepted
**Date:** 2026-08-12

## Context

The grain of a table is the answer to "what does one row represent". Every downstream
decision depends on it: the partition key (4.2), the idempotent write semantics (4.5,
5.7), the Pydantic model fields (5.2), the uniqueness checks (5.8) and every Athena query
written in step 9. Choosing it wrongly is not a bug that surfaces as an error — it
surfaces months later as a question the table cannot answer.

The measurements from 1.5 and 1.6 constrain the choice:

- The payload carries **no date field**. Whatever temporal meaning the data has must be
  attached from outside, at ingestion time.
- `playcount` and `listeners` are **cumulative counters**, not per-period values.
  `"playcount": "1114096"` is a lifetime total, not "plays today".
- `chart.getTopTracks` accepts only `page` and `limit`. There is no date parameter, so a
  day that is not fetched cannot be fetched later. Missing data is permanently missing.
- `mbid` is absent as a dictionary key in 4 of 19 records in the tail of the chart
  (`chart_gettoptracks_edge_cases.json`), while being present in all 20 records of
  page 1. It is never the empty string — the key simply does not exist.
- `(artist.name, name)` and `url` are each fully unique within both recorded pages
  (20/20 and 19/19). `url` is a URL-encoded rendering of the same two values and adds no
  distinguishing information.
- The pipeline will run on two developer machines in local time and, from 9.7, on AWS
  Lambda in UTC.

## Decision

We will define the grain of the curated table as:

> **One row = one track appearing in the Last.fm global top-tracks chart, as observed on
> one UTC day.**

The primary key is **`(snapshot_date, artist_name, track_name)`**.

Concretely:

- `snapshot_date` is a UTC calendar date, assigned by the pipeline at extraction time
  because the API supplies none.
- A daily run **appends a new set of rows** rather than updating existing ones. A track
  that appears on 30 consecutive days produces 30 rows.
- `url` is stored as an ordinary column, not as the key.
- `mbid` is stored as a nullable attribute, never as part of any key.
- `artist_name` is stored denormalised on the fact row. No separate artist dimension is
  created at this stage.
- `snapshot_date` (business date) and the audit column `ingested_at` (technical time)
  remain **two separate columns** even though they coincide on a normal daily run.

In Kimball terms this is a **periodic snapshot fact table**.

## Alternatives considered

| Option | Why rejected |
|---|---|
| One row per track, updated in place with the latest `playcount` (SCD Type 1) | Destroys history silently. Because `playcount` is cumulative, the daily delta is only derivable by differencing two snapshots; overwriting makes it unrecoverable. No query could answer when a track peaked, or how many plays it gained on a given day. Nothing errors — the table simply cannot answer the questions it exists for. |
| Include `mbid` in the primary key | Adding a column to a key narrows the grain and increases duplication risk rather than reducing it. `mbid` is missing in 21% of tail records, and a NULL component cannot be enforced by a UNIQUE constraint (`NULL != NULL`). It is MusicBrainz's identifier, not Last.fm's: a track that has no match today may acquire one tomorrow, changing its key and appearing as a new entity. |
| Use `url` as the primary key | Measured as equally unique, so this was a genuine trade-off, not an obvious rejection. Rejected because a URL is an address, not an identity: keying on it couples the data model to the source system's site structure, and every analytical filter becomes a `LIKE` against an encoded string instead of a readable equality. Retained as a column so the canonical reference is not lost. |
| Use local dates instead of UTC | The same chart would receive different `snapshot_date` values depending on which machine ran the pipeline, breaking the key across environments. `date.today()` returns local time and is the specific trap here. |
| One row per (track, artist) with a separate artist dimension | Premature. Page 1 shows 6 artists across 20 tracks, so a dimension is defensible, but no query in the roadmap requires artist-level attributes, and a second table doubles the write path and the idempotency surface. Revisit if artist attributes beyond the name are ever ingested. |
| Collapse `snapshot_date` and `ingested_at` into one column | They coincide only on the normal path. During a backfill reconstructed from the raw layer, `ingested_at` is today while `snapshot_date` is a past date; a single column would have to lie about one of them. |

## Consequences

**Easier**

- Trend analysis becomes possible: daily deltas are derived as
  `playcount(t) - playcount(t-1)` over the same key.
- Idempotency follows from the key rather than being bolted on. Re-running a given day
  produces identical keys, so a partition overwrite on `snapshot_date` leaves the row
  count unchanged. This satisfies 4.5, 5.7 and 6.8 by construction.
- `snapshot_date` is the natural partition key for both the local raw layer and S3,
  aligning with the `dt=` convention already recorded in `PROJECT_CONTEXT.md` §4, and it
  lets Athena queries prune partitions instead of scanning the bucket.
- Backfill (6.4) has a well-defined meaning: reprocess raw files for a date range. It
  cannot mean re-fetching from the API, and the grain makes that explicit.

**Harder / accepted costs**

- The table grows unbounded — roughly 10,000 rows per day if the full chart is ingested,
  and it never shrinks. Storage and Athena scan cost grow linearly with retention, which
  makes partition pruning a requirement rather than an optimisation (9.9, 9.11).
- Queries become more verbose. "The current chart" is no longer `SELECT *` but requires
  filtering on the latest `snapshot_date`.
- The key is a natural key built from mutable text. If Last.fm renames an artist or a
  track, historical rows keep the old name and a trend query joining on the name breaks.
  This is a consequence of snapshot semantics rather than a defect — no data is lost, and
  the raw layer still holds the original response — but it means name-based joins across
  long time ranges are not guaranteed. A surrogate key would not fix this either, since
  it would still have to be assigned from the same natural key.
- A day that is never fetched is a permanent gap in the table, and nothing in the data
  itself reports the gap. Detecting missing partitions requires monitoring outside the
  pipeline (9.10).
- The same track may appear on two pages within a single day's fetch if the chart
  reorders while pages are being requested. The key would then collide within one
  `snapshot_date`. This was not observed — the two recorded pages do not overlap — and it
  remains an open question for 4.5 and 5.8 rather than a solved one.

**Reversibility**

Low to moderate. Narrowing the grain later (adding a column to the key) is feasible;
widening it is not, because the discarded detail no longer exists. This asymmetry is the
reason the decision is taken before any code is written. The raw layer mitigates it
partially: as long as raw files are retained, the curated table can be rebuilt under a
different grain, but only for days that were actually fetched.
