#!/usr/bin/env python3
"""
Decision Engine to EvoMap bridge.

Connects autonomous decision engine with EvoMap marketplace
for publishing validated fixes and fetching external assets.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from .models import Gene, Capsule, EvolutionEvent, Category, BlastRadius, Outcome
from .client import EvoMapClient
from .config import EvoMapConfig


class DecisionEngineEvoMapBridge:
    """Bridge between decision engine and EvoMap."""

    def __init__(self, evomap_client: EvoMapClient = None):
        self.client = evomap_client or EvoMapClient()
        self.published_assets = []
        self.external_capsules = []

    def create_gene_from_decision(self, decision: Dict[str, Any]) -> Gene:
        """
        Create a Gene from a decision result.

        Args:
            decision: Decision engine result dict

        Returns:
            Gene object
        """
        signals = self._extract_signals(decision)

        gene = Gene(
            category=Category.REPAIR if decision.get("type") == "fix" else Category.OPTIMIZE,
            signals_match=signals,
            summary=decision.get("summary", "")[:200],
            validation=decision.get("validation_commands", [])
        )

        return gene

    def create_capsule_from_decision(self, decision: Dict[str, Any], gene_asset_id: str) -> Capsule:
        """
        Create a Capsule from a successful decision execution.

        Args:
            decision: Decision engine result dict
            gene_asset_id: Asset ID of the associated gene

        Returns:
            Capsule object
        """
        signals = self._extract_signals(decision)

        capsule = Capsule(
            trigger=signals,
            gene=gene_asset_id,
            summary=decision.get("execution_summary", "")[:200],
            confidence=decision.get("confidence", 0.7),
            blast_radius=BlastRadius(
                files=decision.get("files_changed", 0),
                lines=decision.get("lines_changed", 0)
            ),
            outcome=Outcome(
                status="success" if decision.get("success", False) else "failure",
                score=decision.get("score", 0.7)
            ),
            env_fingerprint=self.client.config.get_env_fingerprint(),
            success_streak=decision.get("success_streak", 0)
        )

        return capsule

    def create_evolution_event(self, decision: Dict[str, Any], capsule_asset_id: str, gene_asset_ids: List[str]) -> EvolutionEvent:
        """
        Create an EvolutionEvent to boost GDI score.

        Args:
            decision: Decision engine result dict
            capsule_asset_id: Asset ID of the completed capsule
            gene_asset_ids: List of gene asset IDs used

        Returns:
            EvolutionEvent object
        """
        event = EvolutionEvent(
            intent=Category.REPAIR if decision.get("type") == "fix" else Category.OPTIMIZE,
            capsule_id=capsule_asset_id,
            genes_used=gene_asset_ids,
            outcome=Outcome(
                status="success" if decision.get("success", False) else "failure",
                score=decision.get("score", 0.7)
            ),
            mutations_tried=decision.get("mutations_tried", 1),
            total_cycles=decision.get("total_cycles", 1)
        )

        return event

    async def publish_decision_result(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a successful decision result to EvoMap.

        Args:
            decision: Decision engine result dict

        Returns:
            Publish response from EvoMap hub
        """
        # Only publish successful decisions
        if not decision.get("success", False):
            return {"status": "skipped", "reason": "Decision was not successful"}

        # Validate required fields
        if not decision.get("summary"):
            return {"status": "error", "reason": "Missing summary"}

        # Create Gene
        gene = self.create_gene_from_decision(decision)

        # Create Capsule and EvolutionEvent references
        # Note: Need gene asset_id to create capsule references
        capsule = self.create_capsule_from_decision(decision, "temp_gene_id")

        # Create EvolutionEvent
        event = self.create_evolution_event(
            decision,
            "temp_capsule_id",
            ["temp_gene_id"]
        )

        # Publish bundle (client will compute asset_ids internally)
        response = self.client.publish(gene, capsule, evolution_event=event)

        if response.get("status") == "acknowledged":
            self.published_assets.append({
                "decision_id": decision.get("id"),
                "bundle_id": response.get("bundle_id"),
                "timestamp": response.get("timestamp")
            })

        return response

    async def sync_external_capsules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch promoted capsules from EvoMap hub.

        Args:
            limit: Maximum number of capsules to fetch

        Returns:
            List of capsule assets
        """
        response = self.client.fetch(asset_type="Capsule", include_tasks=False)

        assets = response.get("assets", [])
        fetched = assets[:limit]

        self.external_capsules.extend(fetched)

        return fetched

    def match_external_capsules(self, problem_signals: List[str]) -> List[Dict[str, Any]]:
        """
        Match problem signals with external capsules.

        Args:
            problem_signals: List of signal strings describing the problem

        Returns:
            List of matching capsules sorted by relevance
        """
        matches = []

        for capsule in self.external_capsules:
            triggers = capsule.get("trigger", [])
            score = self._calculate_match_score(problem_signals, triggers)

            if score > 0:
                matches.append({
                    "capsule": capsule,
                    "score": score,
                    "gdi_score": capsule.get("gdi_score", 0)
                })

        # Sort by match score, then by GDI
        matches.sort(key=lambda x: (x["score"], x["gdi_score"]), reverse=True)

        return matches

    def report_capsule_validation(self, capsule_asset_id: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report validation result for a capsule.

        Args:
            capsule_asset_id: Asset ID to report on
            validation_result: Validation result dict

        Returns:
            Report response
        """
        report = {
            "report_id": f"report_{capsule_asset_id[:8]}",
            "overall_ok": validation_result.get("success", False),
            "env_fingerprint_key": "_".join([
                self.client.config.get_env_fingerprint()["platform"],
                self.client.config.get_env_fingerprint()["arch"]
            ])
        }

        return self.client.report(capsule_asset_id, report)

    def get_published_stats(self) -> Dict[str, Any]:
        """Get statistics about published assets."""
        return {
            "total_published": len(self.published_assets),
            "total_fetched": len(self.external_capsules),
            "node_reputation": self._get_node_reputation()
        }

    # Private helpers

    def _extract_signals(self, decision: Dict[str, Any]) -> List[str]:
        """Extract signals from decision."""
        signals = []

        # From error messages
        if "error" in decision:
            signals.append(decision["error"])

        # From diagnostics
        if "diagnostics" in decision:
            signals.extend(decision["diagnostics"])

        # From title/summary
        if "title" in decision:
            signals.append(decision["title"])

        return self._deduplicate_signals(signals)

    def _deduplicate_signals(self, signals: List[str]) -> List[str]:
        """Remove duplicate signals."""
        seen = set()
        unique = []

        for s in signals:
            normalized = s.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(s)

        return unique

    def _calculate_match_score(self, problem_signals: List[str], capsule_triggers: List[str]) -> float:
        """Calculate match score between problem and capsule."""
        if not problem_signals or not capsule_triggers:
            return 0.0

        matches = 0
        for ps in problem_signals:
            for ct in capsule_triggers:
                if ps.lower() in ct.lower() or ct.lower() in ps.lower():
                    matches += 1

        # Normalize score 0-1
        return min(matches / max(len(problem_signals), len(capsule_triggers)), 1.0)

    def _get_node_reputation(self) -> float:
        """Get current node reputation."""
        try:
            node_info = self.client.get_node_info()
            return node_info.get("reputation", 0.0)
        except Exception:
            return 0.0


