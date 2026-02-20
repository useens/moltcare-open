#!/usr/bin/env python3
"""
EvoMap client configuration.

Manage EvoMap hub connection settings and node identity.
"""

import os
import json
import platform
from pathlib import Path


class EvoMapConfig:
    """EvoMap client configuration manager."""

    DEFAULT_HUB_URL = "https://evomap.ai"
    CONFIG_PATH = Path.home() / ".openclaw" / "evomap_config.json"

    def __init__(self, hub_url: str = None, sender_id: str = None):
        self.hub_url = hub_url or self.DEFAULT_HUB_URL
        self.sender_id = sender_id

    @classmethod
    def load(cls) -> "EvoMapConfig":
        """Load configuration from file or create new."""
        if cls.CONFIG_PATH.exists():
            with open(cls.CONFIG_PATH, "r") as f:
                data = json.load(f)
                return cls(
                    hub_url=data.get("hub_url", cls.DEFAULT_HUB_URL),
                    sender_id=data.get("sender_id")
                )
        else:
            config = cls()
            config.save()
            return config

    def save(self):
        """Save configuration to file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "hub_url": self.hub_url,
            "sender_id": self.sender_id
        }
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def generate_sender_id(self):
        """Generate and save a new sender_id."""
        from .hash_utils import random_hex
        self.sender_id = f"node_{random_hex(8)}"
        self.save()

    def get_env_fingerprint(self) -> dict:
        """Get environment fingerprint."""
        return {
            "platform": platform.system().lower(),
            "arch": platform.machine().lower()
        }

    def claim_code_url(self, claim_code: str) -> str:
        """Get claim URL for binding agent to account."""
        return f"{self.hub_url}/claim/{claim_code}"
