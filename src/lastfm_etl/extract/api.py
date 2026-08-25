"""Fetch chart data from the Last.fm API.

This module owns one thing: turning a Last.fm API method call into either a raw JSON
payload or a typed exception. It does not reshape, flatten or persist anything — what it
returns is what the API sent, so the raw layer (P2.2) can store it untouched.
"""

from __future__ import annotations

import logging
from typing import Any, Final

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from lastfm_etl.config import Config

logger = logging.getLogger(__name__)

BASE_URL: Final = "http://ws.audioscrobbler.com/2.0/"
TOP_TRACKS_METHOD: Final = "chart.getTopTracks"

# (connect, read): a connect timeout means the host never answered, a read timeout means
# it answered and then went quiet. Never omit — without it requests waits forever.
DEFAULT_TIMEOUT: Final[tuple[float, float]] = (3.05, 10.0)

MAX_ATTEMPTS: Final = 4
MAX_BACKOFF_SECONDS: Final = 30

# Last.fm reports its real failure in the body, not the status line. Only these codes
# describe a condition that may clear on its own; 26 (suspended key) is deliberately
# absent, because retrying a suspended key makes it worse.
RETRYABLE_ERROR_CODES: Final[frozenset[int]] = frozenset({8, 11, 16, 29})

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})

# Deliberately below TARGET_TRACK_COUNT so the pagination path runs on every
# execution. A loop that makes a single pass is untested code that first runs on the
# day it matters.
DEFAULT_PAGE_SIZE: Final = 50
TARGET_TRACK_COUNT: Final = 100

# Never expected to bind: 100 tracks at 50 a page is two calls. It exists so a server
# that answers without making progress ends the loop instead of the Lambda timeout.
MAX_PAGES: Final = 10


class LastfmError(Exception):
    """Base class for every failure raised by this module."""


class LastfmAPIError(LastfmError):
    """The API answered, and the answer was an error document."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Last.fm error {code}: {message}")
        self.code = code
        self.message = message


class LastfmTransientError(LastfmError):
    """A failure that may succeed if the same call is repeated later."""


@retry(
    retry=retry_if_exception_type(LastfmTransientError),
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential_jitter(initial=1, max=MAX_BACKOFF_SECONDS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    # Without this the final failure arrives wrapped in RetryError and the caller loses
    # the Last.fm error code it needs to act on.
    reraise=True,
)
def _request(
    session: requests.Session,
    method: str,
    params: dict[str, str],
    *,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Perform one HTTP call and return the decoded payload.

    Raises:
        LastfmTransientError: network failure, or a status/error code worth retrying.
        LastfmAPIError: the API returned a permanent error document.
        LastfmError: the response was not JSON, or carried a bad status and no error
            document.
    """
    try:
        response = session.get(BASE_URL, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise LastfmTransientError(f"{method}: request failed: {exc}") from exc

    try:
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        # A gateway in front of the API answers 5xx with HTML, so the decode failure
        # alone would call a temporary outage permanent.
        if response.status_code in RETRYABLE_STATUS_CODES:
            raise LastfmTransientError(
                f"{method}: HTTP {response.status_code} with a non-JSON body"
            ) from exc
        raise LastfmError(
            f"{method}: HTTP {response.status_code} returned a non-JSON body: "
            f"{response.text[:200]!r}"
        ) from exc

    # Checked before the status, because an invalid API key arrives with status 200.
    if "error" in payload:
        try:
            code = int(payload["error"])
        except (TypeError, ValueError) as exc:
            raise LastfmError(f"{method}: unreadable error document: {payload!r}") from exc
        message = str(payload.get("message", ""))
        if code in RETRYABLE_ERROR_CODES:
            raise LastfmTransientError(f"{method}: Last.fm error {code}: {message}")
        raise LastfmAPIError(code, message)

    # Backstop: valid JSON, no error document, but a status that still means failure.
    if response.status_code in RETRYABLE_STATUS_CODES:
        raise LastfmTransientError(f"{method}: HTTP {response.status_code}")
    if response.status_code >= 400:
        raise LastfmError(
            f"{method}: HTTP {response.status_code} with no error document"
        )

    return payload


def _track_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the track list inside a chart payload, leaving the payload untouched.

    Reading is not reshaping: the caller needs a count, and the payload it stores must
    stay exactly as the API sent it.

    Raises:
        LastfmError: the payload did not carry a readable track list.
    """
    tracks = payload.get("tracks")
    if not isinstance(tracks, dict) or "track" not in tracks:
        raise LastfmError(
            f"{TOP_TRACKS_METHOD}: payload carried no track list: {payload!r}"
        )

    records = tracks["track"]
    # This JSON is generated from XML, so a one-element list arrives as a bare object.
    if isinstance(records, dict):
        return [records]
    if not isinstance(records, list):
        raise LastfmError(
            f"{TOP_TRACKS_METHOD}: unexpected track container: {type(records).__name__}"
        )
    return records


def fetch_top_tracks(
    config: Config,
    *,
    limit: int = 100,
    page: int = 1,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Return one page of ``chart.getTopTracks`` exactly as the API sent it.

    The payload is deliberately not reshaped: the raw layer stores this verbatim, and
    ``@attr`` (page, perPage, total) must survive because rank is derived from it.
    """
    params = {
        "method": TOP_TRACKS_METHOD,
        "api_key": config.lastfm_api_key,
        # Not optional: without it the API answers with XML and status 200.
        "format": "json",
        "limit": str(limit),
        "page": str(page),
    }

    # %s, not an f-string: logging skips formatting when the level is disabled. params is
    # never logged — it carries the API key.
    logger.info("fetching %s page=%s limit=%s", TOP_TRACKS_METHOD, page, limit)

    return _request(session or requests.Session(), TOP_TRACKS_METHOD, params)


def fetch_top_tracks_pages(
    config: Config,
    *,
    target: int = TARGET_TRACK_COUNT,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = MAX_PAGES,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Return whole page payloads until ``target`` tracks have been seen.

    Pages come back verbatim and unmerged: rank is derived from ``@attr`` (page,
    perPage) plus a record's position inside its page, so merging would destroy it.

    The loop stops on the number of records actually received, never on arithmetic over
    ``page_size``. Last.fm may answer with fewer records than requested and reports no
    error when it does, so a computed page count would end the run short and silently.

    Returns:
        One element per page, in request order. The total may exceed ``target``;
        trimming belongs to the transform layer, which is allowed to reshape.

    Raises:
        LastfmError: a page carried no readable track list.
        LastfmAPIError: the API returned a permanent error document.
        LastfmTransientError: a retryable failure outlived every attempt.
    """
    # One session for every page: the connection pool only pays off when the same
    # object is reused, and fetch_top_tracks would otherwise open a fresh one per call.
    session = session or requests.Session()

    pages: list[dict[str, Any]] = []
    collected = 0

    for page in range(1, max_pages + 1):
        payload = fetch_top_tracks(config, limit=page_size, page=page, session=session)
        records = _track_records(payload)

        if not records:
            logger.info("page %s carried no tracks, stopping early", page)
            break

        pages.append(payload)
        collected += len(records)

        if collected >= target:
            break
    else:
        # Reached only when no break ran: the ceiling bound before the target was met.
        logger.warning(
            "stopped at the %s page ceiling with %s of %s tracks",
            max_pages,
            collected,
            target,
        )

    logger.info("collected %s tracks across %s pages", collected, len(pages))
    return pages
