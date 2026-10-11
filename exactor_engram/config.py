"""
Centralized configuration for Exactor Engram Memory.

Plan limits follow the official Exactor licensing scheme
(.agent/rules/pricing_and_licensing.md). The associative hypercube uses
k = 64 propositions, which requires at least the PRO / DEV plan.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

try:  # optional .env support
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


@dataclass(frozen=True)
class PlanLimits:
    name: str
    price_usd_month: Optional[float]
    seats: Optional[int]
    max_variables: int
    max_minterms: Optional[int]
    su_included_month: Optional[int]
    overage_usd_per_1k_su: Optional[float]  # None => hard limit


# Official plan matrix (SaaS ceiling is 128 variables; 256+ is an Engineering Expansion Project).
PLANS: Dict[str, PlanLimits] = {
    "GRATIS": PlanLimits("GRATIS", 0, 1, 12, 1_000, 100, None),
    "SCOUT": PlanLimits("SCOUT", 20, 1, 20, 2_500, 1_000, None),
    "PRO": PlanLimits("PRO", 49, 1, 64, 10_000, 5_000, 10.0),
    "STARTUP": PlanLimits("STARTUP", 499, 5, 128, 100_000, 50_000, 8.0),
    "ESCALA": PlanLimits("ESCALA", 2_499, 15, 128, 1_000_000, 500_000, 5.0),
    "EMPRESARIAL": PlanLimits("EMPRESARIAL", None, None, 128, None, None, None),
}

HYPERCUBE_K = 64  # number of boolean propositions per object


@dataclass
class EngramConfig:
    db_path: str = field(default_factory=lambda: os.getenv("ENGRAM_DB_PATH", "engram_memory.db"))
    blob_dir: str = field(default_factory=lambda: os.getenv("ENGRAM_BLOB_DIR", "engram_blobs"))
    inline_blob_max_bytes: int = 2 * 1024 * 1024  # payloads above this are stored content-addressed on disk
    plan: str = field(default_factory=lambda: os.getenv("EXACTOR_PLAN", "PRO").upper())

    # Perception (Pillar 1)
    stability_margin: float = 0.18  # |value - threshold| / scale below this => bit is don't-care

    # Engram compiler (Pillar 4)
    guard_tolerance_ratio: float = 0.14  # Hamming tolerance of the invariant guard (threshold function)
    guard_min_tolerance: int = 3
    guard_min_literals: int = 12  # an engram must keep at least this many invariant literals
    discriminant_max_bits: int = 10  # projected support for exact minimization (2^10 cells)

    # Oracle (Pillar 2)
    oracle_provider: str = field(default_factory=lambda: os.getenv("ENGRAM_ORACLE", "auto"))
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    deepseek_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"))
    deepseek_base_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    deepseek_model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))

    # Reference cost of one cloud oracle call (used for savings telemetry when the provider
    # does not report usage). Approximate multimodal call: ~1,300 tokens.
    oracle_ref_tokens: int = 1_300
    oracle_ref_cost_usd: float = 0.0040

    @property
    def plan_limits(self) -> PlanLimits:
        return PLANS.get(self.plan, PLANS["PRO"])

    def validate(self) -> None:
        limits = self.plan_limits
        if HYPERCUBE_K > limits.max_variables:
            raise ValueError(
                f"El hipercubo asociativo usa k={HYPERCUBE_K} variables; el plan {limits.name} "
                f"permite hasta {limits.max_variables}. Se requiere al menos PRO / DEV."
            )


_config: Optional[EngramConfig] = None


def get_config() -> EngramConfig:
    global _config
    if _config is None:
        _config = EngramConfig()
    return _config


def set_config(cfg: EngramConfig) -> None:
    global _config
    _config = cfg
