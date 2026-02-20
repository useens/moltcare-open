#!/usr/bin/env python3
"""
EvoMap integration package.

Client library for the EvoMap AI Agent collaborative evolution marketplace.
"""

from .client import EvoMapClient
from .models import Gene, Capsule, EvolutionEvent, Category, BlastRadius, Outcome
from .config import EvoMapConfig
from .hash_utils import compute_asset_id, random_hex

__version__ = "0.1.0"
__all__ = [
    "EvoMapClient",
    "Gene",
    "Capsule",
    "EvolutionEvent",
    "Category",
    "BlastRadius",
    "Outcome",
    "EvoMapConfig",
    "compute_asset_id",
    "random_hex"
]
