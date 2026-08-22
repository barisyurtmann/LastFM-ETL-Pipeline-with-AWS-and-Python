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

# (connect, read). Split because the two fail for different reasons: a connect timeout
# means the host never answered, a read timeout means it accepted the connection and then
# went quiet. A single number hides which one happened. Never omit it — without a timeout
# requests waits forever and a Lambda dies on its own timeout with no useful log line.
DEFAULT_TIMEOUT: Final[tuple[float, float]] = (3.05, 10.0)

MAX_ATTEMPTS: Final = 4
MAX_BACKOFF_SECONDS: Final = 30

# Last.fm reports its real failure in the body, not the status line. These codes describe
# a condition that may clear on its own; every other code is permanent, and retrying a
# permanent failure only burns the rate limit.
#   8  operation failed      11  service offline
#   16 temporary error       29  rate limit exceeded
# 26 (suspended API key) is deliberately absent: retrying a suspended key makes it worse.
RETRYABLE_ERROR_CODES: Final[frozenset[int]] = frozenset({8, 11, 16, 29})

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})


class LastfmError(Exception):
    """Base class for every failure raised by this module."""


class LastfmAPIError(LastfmError):
    """The API answered, and the answer was an error document.

    Carries the Last.fm error code so callers can branch on it instead of parsing text.
    """

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Last.fm error {code}: {message}")
        self.code = code
        self.message = message


class LastfmTransientError(LastfmError):
    """A failure that may succeed if the same call is repeated later.

    This is the only exception tenacity retries. Raising it is a decision, not a
    description: see RETRYABLE_ERROR_CODES.
    """


@retry(
    # Only transient failures are retried. LastfmAPIError escapes on the first attempt —
    # a wrong API key does not become right on the fourth try.
    retry=retry_if_exception_type(LastfmTransientError),
    stop=stop_after_attempt(MAX_ATTEMPTS),
    # Full jitter: min(initial * 2**n + uniform(0, jitter), max). Without the random part
    # every client that failed at the same moment retries at the same moment.
    wait=wait_exponential_jitter(initial=1, max=MAX_BACKOFF_SECONDS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    # Without this, tenacity wraps the final failure in RetryError and the caller loses
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

    Retried by tenacity while it raises LastfmTransientError.

    Raises:
        LastfmTransientError: network failure, or a status/error code worth retrying.
        LastfmAPIError: the API returned a permanent error document.
        LastfmError: the response was not JSON at all.

    TODO(barış): implement in this order — the order is the lesson.
      1. session.get(BASE_URL, params=params, timeout=timeout), wrapping ONLY that call
         in try/except requests.RequestException -> raise LastfmTransientError(...) from exc.
      2. Decode the body BEFORE looking at the status: response.json() inside
         try/except ValueError. On failure raise LastfmError including
         response.status_code and response.text[:200] — a bare JSONDecodeError says
         "char 0" and nothing else.
      3. If "error" in payload: read code and message. Raise LastfmTransientError if the
         code is in RETRYABLE_ERROR_CODES, otherwise LastfmAPIError(code, message).
      4. Only now check response.status_code: LastfmTransientError if it is in
         RETRYABLE_STATUS_CODES, LastfmError if it is >= 400 with no error document.
      5. Return payload.
    """
    raise NotImplementedError


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

    TODO(barış): build the params dict and delegate to _request.
      - params: method="chart.getTopTracks", api_key (config.lastfm_api_key),
        format="json", limit, page. limit and page as str — requests would coerce ints,
        but being explicit keeps the request identical every time.
      - format="json" is not optional: without it the API returns XML with status 200.
      - reuse the caller's session if given, otherwise requests.Session() so the TCP
        handshake is not repeated per call.
      - log at INFO before the call: method, page, limit. Never log params — it holds
        the key. Use %s formatting, not f-strings: logging skips formatting entirely
        when the level is disabled.
    """
    raise NotImplementedError
