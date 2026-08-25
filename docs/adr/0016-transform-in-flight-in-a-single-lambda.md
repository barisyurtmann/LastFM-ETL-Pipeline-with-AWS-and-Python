# ADR-0016: Transform in flight in a single Lambda

**Status:** Accepted
**Date:** 2026-08-25

## Context

ADR-0009 states that this pipeline is **ETL, not ELT** — the transform runs in its own
tier before the data reaches the query engine. ADR-0012 then designed a raw bucket that
the extract tier writes to and a transform tier that reads from it. That layout is ELT in
everything but name: the payload is loaded to durable storage first and transformed
afterwards, which is precisely the ordering ADR-0009 rejected.

The contradiction survived three working days and produced a sub-step (P2.2, "write raw
to S3") that the roadmap's own P2 heading — *"Local: extract + transform"* — did not call
for. It was caught by reading the plan, not by reading the code.

The course this project follows (ADR-0010) does not have the raw tier either. Its part 3
reads: *"In Part 3, you will deploy this code to AWS Lambda, set up the CloudWatch trigger
for daily execution, and store the data in S3."* One deployment, one write, at the end.

The stated learning goal is ETL. Building ELT while calling it ETL teaches neither.

## Decision

We will run extract, transform and load in a **single Lambda**, in one invocation:

```
EventBridge (daily) -> Lambda -> extract pages
                              -> transform in memory
                              -> write Parquet to S3 (curated)
```

The API payload is never persisted as a pipeline layer. During local development it may
be dumped into the git-ignored `data/` directory as a developer convenience; that
directory is not part of the architecture and nothing reads from it in production.

Two consequences follow immediately and are part of this decision:

- **`rank` is computed during transform**, from a record's position inside its page plus
  that page's `@attr`. There is no second chance to recover it, so the page list must
  reach the transform in request order and unmerged — ADR-0015 already guarantees this.
- **Idempotency moves to the output key.** A re-run for the same day overwrites the same
  curated objects instead of appending a second snapshot. The `to_processed/` →
  `processed/` file move from ADR-0012 no longer exists and is not replaced.

We will keep the existing `lastfm-etl-transformed-<suffix>` bucket as the single data
bucket. The `lastfm-etl-raw-<suffix>` bucket is left in place, empty and unused: S3 does
not reliably release a deleted name, and an empty bucket costs nothing.

This supersedes ADR-0012.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Keep the raw tier and rename the project ELT | Technically the stronger pipeline, and the honest name. Rejected because the learning objective is ETL specifically, and the reference architecture does not have the tier. The trade-off is accepted with eyes open, below |
| Keep the raw tier as a "backup", still calling the pipeline ETL | The same contradiction this ADR exists to remove. A durable copy of the source payload *is* the raw tier, whatever it is called in a diagram |
| Two Lambdas without a raw tier (extract invoking transform directly) | Two functions, two roles, two cold starts, and a synchronous invoke that can fail between them — for no separation this workload needs. The split in ADR-0012 was justified by the S3 trigger, and that trigger is gone |
| Write curated data to the raw bucket and drop the transformed one | Its name would then describe the wrong contents. Names outlive the reasons they were chosen |

## Consequences

**Easier:**

- One deployment artefact, one IAM role, one trigger. The recursion risk that justified
  two buckets cannot exist: nothing in this pipeline is triggered by S3 at all.
- The whole pipeline is one function call locally, so the end-to-end run in P2 needs no
  AWS at all — fixtures cover the transform, and the first S3 write happens in P3.
- A re-run for the same day is naturally idempotent, because it overwrites its own output.

**Harder — and this is the price of the decision:**

- **A transform bug is unrecoverable for the days it ran.** The source payload is gone
  once the invocation ends, and `chart.getTopTracks` accepts no date parameter
  (ADR-0006), so the day cannot be re-fetched. Under the superseded layout the fix was to
  re-run the transform against raw; there is no such fix now.
- Debugging a bad row means reasoning from curated data and logs, not from the payload
  that produced it.
- The transform must be correct *before* it runs in production, which raises what P2.4's
  tests have to cover. Test coverage is no longer a good practice here; it is the only
  remaining safety net.

**Reversal:** adding a raw tier back is cheap in code — one `put_object` before the
transform — but it converts the pipeline to ELT and supersedes this ADR. Data lost in the
meantime does not come back.
