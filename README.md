# Last.fm ETL Pipeline

A batch ETL pipeline that extracts listening data from the Last.fm API, stores it as
immutable raw JSON, transforms it into partitioned Parquet, and is designed to run on AWS
(S3, Lambda, EventBridge, Athena).

This is a learning project. Every architectural decision is recorded in
[`docs/adr/`](docs/adr/) with its alternatives and trade-offs.

## Status

**Work in progress — step 0 of 9 (repository setup).**

The pipeline is not runnable yet: no extract, transform or load code exists.
Current position: [`docs/PROGRESS.md`](docs/PROGRESS.md) ·
Plan: [`docs/ROADMAP.md`](docs/ROADMAP.md)

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — used for environment and dependency management.
  This project does not use `pip` directly (see [ADR-0003](docs/adr/0003-use-uv-for-environment-and-dependency-management.md))
- **git**

Install uv:

```bash
# Windows
winget install --id=astral-sh.uv -e

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```


## Setup

```bash
git clone https://github.com/barisyurtmann/LastFM-ETL-Pipeline-with-AWS-and-Python.git
cd LastFM-ETL-Pipeline-with-AWS-and-Python

# Create .venv/ and install exactly what uv.lock specifies
uv sync

# Copy the environment template and fill in your Last.fm API key
cp .env.example .env
```

Verify the installation:

```bash
uv run python -c "import lastfm_etl; print('ok')"
```


## Project structure

```
.
├── src/lastfm_etl/     # the package (src layout — see ADR-0002)
├── docs/               # project documentation (see below)
├── pyproject.toml      # project metadata, dependencies, build config
├── uv.lock             # exact resolved versions, committed for reproducibility
└── .env.example        # template for required environment variables
```


`data/` is created at runtime and is git-ignored. Its layout mirrors the target S3
structure (`raw/`, `curated/`) so that moving to AWS does not change any path logic.

## Documentation

| Path | Contents |
|---|---|
| [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) | Goals, constraints, target architecture |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | The plan: 9 steps, sub-steps, definitions of done |
| [`docs/PROGRESS.md`](docs/PROGRESS.md) | Current position — single source of truth |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |
| [`docs/notes/`](docs/notes/) | Learning notes, one per sub-step (written in Turkish) |
| [`docs/TOOLING.md`](docs/TOOLING.md) | Data tooling landscape: layers, selection criteria, cost models (written in Turkish) |

Three separate files exist by design: **contract ≠ plan ≠ position.** Keeping the same
information in two places guarantees drift.