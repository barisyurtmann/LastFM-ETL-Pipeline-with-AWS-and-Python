# ADR-0004: Store recorded API payloads as test fixtures

**Status:** Accepted
**Date:** 2026-08-11

## Context

Step 1 of the roadmap produces knowledge, not code: the real shape of the Last.fm
response. Every downstream decision — the target schema (1.7), the data grain (1.6),
the partition key (4.2), the Pydantic models (5.2) — is derived from that shape. Those
discussions need the payload available repeatedly, and the Last.fm rate limit is roughly
five requests per minute, so re-fetching during design work is impractical.

Step 7.2 needs the same payload for a different reason. The completion criteria for
step 7 require the test suite to pass with no network connection and with no `.env`
present, and require test data to be derived from a real response rather than
hand-written. A recorded payload satisfies both.

This creates a single artefact with two audiences: a human reading it as documentation,
and `pytest` reading it as test input. The roadmap left the location open — `tests/fixtures/`
or `docs/samples/` — precisely because of this dual purpose.

Two further facts shaped the format decision. The file will be committed and will change
over time as the API evolves, so `git diff` readability matters. And the raw layer
(step 4) has the opposite requirement: its completion criteria demand byte-level
comparison with what the API returned, which forbids any reformatting.

## Decision

We will record real API responses as JSON files under **`tests/fixtures/lastfm/`**, and
treat that directory as the single location for them.

Concretely:

- Both success and error responses are recorded. Error payloads are as valuable as
  successful ones, because the error path is what step 3 is built around.
- Files are stored **pretty-printed** (`python -m json.tool --no-ensure-ascii`), not as
  the raw single-line response body.
- Documentation references these files by path and does not reproduce their contents.
- Naming follows `<method>_<scenario>.json` for method-specific payloads
  (`chart_gettoptracks_success.json`) and `error_<code>_<meaning>.json` for error
  payloads (`error_10_invalid_api_key.json`), since a given error code is returned
  identically regardless of the method called.
- Method names in filenames are lowercased and dot-free, matching the S3 path convention
  already recorded in `PROJECT_CONTEXT.md` §4 (`method=chart_gettoptracks`).

This decision governs fixtures only. The raw layer defined in step 4 keeps the opposite
rule — bytes are preserved exactly as received — because its purpose is replay, not
inspection.

## Alternatives considered

| Option | Why rejected |
|---|---|
| `docs/samples/` | Nothing executes documentation. A file that no code reads can be moved, renamed or deleted without anything failing. Under `tests/`, the path is exercised by the test suite, so its existence and location are verified automatically on every run. |
| Both locations, one copy each | Two copies of the same fact drift. The realistic failure is mundane: a test breaks, the fixture is updated, the documentation copy is forgotten, and months later the schema is reviewed against a stale file. Nothing reports this, because documentation is not tested. The project already applies this principle to `PROJECT_CONTEXT.md` / `ROADMAP.md` / `PROGRESS.md`. |
| Store the raw single-line body | A one-line JSON file produces a one-line diff. When a field changes, git reports that the line changed without showing which field. For a file whose purpose is to make schema change visible, this defeats the purpose. |
| Generate fixtures from a recording library (VCR / `responses`) | Cassette formats add a layer between the file and the reader, and the file stops being readable as plain JSON. The value here is that a human can open the fixture during schema design. Worth revisiting in step 7.5 for the HTTP mocking layer specifically. |
| Fetch live data in tests | Violates the step 7 completion criteria: tests would require network access and an API key, would consume the rate limit, and would turn an unrelated API outage into a red CI build. |

## Consequences

**Easier**

- Schema design (1.5–1.7) proceeds without further API calls, keeping the rate limit
  available for the rate-limit measurement in 1.8.
- Step 7.2 has its test data ready before any test code exists.
- `git diff` on a fixture shows exactly which field changed, making an API change
  visible during review rather than at runtime.
- The error payloads recorded in 1.3 give step 3 concrete cases to build the exception
  hierarchy against, instead of hypothetical ones.

**Harder / accepted costs**

- A fixture is a frozen snapshot. It cannot detect that the live API has changed; it only
  makes the change visible once someone re-records. Detecting drift automatically is a
  separate mechanism — Pydantic validation at the transform boundary (5.2) catches it at
  runtime, and a contract test could catch it earlier, but neither is provided by this
  decision.
- Pretty-printing means the file is not byte-identical to the response. Number
  representation is normalised and original whitespace is lost. This is acceptable here
  and unacceptable in the raw layer; the difference in rules between the two locations
  must be documented, or someone will eventually apply the wrong one.
- Fixtures must be refreshed deliberately. A stale fixture makes tests pass against a
  contract the API no longer honours — a green suite that proves nothing.
- Recording responses risks committing secrets if a payload ever echoes request
  parameters. This was checked with `grep -rn "api_key" tests/` and must be rechecked
  whenever a new fixture is added.

**Reversibility**

High. The files are plain JSON; moving them means changing a path constant in the test
suite. The format decision is likewise reversible, since the raw response can be
reconstructed by re-fetching.
