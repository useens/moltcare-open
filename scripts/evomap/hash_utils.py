#!/usr/bin/env python3
"""
EvoMap asset hash utilities.

Compute SHA256 content-addressable IDs for assets.
"""

import hashlib
import json


def compute_asset_id(asset_without_id: dict) -> str:
    """
    Compute SHA256 hash for an asset object (excluding the asset_id field).

    Args:
        asset_without_id: Asset dict without the asset_id field

    Returns:
        "sha256:" + hex digest
    """
    canonical = _canonical_json(asset_without_id)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return f"sha256:{digest}"


def _canonical_json(obj: dict) -> str:
    """
    Convert dict to canonical JSON (sorted keys, deterministic serialization).

    Args:
        obj: Dict to serialize

    Returns:
        Canonical JSON string
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def random_hex(length: int) -> str:
    """
    Generate random hex string.

    Args:
        length: Number of hex characters

    Returns:
        Random hex string
    """
    import secrets
    return secrets.token_hex(length // 2)[:length]
