# ADR-0017: Model the curated layer as two tables with natural keys

**Status:** Accepted
**Date:** 2026-08-25

## Context

The reference architecture (ADR-0010) produces three tables from Spotify — albums,
artists, songs — each with a stable, service-issued identifier as its primary key. Two
facts make that model impossible to copy.

`chart.getTopTracks` returns no album, so one of the three tables has no source. And
Last.fm's identifier, `mbid`, is not guaranteed: it was measured absent — the key itself
missing from the object, not empty — in 4 of 19 recorded track objects, and it can be
absent on the nested artist as well. A field that is sometimes missing cannot be a
primary key, and a foreign key pointing at one is worse than no foreign key at all.

A separate force comes from ADR-0016. With no raw tier, this schema is the only durable
form the data ever takes. A column dropped here is dropped permanently, because the day
cannot be re-fetched (ADR-0006).

The grain was fixed earlier (ADR-0005): one row per track per UTC day.

## Decision

We will produce **two tables**, `tracks` (fact) and `artists` (dimension), keyed on
natural values:

| Table | Primary key | Foreign key |
|---|---|---|
| `tracks` | `(snapshot_date, artist_name, track_name)` | `artist_name` → `artists` |
| `artists` | `(snapshot_date, artist_name)` | — |

`mbid` is carried on both tables as a nullable attribute. It is the only way to detect a
rename later, so it is kept — but nothing keys on it.

Both tables are produced in a **single pass** over the payload, so that every
`tracks.artist_name` exists in `artists` by construction rather than by review. The
column list, types and null policy live in `docs/SCHEMA.md`, which is the specification;
this ADR records only why the shape is what it is.

## Alternatives considered

| Option | Why rejected |
|---|---|
| One denormalised table (the step 1.7 draft) | Honest for this grain and simpler to write, but removes the join from a project whose stated purpose includes learning joins, and ADR-0010 binds the scope to a two-table model. Revisit if the join ever costs more than it teaches |
| `mbid` as the primary key | Measured absent in 4 of 19 records. Keying on it would drop those rows or produce null keys |
| A surrogate key, e.g. `sha1(artist_name)` | Solves nothing at this scale: a string join over ~100 rows a day costs nothing, and an extra column is an extra thing to keep correct. It becomes right when the artist name can change while the entity does not (SCD type 2), or when the table gains a second source |
| Building `artists` in its own pass over the payload | This is exactly how the reference implementation acquires a broken foreign key: it reads the song's artist from one path and the artist table from another, so a song can reference an artist that is not in the table. Two passes make correctness a matter of discipline; one pass makes it a property of the code |
| Keeping `artist_url` out of `tracks` *and* out of `artists` | It was eliminated in the step 1.7 draft as functionally dependent on `artist_name`. That reasoning holds for a single wide table, where it would repeat on every row, and fails for a dimension, where it appears once. Field elimination is decided per table, not globally |

## Consequences

- A join is required for any question that mixes track metrics with artist attributes.
  That is the intended teaching cost, and at this size it is the only cost.
- `artists` is a **daily snapshot**, not a slowly changing dimension: it is rewritten per
  `snapshot_date` partition. History of an artist's attributes is obtainable only by
  querying across partitions. Adding SCD behaviour later means a new table shape and a
  new ADR.
- The key is a pair of free-text values. A track renamed by Last.fm — a remaster suffix
  added, casing changed — appears as a new row rather than the same row changed. Nothing
  detects this; `track_mbid` is the only clue and it is nullable.
- Row-level failures are dropped rather than repaired, and the counts are logged. The
  full policy is in `docs/SCHEMA.md`; the principle is that a row with a null key
  survives every later check and a missing row does not.
