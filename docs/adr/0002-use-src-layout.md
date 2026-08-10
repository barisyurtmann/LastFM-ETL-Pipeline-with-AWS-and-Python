# ADR-0002: Use a src layout for the package

**Status:** Accepted
**Date:** 2026-08-10

## Context

Python resolves imports by scanning `sys.path` in order and taking the first match. The
first entry of that list is the current working directory in almost every common
invocation: `python -m x`, `python -c "..."`, the REPL, and pytest's default `prepend`
import mode all place the repository root on `sys.path`.

With a flat layout — the package directory sitting at the repository root — this means
`import lastfm_etl` resolves against the **source tree**, never against the installed
distribution. Tests, linters, and CI all exercise the source tree. The wheel that users
install is never imported during development.

The consequence is a class of packaging errors that no local check can catch: a
subpackage missing from the build configuration, a data file absent from the wheel, a
module excluded by a discovery rule. Everything is green locally and in CI; the failure
appears on first import after `pip install`.

This project targets AWS Lambda (step 9). A packaging error there surfaces as an
`ImportError` in CloudWatch after deployment — the most expensive place to find it.

A second, smaller force: every directory and `.py` file at the repository root becomes an
importable top-level name. A root-level `tests/` is importable as `tests`; a root-level
`logging.py` would shadow the standard library module of that name.

## Decision

We will place the package under `src/`, so the import path is
`src/lastfm_etl/__init__.py`, and the repository root contains no importable Python
package.

`src/` is not itself a package: it contains no `__init__.py`, is never added to
`sys.path`, and does not appear in any import statement. The installed package is
`lastfm_etl`, not `src.lastfm_etl`.

This makes an editable install (`pip install -e .`) a prerequisite for running tests
locally. That prerequisite is the point of the decision, not a side effect.

Package naming follows from the same reasoning: the distribution name is `lastfm-etl`
and the import name is `lastfm_etl`. A hyphen is legal in a distribution name and
illegal in a Python identifier — `import lastfm-etl` is a `SyntaxError`, not a
`ModuleNotFoundError`, and therefore cannot be caught at runtime.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Flat layout (`lastfm_etl/` at the repository root) | Tests import the source tree, so packaging configuration is never exercised. Errors surface at `pip install` time in production rather than at the first local test run. |
| Flat layout plus a CI job that installs the wheel and imports it | Recovers most of the safety, but only in CI and only for the checks explicitly written. The src layout enforces the same property locally and by construction. |
| Manipulating `sys.path` in `conftest.py` | Makes the import path depend on test configuration rather than on installation, which is the problem restated rather than solved. Also silently diverges from how the package behaves in production. |
| Namespace package with no `__init__.py` | Solves nothing here, and introduces silent directory merging when two directories share a name on `sys.path`. |

## Consequences

**Easier:** packaging errors surface at the first local test run. What is tested is
byte-for-byte what is shipped. The repository root stays free of importable names, so
stdlib shadowing and accidental top-level imports of `tests` become impossible.

**Harder:** the package must be installed before anything can import it. A fresh clone
cannot run `pytest` until `pip install -e .` has been run, and this must be documented in
the README (step 0.5) and encoded in CI (step 8.5). Contributors used to flat layouts
will hit `ModuleNotFoundError` and need to be told why.

**Accepted cost:** editable installs are a comparatively recent mechanism (PEP 660) and
their behaviour is backend-specific. Setuptools implements them with an import hook
rather than a simple path entry, which occasionally confuses IDE indexers and static
analysers. This is a known and tolerated rough edge.

**Deferred verification:** the decision cannot be fully validated until a virtual
environment exists (step 0.4). Until then only the TOML syntax and the directory
structure can be checked, not installability.
