"""Extraction layer: read from external sources, return payloads untouched.

Nothing in this layer reshapes data. Flattening belongs to `transform`, persistence to
`load`. The dependency direction is one-way: `extract` imports `config`, and nothing
imports `extract` except the entrypoint.

The re-exports below are the layer's public surface. Callers write
`from lastfm_etl.extract import fetch_top_tracks` and stay unaware of which module inside
the package holds it, so files can be renamed or split without touching call sites.
Kept deliberately small: every name here is imported at package-import time, and on a
Lambda cold start that time is billed.
"""

from lastfm_etl.extract.api import (
    LastfmAPIError,
    LastfmError,
    LastfmTransientError,
    fetch_top_tracks,
)

__all__ = [
    "LastfmAPIError",
    "LastfmError",
    "LastfmTransientError",
    "fetch_top_tracks",
]
