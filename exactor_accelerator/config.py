"""
Exactor Accelerator — Centralized Configuration

Provides a single entry point to configure API tokens for:
- EXACTOR Core engine (exactor.tech)
- TypeSafe Jev AI
- DeepSeek LLM Explainer

Tokens can be set via:
1. Environment variables (EXACTOR_CORE_TOKEN, JEV_API_KEY, DEEPSEEK_API_KEY)
2. Programmatic call: exactor_accelerator.configure(exactor_core_token="...")
3. A .env file loaded automatically at import time
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("exactor_accelerator.config")

# ---------------------------------------------------------------------------
# Global token store (module-level singleton)
# ---------------------------------------------------------------------------

_ENV_EXACTOR_CORE_TOKEN = "EXACTOR_CORE_TOKEN"
_ENV_EXACTOR_API_KEY = "EXACTOR_API_KEY"  # legacy alias
_ENV_EXACTOR_BASE_URL = "EXACTOR_BASE_URL"
_ENV_JEV_API_KEY = "JEV_API_KEY"
_ENV_TYPESAFE_API_KEY = "TYPESAFE_API_KEY"  # legacy alias
_ENV_DEEPSEEK_API_KEY = "DEEPSEEK_API_KEY"
_ENV_DEEPSEEK_BASE_URL = "DEEPSEEK_BASE_URL"
_ENV_DEEPSEEK_MODEL = "DEEPSEEK_MODEL"


class _Config:
    """Internal singleton holding resolved configuration values."""

    __slots__ = (
        "exactor_core_token",
        "exactor_base_url",
        "jev_api_key",
        "deepseek_api_key",
        "deepseek_base_url",
        "deepseek_model",
    )

    def __init__(self):
        self.exactor_core_token: Optional[str] = None
        self.exactor_base_url: str = "https://exactor.tech"
        self.jev_api_key: Optional[str] = None
        self.deepseek_api_key: Optional[str] = None
        self.deepseek_base_url: str = "https://api.deepseek.com"
        self.deepseek_model: str = "deepseek-chat"
        self._load_from_env()

    # --- private helpers ---------------------------------------------------

    def _load_from_env(self):
        """Reads environment variables (including .env files) into config."""
        self._try_load_dotenv()

        self.exactor_core_token = (
            os.getenv(_ENV_EXACTOR_CORE_TOKEN)
            or os.getenv(_ENV_EXACTOR_API_KEY)
            or self.exactor_core_token
        )
        self.exactor_base_url = (
            os.getenv(_ENV_EXACTOR_BASE_URL) or self.exactor_base_url
        )
        self.jev_api_key = (
            os.getenv(_ENV_JEV_API_KEY)
            or os.getenv(_ENV_TYPESAFE_API_KEY)
            or self.jev_api_key
        )
        self.deepseek_api_key = (
            os.getenv(_ENV_DEEPSEEK_API_KEY) or self.deepseek_api_key
        )
        self.deepseek_base_url = (
            os.getenv(_ENV_DEEPSEEK_BASE_URL) or self.deepseek_base_url
        )
        self.deepseek_model = (
            os.getenv(_ENV_DEEPSEEK_MODEL) or self.deepseek_model
        )

    @staticmethod
    def _try_load_dotenv():
        """Best-effort load of .env from cwd or package root."""
        try:
            from dotenv import load_dotenv  # type: ignore

            # Try cwd first, then package directory
            for candidate in [Path.cwd() / ".env", Path(__file__).parent.parent / ".env"]:
                if candidate.is_file():
                    load_dotenv(candidate, override=False)
                    logger.debug("Loaded .env from %s", candidate)
                    return
        except ImportError:
            pass  # python-dotenv not installed — no problem

    def update(
        self,
        exactor_core_token: Optional[str] = None,
        exactor_base_url: Optional[str] = None,
        jev_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        deepseek_base_url: Optional[str] = None,
        deepseek_model: Optional[str] = None,
    ):
        """Merge explicit values into the config (None = keep current)."""
        if exactor_core_token is not None:
            self.exactor_core_token = exactor_core_token
        if exactor_base_url is not None:
            self.exactor_base_url = exactor_base_url
        if jev_api_key is not None:
            self.jev_api_key = jev_api_key
        if deepseek_api_key is not None:
            self.deepseek_api_key = deepseek_api_key
        if deepseek_base_url is not None:
            self.deepseek_base_url = deepseek_base_url
        if deepseek_model is not None:
            self.deepseek_model = deepseek_model

    def __repr__(self) -> str:
        def _mask(val: Optional[str]) -> str:
            if val is None:
                return "None"
            return f"{val[:8]}...{val[-4:]}" if len(val) > 16 else "****"

        return (
            f"ExactorConfig("
            f"exactor_core_token={_mask(self.exactor_core_token)}, "
            f"exactor_base_url='{self.exactor_base_url}', "
            f"jev_api_key={_mask(self.jev_api_key)}, "
            f"deepseek_api_key={_mask(self.deepseek_api_key)})"
        )


# Module-level singleton
config = _Config()


def configure(
    exactor_core_token: Optional[str] = None,
    exactor_base_url: Optional[str] = None,
    jev_api_key: Optional[str] = None,
    deepseek_api_key: Optional[str] = None,
    deepseek_base_url: Optional[str] = None,
    deepseek_model: Optional[str] = None,
) -> None:
    """
    Set API tokens programmatically.

    Example::

        import exactor_accelerator
        exactor_accelerator.configure(
            exactor_core_token="your-token-here",
            jev_api_key="your-jev-key",
        )
    """
    config.update(
        exactor_core_token=exactor_core_token,
        exactor_base_url=exactor_base_url,
        jev_api_key=jev_api_key,
        deepseek_api_key=deepseek_api_key,
        deepseek_base_url=deepseek_base_url,
        deepseek_model=deepseek_model,
    )
    logger.info("Configuration updated: %s", config)


def get_config() -> _Config:
    """Return the current global config singleton."""
    return config
