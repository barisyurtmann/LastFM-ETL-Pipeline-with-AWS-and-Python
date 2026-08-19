"""Application configuration, loaded once from the environment."""

import logging
import os
from dataclasses import dataclass, fields
from functools import lru_cache
from typing import Final

from dotenv import find_dotenv, load_dotenv

# Module-level logger: no setup, no side effect. The application configures handlers.
logger = logging.getLogger(__name__)

# Every name here must be present and non-empty before the pipeline may start
REQUIRED_ENV_VARS: Final[tuple[str, ...]] = ("LASTFM_API_KEY",)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing, empty or invalid."""


@dataclass(frozen=True, slots=True, repr=False)
class Config:
    """Validated runtime configuration.

    Frozen because configuration is a reading taken at startup, not a variable.
    """

    lastfm_api_key: str

    def __post_init__(self) -> None:
        # Backstop invariant: no code path, not even a test, may build an invalid Config
        blank = [f.name for f in fields(self) if not getattr(self, f.name).strip()]
        if blank:
            raise ConfigError(f"Config fields must not be empty: {', '.join(blank)}")

    def __repr__(self) -> str:
        # The generated dataclass repr prints every field; this one must never leak the key
        return f"Config(lastfm_api_key='***{self.lastfm_api_key[-4:]}')"


@lru_cache(maxsize=1)
def load_config() -> Config:
    """Read, validate and cache configuration, failing loudly if anything is missing."""
    dotenv_path = find_dotenv()
    if dotenv_path:
        # override=False keeps real environment variables winning: Lambda has no .env file
        load_dotenv(dotenv_path, override=False)
        logger.debug("loaded environment file %s", dotenv_path)
    else:
        logger.debug("no .env file found, using the process environment only")

    values = {name: os.environ.get(name, "").strip() for name in REQUIRED_ENV_VARS}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ConfigError(
            f"Missing or empty environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

    config = Config(lastfm_api_key=values["LASTFM_API_KEY"])
    logger.debug("configuration loaded: %s", config)  # masked repr, safe to log
    return config
