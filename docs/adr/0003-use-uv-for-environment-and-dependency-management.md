# ADR-0003: Use uv for environment and dependency management

**Status:** Accepted
**Date:** 2026-08-10

## Context

ADR-0002 committed this project to a `src/` layout. A consequence of that layout is that
`src/` is not on `sys.path`, so the package cannot be imported without being installed.
Step 0.3 was therefore closed with its installability unverified — no environment existed
to install into. Creating that environment is step 0.4.

The project is developed on two machines (home and work) and is synchronised through git.
`.venv/` is git-ignored, so each machine rebuilds its environment from the repository.
Nothing currently guarantees that the two rebuilds produce the same package versions:
`pyproject.toml` declares `dependencies = []` today, and even once entries are added,
a version range — or an exact pin — constrains only direct dependencies. Transitive
dependencies remain free to drift between machines and over time.

Later roadmap steps depend on this: step 8.5 runs the test suite in CI, 8.6 explicitly
requires dependency pinning with a lock file and a dev/prod split, and 8.7 builds a
Docker image. Each of those needs a reproducible environment definition, not an ad-hoc one.

Python's standard library provides `venv` (PEP 405) and pip provides installation, but
pip has no lock file. `pip freeze` records installed versions without hashes, without
recording why a package is present, and without separating development from runtime
dependencies.

## Decision

We will use **uv** in project mode for environment creation, dependency resolution and
dependency locking.

Concretely:

- `uv venv` creates `.venv/`
- `uv add` / `uv add --dev` declare dependencies in `pyproject.toml`, using PEP 735
  dependency groups for development tooling
- `uv.lock` is committed and is the source of truth for what is installed
- `uv sync` reconstructs an environment from the lock file; CI uses `uv sync --frozen`
- `pyproject.toml` continues to declare abstract version ranges; exact versions live only
  in the lock file

The build backend stays `setuptools`, as chosen in step 0.3. uv is a package manager and
resolver, not a build backend, so the two decisions are independent.

## Alternatives considered

| Option | Why rejected |
|---|---|
| `venv` + `pip` only | No lock file. Reproducibility between the two development machines would rest on transitive dependencies happening to resolve identically. Step 8.6 would force a lock tool to be chosen anyway, so this defers the decision rather than avoiding it. |
| `venv` + `pip` now, migrate to uv later | Introduces a third tool: `venv`+`pip`, then `pip-tools` for locking in 8.6, then uv. The stated benefit — learning the underlying mechanism — does not hold, because uv produces the same `.venv/` and the same `pyvenv.cfg` and relies on the same `PATH` behaviour. Nothing is hidden that `venv` would have exposed. |
| `pip-tools` (`pip-compile`) | Solves locking only. Environment creation, Python version management and the dev/prod split remain separate concerns handled by separate tools. |
| Poetry | Mature and widely used, but historically diverged from `pyproject.toml` standards and is substantially slower to resolve. Its position has weakened as PEP 621 and PEP 735 moved the ecosystem toward standard metadata. |
| Conda | Solves a different problem — non-Python binary dependencies (CUDA, compiled scientific stacks). This project has no such requirement, and Conda would add an environment model incompatible with the Lambda packaging planned for step 9.5. |

## Consequences

**Easier**

- Step 8.6 (dependency pinning, dev/prod split) is largely satisfied by `uv.lock` and
  PEP 735 groups rather than requiring new tooling.
- CI (8.5) and Docker builds (8.7) become significantly faster, and `uv sync --frozen`
  makes them fail loudly if the lock file is stale rather than silently installing
  something else.
- `uv sync` removes packages absent from the lock file, so "what is in my environment"
  has a definite answer. `pip install -r` never removes anything.
- Python version drift between the two machines is manageable through
  `uv python install`, without adding pyenv.

**Harder / accepted costs**

- uv is not part of the standard library. A new contributor must install it before
  anything else works; the README must state this as a prerequisite.
- `uv.lock` is a uv-specific format, not the PEP 751 standard (`pylock.toml`). Tools that
  consume lock files directly may not read it. Mitigation: `uv export` produces
  `requirements.txt` or `pylock.toml` on demand.
- uv is a young tool (first released 2024) under rapid development by a single company.
  Its behaviour and CLI surface may change faster than a stdlib tool would.
- Because `uv run` manages the environment implicitly, it is possible to use this project
  without ever understanding `PATH`, `pyvenv.cfg` or `sys.prefix`. This is a real risk for
  a learning project; it is mitigated by `docs/notes/08-virtual-environments-and-uv.md`,
  which documents the underlying mechanism independently of the tool.

**Reversibility**

Low cost. uv consumes standard `pyproject.toml` metadata and does not require
tool-specific dependency declarations. Abandoning uv means deleting `uv.lock` and
choosing another resolver; `pyproject.toml` is unaffected.
