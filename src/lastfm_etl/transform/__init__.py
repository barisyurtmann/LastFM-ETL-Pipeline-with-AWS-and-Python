"""Transformation layer: turn raw payloads into the curated tables.

Nothing in this layer talks to the network or to storage. It takes payloads produced by
`extract` and returns plain rows; writing them is `load`'s job. The dependency direction
stays one-way: `transform` imports nothing from `extract` or `load`, so the tables can
be built from a live run, a fixture, or a hand-written dict with equal ease.

The re-exports below are the layer's public surface. `ChartTables` is part of it because
callers unpack it; `TransformError` is part of it because callers catch it. Everything
else in `chart` is private to the module.
"""

from lastfm_etl.transform.chart import (
    ChartTables,
    TransformError,
    transform_chart,
)

__all__ = [
    "ChartTables",
    "TransformError",
    "transform_chart",
]
