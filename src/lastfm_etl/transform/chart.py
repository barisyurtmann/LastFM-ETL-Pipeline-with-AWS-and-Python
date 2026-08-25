"""Turn Last.fm chart payloads into the rows of the two curated tables.

The contract this module implements — columns, types, keys and the policy for unusable
rows — is `docs/SCHEMA.md`. When the two disagree, the document is the specification and
this file is the bug.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Final

logger = logging.getLogger(__name__)

# Last.fm sends "0" for a duration it does not know, not for a zero-length track.
UNKNOWN_DURATION: Final = 0


class TransformError(Exception):
    """Raised when a payload cannot be read at all, unlike a single unusable row."""


@dataclass(frozen=True, slots=True)
class ChartTables:
    """The two curated tables produced by one run, in chart order.

    A pair of named lists rather than a tuple: at the call site `tables.tracks` says
    what it holds and `tables[0]` does not.
    """

    tracks: list[dict[str, Any]]
    artists: list[dict[str, Any]]


def _text(value: Any) -> str | None:
    """Return a stripped, non-empty string, or None.

    This payload expresses "absent" three ways in the same field: a missing key, an
    empty string, and whitespace. Collapsing them here stops every caller from
    repeating it.
    """
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _to_int(value: Any) -> int | None:
    """Return the value as an int, or None when it is absent or not a number.

    Every numeric field in this payload arrives as a string, so this is not defensive
    coding — it is the actual type boundary of the pipeline.
    """
    text = _text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _rank(attr: dict[str, Any], index: int) -> int:
    """Return the chart position of the record at `index` within its page.

    Both numbers come from the response's own `@attr`, never from the page size we asked
    for: the server decides what a page holds, and one short page in the middle would
    otherwise shift every rank after it.

    Raises:
        TransformError: the page carried no readable @attr.
    """
    try:
        page = int(attr["page"])
        per_page = int(attr["perPage"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TransformError(
            f"rank cannot be derived from this @attr: {attr!r}"
        ) from exc
    return (page - 1) * per_page + index + 1


def _records(page: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
    """Return one page's @attr and its track list.

    Raises:
        TransformError: the page is not a chart payload. A page that cannot be read is
            not a bad row — every rank behind it would be wrong, so the run stops.
    """
    container = page.get("tracks")
    if not isinstance(container, dict):
        raise TransformError(f"payload carried no track container: {page!r}")

    attr = container.get("@attr")
    if not isinstance(attr, dict):
        raise TransformError(f"page carried no @attr: {container.keys()}")

    records = container.get("track")
    # Generated from XML, where a one-element list is indistinguishable from an object.
    if isinstance(records, dict):
        return attr, [records]
    if not isinstance(records, list):
        raise TransformError(f"unexpected track container: {type(records).__name__}")
    return attr, records


def transform_chart(
    pages: list[dict[str, Any]],
    *,
    snapshot_date: date | None = None,
    ingested_at: datetime | None = None,
) -> ChartTables:
    """Turn one run's page payloads into the rows of both curated tables.

    Both tables come out of a single pass, so every `tracks.artist_name` exists in
    `artists` by construction rather than by discipline. Parsing the same payload twice
    is how a foreign key silently starts pointing at nothing.

    Rows whose key components are unusable are dropped and counted, not repaired: a row
    with a null key survives every later check, and a missing row does not. The policy
    per field is in `docs/SCHEMA.md`.

    Both timestamps are parameters rather than calls to now(), so one run can produce
    the same output twice and a test never depends on the clock.

    Raises:
        TransformError: a page carried no readable track list or no readable @attr, or
            ingested_at was naive.
    """
    snapshot_date = snapshot_date or datetime.now(UTC).date()
    ingested_at = ingested_at or datetime.now(UTC)
    if ingested_at.tzinfo is None:
        raise TransformError(
            "ingested_at must be timezone-aware; a naive value would be written as if "
            "it were UTC and no reader could tell"
        )

    # Serialised once, not per row: JSON has no date type, so both leave as strings.
    snapshot = snapshot_date.isoformat()
    ingested = ingested_at.astimezone(UTC).isoformat().replace("+00:00", "Z")

    tracks: list[dict[str, Any]] = []
    artists: dict[str, dict[str, Any]] = {}
    seen: set[tuple[str, str]] = set()
    dropped = 0

    for page in pages:
        attr, records = _records(page)

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                dropped += 1
                logger.warning("dropped a non-object row at index %s", index)
                continue

            artist = record.get("artist")
            artist = artist if isinstance(artist, dict) else {}
            artist_name = _text(artist.get("name"))
            track_name = _text(record.get("name"))
            if artist_name is None or track_name is None:
                dropped += 1
                logger.warning(
                    "dropped a row with no usable key: artist=%r track=%r",
                    artist_name,
                    track_name,
                )
                continue

            playcount = _to_int(record.get("playcount"))
            listeners = _to_int(record.get("listeners"))
            if playcount is None or listeners is None:
                dropped += 1
                logger.warning(
                    "dropped %r by %r: playcount=%r listeners=%r",
                    track_name,
                    artist_name,
                    record.get("playcount"),
                    record.get("listeners"),
                )
                continue

            key = (artist_name, track_name)
            if key in seen:
                dropped += 1
                logger.warning(
                    "dropped a repeat of %r by %r; the earlier rank wins",
                    track_name,
                    artist_name,
                )
                continue
            seen.add(key)

            duration = _to_int(record.get("duration"))
            tracks.append(
                {
                    "snapshot_date": snapshot,
                    "rank": _rank(attr, index),
                    "track_name": track_name,
                    "artist_name": artist_name,
                    "playcount": playcount,
                    "listeners": listeners,
                    "duration_seconds": (
                        None if duration == UNKNOWN_DURATION else duration
                    ),
                    "track_mbid": _text(record.get("mbid")),
                    "track_url": _text(record.get("url")),
                    "ingested_at": ingested,
                }
            )

            # setdefault, not an if: the first occurrence of an artist wins, and the
            # first occurrence is the one with the best rank because pages are ordered.
            artists.setdefault(
                artist_name,
                {
                    "snapshot_date": snapshot,
                    "artist_name": artist_name,
                    "artist_mbid": _text(artist.get("mbid")),
                    "artist_url": _text(artist.get("url")),
                    "ingested_at": ingested,
                },
            )

    logger.info(
        "%s tracks, %s artists, %s rows dropped",
        len(tracks),
        len(artists),
        dropped,
    )
    return ChartTables(tracks, list(artists.values()))
