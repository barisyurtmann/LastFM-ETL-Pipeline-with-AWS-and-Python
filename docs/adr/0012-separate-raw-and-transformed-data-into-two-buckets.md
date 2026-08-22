# ADR-0012: Separate raw and transformed data into two S3 buckets

**Status:** Accepted
**Date:** 2026-08-22

## Context

The pipeline has two data layers with different guarantees:

- **Raw** — the API response, stored exactly as received. It is the source of record. If a
  transform is wrong, the fix is to re-run it against raw. Raw is never rewritten.
- **Transformed** — Parquet tables derived from raw. Entirely reproducible, therefore
  disposable.

The course this project follows uses a single bucket with two prefixes (`raw/` and
`transformed/`). That is a legitimate layout, so the alternative had to be examined rather
than dismissed.

Three facts shaped the decision:

1. **The transform Lambda is triggered by an S3 PUT event.** If its output lands in the
   same bucket that triggers it, the write is itself a PUT and can re-invoke the function.
   In a single bucket, only the event notification's prefix/suffix filter prevents this.
2. **Several settings are bucket-scoped and have no prefix-level equivalent**: versioning,
   default encryption, Block Public Access, bucket policy, replication, and Object Lock.
   Lifecycle rules and event notifications *can* be filtered by prefix; these cannot.
3. **Buckets are not a scarce resource.** The default quota is 10,000 general purpose
   buckets per account, and buckets themselves are free — billing is for storage and
   requests. An earlier draft of this reasoning cited a limit of 100; that figure is
   outdated and the argument it supported does not hold.

## Decision

We will store each layer in its own bucket:

```
lastfm-etl-raw-<suffix>            versioning enabled, source of record
lastfm-etl-transformed-<suffix>    versioning enabled, derived data
```

Both are created in eu-central-1 (ADR-0011) with Block Public Access fully enabled, SSE-S3
default encryption, and the tag `Project=lastfm-etl`.

Because the bucket name already identifies the layer, keys do not repeat it. Within the raw
bucket, objects move between two prefixes as they are processed:

```
to_processed/lastfm_raw_<ISO8601-UTC>.json
processed/lastfm_raw_<ISO8601-UTC>.json
```

## Alternatives considered

| Option | Why rejected |
|---|---|
| **One bucket, two prefixes** (the course layout) | Recursion is prevented only by a correctly configured event filter — a setting that can be forgotten, mistyped, or later loosened. Versioning, encryption defaults and bucket policy cannot differ between the layers. IAM resource ARNs become prefix patterns, where a missing `/` silently widens access to the whole bucket |
| **Three buckets** (raw / staging / curated) | There is no staging layer in this architecture. A bucket with no data in it documents nothing |
| **Separate AWS accounts per layer** | The correct answer at organisational scale, where blast radius and billing separation justify it. In a single-person learning account it adds AWS Organizations, cross-account roles, and a second billing surface for no gain |
| **One bucket, rely on recursive-invocation detection** | AWS added loop detection in 2023 and it does stop runaway invocations, but only *after* they start. A layout in which the loop cannot form is stronger than a guard that halts one already running |

## Consequences

**Easier:**

- The transform Lambda cannot trigger itself: it reads from one bucket and writes to
  another. This holds regardless of how the event filter is configured, so a configuration
  mistake cannot produce an invocation loop.
- Each layer carries its own bucket-level policy. Raw can later gain Object Lock or a
  restrictive bucket policy without affecting derived data.
- IAM policies name whole buckets (`arn:aws:s3:::lastfm-etl-raw-<suffix>/*`) instead of
  prefix patterns. Least privilege becomes verifiable by reading the policy, which matters
  because policies loosen over time.
- Deleting or expiring the transformed layer cannot touch raw.

**Harder:**

- Two globally unique names to reserve instead of one, and S3 does not reliably release a
  deleted name — a naming mistake is not cheaply undone.
- Two sets of bucket settings that must be kept consistent. Configuration drift between
  them is now possible and nothing detects it automatically. Infrastructure as code would
  address this; it is out of scope for this round.
- The transform Lambda's role needs two policy statements (read on one bucket, write on the
  other) rather than one. This is more text, though it is also more precise.
- Costs are unchanged, but they are now split across two line items in Cost Explorer. The
  `Project=lastfm-etl` tag exists so they can be recombined.

**Standing:** This is an engineering preference, not a published standard. Both layouts
appear in production systems. The deciding factor here was that structural prevention of
the invocation loop is worth more than the simplicity of a single bucket.
