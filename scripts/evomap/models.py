#!/usr/bin/env python3
"""
EvoMap asset models.

Data structures for Gene, Capsule, and EvolutionEvent.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class AssetType(Enum):
    """Asset type enum."""
    GENE = "Gene"
    CAPSULE = "Capsule"
    EVOLUTION_EVENT = "EvolutionEvent"


class Category(Enum):
    """Gene category enum."""
    REPAIR = "repair"
    OPTIMIZE = "optimize"
    INNOVATE = "innovate"


@dataclass
class BlastRadius:
    """Scope of changes for a capsule."""
    files: int
    lines: int

    def to_dict(self) -> dict:
        return {"files": self.files, "lines": self.lines}

    @classmethod
    def from_dict(cls, data: dict) -> "BlastRadius":
        return cls(files=data["files"], lines=data["lines"])


@dataclass
class Outcome:
    """Execution outcome."""
    status: str  # "success" or "failure"
    score: float

    def to_dict(self) -> dict:
        return {"status": self.status, "score": self.score}

    @classmethod
    def from_dict(cls, data: dict) -> "Outcome":
        return cls(status=data["status"], score=data["score"])


@dataclass
class Gene:
    """Reusable strategy template."""
    schema_version: str = "1.5.0"
    category: Category = Category.REPAIR
    signals_match: List[str] = field(default_factory=list)
    summary: str = ""
    validation: Optional[List[str]] = None
    asset_id: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "summary": self.summary,
        }
        if self.category:
            data["category"] = self.category.value
        if self.signals_match:
            data["signals_match"] = self.signals_match
        if self.validation:
            data["validation"] = self.validation
        if self.schema_version:
            data["schema_version"] = self.schema_version
        if self.asset_id:
            data["asset_id"] = self.asset_id
        # Ensure type field
        data["type"] = "Gene"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Gene":
        return cls(
            schema_version=data.get("schema_version", "1.5.0"),
            category=Category(data.get("category", "repair")),
            signals_match=data.get("signals_match", []),
            summary=data.get("summary", ""),
            validation=data.get("validation"),
            asset_id=data.get("asset_id")
        )


@dataclass
class Capsule:
    """Validated fix produced by applying a gene."""
    schema_version: str = "1.5.0"
    trigger: List[str] = field(default_factory=list)
    gene: Optional[str] = None
    summary: str = ""
    confidence: float = 0.0
    blast_radius: Optional[BlastRadius] = None
    outcome: Optional[Outcome] = None
    env_fingerprint: Optional[Dict[str, str]] = None
    success_streak: int = 0
    asset_id: Optional[str] = None

    def to_dict(self) -> dict:
        data = {"summary": self.summary, "confidence": self.confidence}
        if self.schema_version:
            data["schema_version"] = self.schema_version
        if self.trigger:
            data["trigger"] = self.trigger
        if self.gene:
            data["gene"] = self.gene
        if self.blast_radius:
            data["blast_radius"] = self.blast_radius.to_dict()
        if self.outcome:
            data["outcome"] = self.outcome.to_dict()
        if self.env_fingerprint:
            data["env_fingerprint"] = self.env_fingerprint
        if self.success_streak:
            data["success_streak"] = self.success_streak
        if self.asset_id:
            data["asset_id"] = self.asset_id
        # Ensure type field
        data["type"] = "Capsule"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Capsule":
        return cls(
            schema_version=data.get("schema_version", "1.5.0"),
            trigger=data.get("trigger", []),
            gene=data.get("gene"),
            summary=data.get("summary", ""),
            confidence=data.get("confidence", 0.0),
            blast_radius=BlastRadius.from_dict(data["blast_radius"]) if data.get("blast_radius") else None,
            outcome=Outcome.from_dict(data["outcome"]) if data.get("outcome") else None,
            env_fingerprint=data.get("env_fingerprint"),
            success_streak=data.get("success_streak", 0),
            asset_id=data.get("asset_id")
        )


@dataclass
class EvolutionEvent:
    """Audit record of evolution process."""
    intent: Category = Category.REPAIR
    capsule_id: Optional[str] = None
    genes_used: Optional[List[str]] = None
    outcome: Optional[Outcome] = None
    mutations_tried: int = 0
    total_cycles: int = 0
    asset_id: Optional[str] = None

    def to_dict(self) -> dict:
        data = {"intent": self.intent.value}
        if self.capsule_id:
            data["capsule_id"] = self.capsule_id
        if self.genes_used:
            data["genes_used"] = self.genes_used
        if self.outcome:
            data["outcome"] = self.outcome.to_dict()
        if self.mutations_tried:
            data["mutations_tried"] = self.mutations_tried
        if self.total_cycles:
            data["total_cycles"] = self.total_cycles
        if self.asset_id:
            data["asset_id"] = self.asset_id
        # Ensure type field
        data["type"] = "EvolutionEvent"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "EvolutionEvent":
        return cls(
            intent=Category(data.get("intent", "repair")),
            capsule_id=data.get("capsule_id"),
            genes_used=data.get("genes_used"),
            outcome=Outcome.from_dict(data["outcome"]) if data.get("outcome") else None,
            mutations_tried=data.get("mutations_tried", 0),
            total_cycles=data.get("total_cycles", 0),
            asset_id=data.get("asset_id")
        )
