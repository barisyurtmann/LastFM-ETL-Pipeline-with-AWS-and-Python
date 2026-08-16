# ADR-0010: Adopt the course architecture as the project scope

**Status:** Accepted
**Date:** 2026-08-15

## Context

This project reimplements the four-part "Spotify Pipeline" project from a data
engineering course. The course specifies: a scheduled CloudWatch rule invoking an
extraction Lambda, raw JSON written to one S3 bucket, an S3 object-created event
invoking a transformation Lambda, cleaned tables written to a second S3 bucket, a Glue
Crawler populating the Glue Data Catalog, and Athena for SQL.

The project owner's reason for rebuilding it with assistance is explicit and narrow: the
course teaches the architecture but omits the engineering practice around it. Credentials
are hardcoded, code is pasted into the Lambda console rather than kept in version
control, there is no `src/` layout, no environment isolation, no tests, and IAM is
`AmazonS3FullAccess` — which the course itself flags as unsuitable outside a tutorial.
The gap between "it works in the console" and "it is a repository someone else can run"
is the subject being learned.

Until now that scope was not written down anywhere, and every component became a design
question. Over nine days the roadmap replaced the Glue Crawler with Athena partition
projection, replaced the two-Lambda split with a single runner plus a CLI, and replaced
the entire extract and transform tier with dlt and dbt (ADR-0007, ADR-0008, both
superseded by ADR-0009). Each substitution was individually defensible. Together they
produced 9,527 lines of documentation and no pipeline.

The binding constraint was never which tools are best. It was that the project had no
written boundary, so nothing was ever out of scope.

## Decision

We will treat the **course's four parts as the definition of scope**. The architecture is
built as taught, including the components a from-scratch design would question.

The professional practice the course omits is what this project adds, and it is
enumerated rather than left to judgement: configuration and secret handling, an IAM user
and budget alarm, bucket hygiene, a `src/` package with module boundaries, error paths,
tests against recorded fixtures, zip-packaged deployment, least-privilege roles, and a
README. `ROADMAP.md` maps each of these to a specific sub-step.

Four deviations from the course are taken deliberately and recorded here:

| Deviation | Reason |
|---|---|
| **Last.fm** instead of the Spotify API | Step 1 already measured Last.fm's error behaviour, fixed the grain, and recorded fixtures (ADR-0004, 0005, 0006). Switching discards that work. Last.fm is also simpler: an `api_key` query parameter rather than an OAuth token exchange. |
| **`requests`** instead of `spotipy` | Last.fm has no official wrapper. More importantly, a wrapper hides the error path, and the error path is one of the things being learned. |
| **Two tables** (`tracks`, `artists`) instead of three | `chart.getTopTracks` does not return album data. The nested-flattening and foreign-key lesson survives with two tables and a join. |
| **Parquet** instead of CSV | The Glue Crawler infers types from CSV and gets them wrong often enough that the course itself warns about headers. Parquet carries its own schema. The code change is `to_csv` → `to_parquet`, and the AWS-provided pandas layer already includes the writer. |

Everything not in the course and not in the practice list above is out of scope for this
round and belongs in `ROADMAP.md` under "Sonraki tur" — including CI, Terraform, dbt,
partitioning, and alarms.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Design the optimal architecture for this workload | Produces a better pipeline and a worse project. The architecture was never the open question; the practice around it was. Redesigning it reopens the discussion that has already cost this project nine days. |
| Follow the course exactly, including hardcoded credentials and console-pasted code | Removes the only reason this project is being built with assistance rather than by following the videos. |
| Substitute Athena partition projection for the Glue Crawler | Cheaper and technically better for a fixed schema, but the Crawler is one of the course's components and schema inference over object storage is a concept worth meeting once. Its per-run cost is measured in P4.1 rather than argued in advance. |
| Collapse the two Lambdas into one function | Simpler and cheaper, but removes the S3 event trigger — the course's only example of event-driven coupling, and the source of its most instructive failure mode. |
| One bucket with `raw/` and `curated/` prefixes | Fewer resources to configure, but the transform Lambda writing into the bucket that triggers it is an infinite-loop risk that only a correct prefix filter prevents. Two buckets make the loop structurally impossible, and it is what the course does. |

## Consequences

**Easier.**

- Scope questions have a mechanical answer: if it is not in the course and not in the
  practice list, it is next round. This removes the largest source of expansion in this
  project's history.
- Every AWS service in the pipeline is one the project owner will be asked about in an
  interview, and the course's own framing — "this is the same pattern used in production,
  at smaller scale" — is defensible.
- The four deviations are written down, so the difference between this repository and the
  course is a short list rather than something a reader has to reconstruct.

**Harder, and accepted.**

- We knowingly build a Glue Crawler over a schema that does not change, and it is billed
  per run (~$0.44) on a personal budget. P1.2 requires a budget alarm before any of this
  exists, and P4.1 requires recording the real cost.
- The two-Lambda split creates a partial-failure state — raw written, transform failed —
  that a single function would not have. The course's `to_processed/` → `processed/` file
  move is the mechanism that makes this recoverable, and P3.2 must implement it
  deliberately rather than copying it.
- The course's transform Lambda lists every file in `to_processed/` on each invocation
  while being triggered per object, so two objects arriving together can be processed
  twice. This is inherited from the reference implementation and must be addressed in
  P3.2 rather than reproduced.
- Deferring partitioning to a later round means Athena scans the whole table on every
  query. At this volume the cost is negligible, but the pipeline as built does not
  demonstrate partition pruning, and that should not be claimed of it.
