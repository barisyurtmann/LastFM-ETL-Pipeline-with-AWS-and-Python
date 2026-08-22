# ADR-0011: Deploy all resources in eu-central-1

**Status:** Accepted
**Date:** 2026-08-22

## Context

The pipeline needs an AWS Region before any resource can exist. The choice is forced now
because S3 buckets were created in step P1.3, and several properties of that choice cannot
be undone:

- A bucket's Region is fixed at creation. There is no "move bucket" operation; relocating
  means creating a new bucket and copying every object.
- Glue Data Catalog databases are regional. A Crawler must run in the same Region as the
  catalog it writes to.
- Athena reads the catalog of the Region it runs in, and its query-results bucket must be
  in that same Region.
- S3 can be read across Regions, but cross-Region requests add latency and inter-Region
  data transfer charges to every call.

In practice this means the Region is not a per-service setting but a single decision that
binds S3, Lambda, EventBridge, Glue and Athena together.

Constraints that apply here:

- The operator works from Istanbul (UTC+3). AWS has no Region in Türkiye.
- Every service in the architecture (S3, Lambda, EventBridge, Glue, Athena) must be
  available in the chosen Region — not all Regions carry all services.
- The workload is a nightly batch job. Human-perceived latency is irrelevant; only console
  and CLI responsiveness are affected.
- This is a personal learning account with a $5/month budget alarm. Regional price
  differences are measurable but small at this scale.

## Decision

We will create every resource in this project in **eu-central-1 (Frankfurt)**.

The Region is recorded in `~/.aws/config` as the default (`aws configure`, step P1.2), so
CLI calls and `boto3` clients inherit it without the value being repeated in code.

## Alternatives considered

| Option | Why rejected |
|---|---|
| **us-east-1** (N. Virginia) | Cheapest Region and the first to receive new features, but the farthest from the operator, and it places EU-originated data in the US for no benefit. Its size also makes it the Region most often named in large-scale outage reports |
| **eu-west-1** (Ireland) | Full service coverage and occasionally lower prices, but geographically farther than Frankfurt with nothing gained in return |
| **eu-south-1** (Milan) | Comparable distance, but a smaller Region with slower feature rollout and no compensating advantage |
| **me-central-1** (UAE) | Nominally "closer" politically but farther in network terms, with narrower service coverage |
| **Per-service Regions** | Would incur cross-Region transfer costs on every object read and break the Glue/Athena co-location requirement |

## Consequences

**Easier:**

- One Region for every resource: no cross-Region transfer charges, no co-location bugs
  where a Crawler cannot see its data.
- Lowest network latency to the operator among Regions with full service coverage.
- Data stays in the EU, which is the defensible default for data originating there.

**Harder:**

- eu-central-1 is priced slightly above us-east-1 for S3 storage and Lambda invocations.
  At this project's volume the difference is cents per month, but the ordering is real and
  would matter at scale.
- New AWS features and services reach us-east-1 first, sometimes by several months.
- Reversing this decision is genuine work: creating replacement buckets, copying objects,
  recreating the Glue database and Crawler, and resetting the Athena query-results
  location. This is the reason the choice is recorded as an ADR rather than a commit
  message.
- The Region now lives in two places: `~/.aws/config` on each machine, and the Regions the
  buckets were physically created in. A machine configured with a different default Region
  will silently address a different endpoint. `aws configure list` is the diagnostic.
