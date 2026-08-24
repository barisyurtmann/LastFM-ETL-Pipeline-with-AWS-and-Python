# ADR-0014: Use tenacity for retry instead of a hand-written loop

**Status:** Accepted
**Date:** 2026-08-24

## Context

`extract/api.py` must survive transient failures: a dropped connection, a 5xx from a
gateway, and Last.fm error codes 8, 11, 16 and 29, which describe conditions that may clear
on their own. Ignoring them means a scheduled run fails permanently because of a two-second
outage.

Retry has two separate questions, and conflating them is the usual mistake:

- **When** to retry — which failures are worth repeating. This is domain knowledge. Last.fm
  answers 200 with `{"error": 10}` for a bad key, and no generic library knows that the
  error lives in the body.
- **How** to retry — attempt counting, sleeping, exponential growth, jitter, logging each
  wait, and re-raising the original exception at the end. This is mechanism, identical in
  every project.

A hand-written version of the *how* is roughly twenty lines and has known failure modes:
sleeping after the final attempt, omitting jitter so every client retries in lockstep,
retrying silently so a degraded backend looks merely slow, and losing the original
exception behind a generic one.

The project already accepts `requests` as a runtime dependency, and the packaged Lambda
will carry its dependencies in a layer (ROADMAP P3.1), so the marginal cost of one more
small pure-Python package is a layer size increase, not a new mechanism.

## Decision

We will use **tenacity** for the mechanism, and keep the taxonomy in our own code.

`_request` carries `@retry(...)` configured with:

| Setting | Value | Reason |
|---|---|---|
| `retry` | `retry_if_exception_type(LastfmTransientError)` | One type is retried. Deciding which failures raise it stays ours |
| `stop` | `stop_after_attempt(4)` | 1 attempt + 3 retries, bounded well under the Lambda timeout |
| `wait` | `wait_exponential_jitter(initial=1, max=30)` | Exponential growth with a random component, so clients that failed together do not retry together |
| `before_sleep` | `before_sleep_log(logger, WARNING)` | A silent retry hides a degraded backend for months |
| `reraise` | `True` | Without it the final failure arrives wrapped in `RetryError` and the caller loses the Last.fm error code it needs |

The classification — `RETRYABLE_ERROR_CODES`, `RETRYABLE_STATUS_CODES`, and the ordering
that reads the body before the status — remains hand-written in `api.py`. Code 26
(suspended key) is deliberately excluded.

## Alternatives considered

| Option | Why rejected |
|---|---|
| **Hand-written retry loop** | The stronger teaching option, and the one that shows what the library removes. Rejected on the merits: correct exponential backoff with full jitter, a bounded final attempt, per-wait logging and exception re-raise is twenty lines that are load-bearing and easy to get subtly wrong. The failure mode of getting it wrong is not a crash but a pipeline that is quietly worse under load |
| **`urllib3.util.Retry` mounted on an `HTTPAdapter`** | The natural `requests`-native answer, and it handles connection errors and status codes without any decorator. It cannot help here: Last.fm's dominant failure — an error document returned with status 200 — is invisible at the transport layer, so the domain retry logic would still have to exist alongside it. Two retry mechanisms in one call path is worse than one |
| **`backoff`** | Equivalent feature set and a smaller API. tenacity was chosen for its explicit, composable strategy objects (`stop_*`, `wait_*`, `retry_*`), which name the four questions separately and make the configuration read as documentation |
| **`stamina`** | A thin opinionated wrapper over tenacity with better defaults. Sound, but it hides the very knobs this project exists to understand |
| **No retry at all** | Acceptable only if the scheduler retries the whole run. EventBridge does not do so by default (ROADMAP P3.3), so a transient failure would become a missing day — and ADR-0006 records that a missed day cannot be backfilled |

## Consequences

**Easier:**

- The retry policy is declared, not implemented. Changing the attempt budget or the backoff
  ceiling is a constant, and the change is visible in a diff as a value rather than as
  rewritten control flow.
- Jitter, bounded growth and re-raise semantics are correct without being maintained here.
- `before_sleep_log` makes retries observable in CloudWatch (P3.4) with no extra code.

**Harder:**

- One more runtime dependency to package into the Lambda layer, and one more thing that can
  break on a major version bump. Its version is pinned in `uv.lock`.
- The decorated function's body can execute up to four times per call. Any side effect
  placed inside `_request` — a write, a counter, a file — happens up to four times. This is
  a standing constraint on P2.2: the S3 write must not live inside the retried function.
- The retry configuration is evaluated once, at import time. Varying it per call would
  require a second wrapper, which is not needed today and would be a new decision.
- Learning cost is deferred, not avoided: the mechanism tenacity replaces is now understood
  from its configuration rather than from having written it. `docs/annotated/src/lastfm_etl/extract/api.py`
  §0.4 and the `@retry` block exist to close that gap.

**Standing:** tenacity is a popular library, not a standard. `backoff`, `stamina` and
`urllib3.util.Retry` all appear in production Python. The deciding factor was that the
mechanism is generic while the taxonomy is not, and only the generic half was delegated.
