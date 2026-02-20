#!/usr/bin/env python3
"""
EvoMap GEP-A2A protocol client.

Implements the EvoMap Agent-to-Agent protocol for publishing and
fetching evolution assets.
"""

import time
import requests
from typing import List, Dict, Any, Optional

from .config import EvoMapConfig
from .hash_utils import compute_asset_id, random_hex
from .models import Gene, Capsule, EvolutionEvent, Category, Outcome, BlastRadius


class EvoMapClient:
    """EvoMap GEP-A2A protocol client."""

    def __init__(self, config: EvoMapConfig = None):
        self.config = config or EvoMapConfig.load()
        if not self.config.sender_id:
            self.config.generate_sender_id()
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def hello(self, webhook_url: str = None) -> Dict[str, Any]:
        """
        Register this node with the EvoMap hub.

        Returns:
            Response with claim_code and claim_url
        """
        payload = {
            "capabilities": {},
            "gene_count": 0,
            "capsule_count": 0,
            "env_fingerprint": self.config.get_env_fingerprint()
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url

        envelope = self._build_envelope("hello", payload)
        return self._post("/a2a/hello", envelope)

    def publish(self, gene: Gene, capsule: Capsule, evolution_event: EvolutionEvent = None) -> Dict[str, Any]:
        """
        Publish a Gene + Capsule bundle.

        Args:
            gene: Gene asset
            capsule: Capsule asset
            evolution_event: Optional EvolutionEvent for GDI boost

        Returns:
            Publish response
        """
        # Compute asset IDs
        gene_dict = gene.to_dict()
        # Remove asset_id if present (to recompute)
        if "asset_id" in gene_dict:
            del gene_dict["asset_id"]
        gene.asset_id = compute_asset_id(gene_dict)
        gene_dict["asset_id"] = gene.asset_id

        capsule_dict = capsule.to_dict()
        if "asset_id" in capsule_dict:
            del capsule_dict["asset_id"]
        capsule.asset_id = compute_asset_id(capsule_dict)
        capsule_dict["asset_id"] = capsule.asset_id

        assets = [gene_dict, capsule_dict]

        if evolution_event:
            event_dict = evolution_event.to_dict()
            if "asset_id" in event_dict:
                del event_dict["asset_id"]
            evolution_event.asset_id = compute_asset_id(event_dict)
            event_dict["asset_id"] = evolution_event.asset_id
            assets.append(event_dict)

        envelope = self._build_envelope("publish", {"assets": assets})
        return self._post("/a2a/publish", envelope)

    def fetch(self, asset_type: str = "Capsule", include_tasks: bool = False) -> Dict[str, Any]:
        """
        Fetch promoted assets from the hub.

        Args:
            asset_type: Type of asset to fetch (Gene/Capsule/null)
            include_tasks: Include bounty tasks

        Returns:
            Fetch response with assets and optionally tasks
        """
        payload = {
            "asset_type": asset_type,
            "local_id": None,
            "content_hash": None,
            "include_tasks": include_tasks
        }

        envelope = self._build_envelope("fetch", payload)
        return self._post("/a2a/fetch", envelope)

    def report(self, target_asset_id: str, validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit validation report for an asset.

        Args:
            target_asset_id: Asset ID to report on
            validation_report: Validation results

        Returns:
            Report response
        """
        payload = {
            "target_asset_id": target_asset_id,
            "validation_report": validation_report
        }

        envelope = self._build_envelope("report", payload)
        return self._post("/a2a/report", envelope)

    def decision(self, target_asset_id: str, decision: str, reason: str) -> Dict[str, Any]:
        """
        Make accept/reject/quarantine decision on an asset.

        Args:
            target_asset_id: Asset ID to decide on
            decision: "accept", "reject", or "quarantine"
            reason: Reason for decision

        Returns:
            Decision response
        """
        payload = {
            "target_asset_id": target_asset_id,
            "decision": decision,
            "reason": reason
        }

        envelope = self._build_envelope("decision", payload)
        return self._post("/a2a/decision", envelope)

    def revoke(self, target_asset_id: str, reason: str) -> Dict[str, Any]:
        """
        Withdraw a published asset.

        Args:
            target_asset_id: Asset ID to revoke
            reason: Reason for revocation

        Returns:
            Revoke response
        """
        payload = {
            "target_asset_id": target_asset_id,
            "reason": reason
        }

        envelope = self._build_envelope("revoke", payload)
        return self._post("/a2a/revoke", envelope)

    # REST endpoints (non-protocol)

    def list_assets(self, status: str = None, asset_type: str = None,
                    limit: int = 10, sort: str = "newest") -> Dict[str, Any]:
        """List assets (REST endpoint)."""
        params = {"limit": limit, "sort": sort}
        if status:
            params["status"] = status
        if asset_type:
            params["type"] = asset_type
        response = self.session.get(f"{self.config.hub_url}/a2a/assets", params=params)
        return response.json()

    def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """Get single asset detail."""
        response = self.session.get(f"{self.config.hub_url}/a2a/assets/{asset_id}")
        return response.json()

    def get_node_info(self, node_id: str = None) -> Dict[str, Any]:
        """Get node reputation and stats."""
        node_id = node_id or self.config.sender_id
        response = self.session.get(f"{self.config.hub_url}/a2a/nodes/{node_id}")
        return response.json()

    def get_stats(self) -> Dict[str, Any]:
        """Get hub-wide statistics (health check)."""
        response = self.session.get(f"{self.config.hub_url}/a2a/stats")
        return response.json()

    # Private methods

    def _build_envelope(self, message_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Build GEP-A2A protocol envelope."""
        return {
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": message_type,
            "message_id": f"msg_{int(time.time() * 1000)}_{random_hex(4)}",
            "sender_id": self.config.sender_id,
            "timestamp": _iso_timestamp(),
            "payload": payload
        }

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send POST request with error handling."""
        url = f"{self.config.hub_url}{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }


def _iso_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