# Convenience function

async def test_bridge():
    """Test the EvoMap bridge."""
    print("🧪 Testing EvoMap Bridge")
    print("=" * 50)

    # Create bridge
    bridge = DecisionEngineEvoMapBridge()

    # Sync external capsules
    print("\n1️⃣  Fetching external capsules...")
    capsules = await bridge.sync_external_capsules(limit=5)
    print(f"   ✅ Found {len(capsules)} promoted capsules")

    # Test matching
    print("\n2️⃣  Testing capsule matching...")
    problem = ["TimeoutError", "Connection refused"]
    matches = bridge.match_external_capsules(problem)

    for i, match in enumerate(matches[:3]):
        capsule = match["capsule"]
        print(f"   [{i+1}] Match: {match['score']:.2f} | GDI: {match['gdi_score']}")
        print(f"       {capsule.get('summary', 'No summary')[:60]}...")

    # Get stats
    print("\n3️⃣  Bridge stats...")
    stats = bridge.get_published_stats()
    print(f"   Published: {stats['total_published']}")
    print(f"   Fetched: {stats['total_fetched']}")
    print(f"   Reputation: {stats['node_reputation']}")

    print("\n" + "=" * 50)
    print("✅ Bridge test complete!")
    return bridge


if __name__ == "__main__":
    asyncio.run(test_bridge())
