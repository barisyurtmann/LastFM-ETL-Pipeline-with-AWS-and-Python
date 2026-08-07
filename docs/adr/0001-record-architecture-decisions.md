# ADR-0001: Record architecture decisions

**Status:** Accepted
**Date:** 2026-08-07

## Context

This project is built incrementally as a learning exercise, across two machines and many
separate working sessions. Decisions made in one session are routinely forgotten by the
next: why the data lake lives under `/data/`, why raw payloads are stored untouched, why
Parquet rather than CSV.

Git history records *what* changed. It does not record what was considered and rejected,
or which constraint forced a choice. Commit messages are the wrong place for this — they
are read linearly and in the context of one diff, not consulted as reference material.

The project is also intended as a portfolio piece. A reviewer can read the code; they
cannot read the reasoning unless it is written down.

## Decision

We will record every non-obvious architectural decision as a numbered Markdown file in
`docs/adr/`, following the format defined in `docs/adr/README.md`.

An ADR is written when the decision meets both criteria:

1. It constrains future work — reversing it later would require changing multiple files.
2. A reasonable engineer could have chosen differently.

General knowledge that is not specific to this project (Git syntax, commit message
conventions, Python idioms) goes to `docs/notes/` instead, and is written in Turkish.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Long-form comments in the code | Decisions span multiple files; a comment has no natural home. Also drifts silently when the code moves. |
| A single `DECISIONS.md` file | Grows without bound, has no status field, and encourages editing past entries — which destroys the record of what we used to believe. |
| A wiki or external tool (Notion, Confluence) | Introduces a second sync mechanism next to Git. The repo is already synchronised across both machines; adding another system guarantees drift. |
| Nothing — rely on memory and commit messages | This is the current failure mode. It is the reason this ADR exists. |

## Consequences

**Easier:** resuming work after a gap; onboarding a reader; answering "why is it built
this way?" in an interview with a written record rather than a reconstruction.

**Harder:** every real decision now costs an extra ten minutes of writing. ADRs written
retroactively are worse than ADRs written at the moment of decision, so this cost cannot
be deferred without losing most of the value.

**Accepted risk:** the practice dies quietly if ADRs stop being written. The mitigation is
procedural, not technical — `docs/PROGRESS.md` is checked at the start of every session,
and an ADR is part of the definition of done for any step that involves a design choice.
