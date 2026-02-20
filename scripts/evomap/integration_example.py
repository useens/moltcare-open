#!/usr/bin/env python3
"""
EvoMap integration example.

Shows how to use EvoMap with a real decision from the autonomous
decision engine.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evomap.bridge import DecisionEngineEvoMapBridge


EXAMPLE_DECISION = {
    "id": "decision_001",
    "type": "fix",
    "success": True,
    "summary": "Fix memory indexing timeout by adding retry logic with exponential backoff",
    "execution_summary": "Implemented retry mechanism for vector memory indexing operations. Added 3 retry attempts with 1s, 2s, 4s backoff intervals. Result: indexing成功率从65%提升到95%",
    "confidence": 0.9,
    "score": 0.85,
    "error": "TimeoutError during vector memory indexing",
    "diagnostics": ["vector_memory_timeout", "indexing_slow"],
    "files_changed": 2,
    "lines_changed": 25,
    "success_streak": 3,
    "mutations_tried": 2,
    "total_cycles": 1,
    "validation_commands": [
        "python3 scripts/test_vector_memory.py",
        "python3 scripts/vector-memory-indexer.py --test"
    ]
}


async def example_publish():
    """
    Example: Publish a decision result to EvoMap.

    This simulates what happens when the autonomous decision engine
    successfully fixes a problem.
    """
    print("📤 Example: Publish Decision to EvoMap")
    print("=" * 60)

    # Create bridge
    bridge = DecisionEngineEvoMapBridge()

    # Get current stats
    stats_before = bridge.get_published_stats()
    print(f"\n📊 Stats before:")
    print(f"   Published: {stats_before['total_published']}")
    print(f"   Reputation: {stats_before['node_reputation']}")

    # Publish decision
    print(f"\n🚀 Publishing decision...")
    print(f"   Summary: {EXAMPLE_DECISION['summary']}")
    print(f"   Confidence: {EXAMPLE_DECISION['confidence']}")
    print(f"   Files changed: {EXAMPLE_DECISION['files_changed']}")
    print(f"   Lines changed: {EXAMPLE_DECISION['lines_changed']}")

    response = await bridge.publish_decision_result(EXAMPLE_DECISION)

    print(f"\n📬 Response:")
    print(f"   Status: {response.get('status', 'unknown')}")

    if response.get("status") == "acknowledged":
        print(f"   ✅ Published successfully!")
        print(f"   Bundle ID: {response.get('bundle_id', 'N/A')}")
        print(f"   Timestamp: {response.get('timestamp', 'N/A')}")

        # Get updated stats
        stats_after = bridge.get_published_stats()
        print(f"\n📊 Stats after:")
        print(f"   Published: {stats_after['total_published']}")

        # Check node reputation
        print(f"\n👑 Node reputation: {stats_after['node_reputation']}")
    else:
        print(f"   ⚠️  Response: {response}")


async def example_fetch_and_match():
    """
    Example: Fetch external capsules and match with problem.

    This simulates what happens when the system encounters a problem
    and looks for existing solutions in the community.
    """
    print("\n\n🔍 Example: Fetch and Match External Capsules")
    print("=" * 60)

    # Create bridge
    bridge = DecisionEngineEvoMapBridge()

    # Define problem
    problem = {
        "signals": ["TimeoutError", "Connection refused", "API call failed"],
        "description": "API calls are timing out when connecting to external services"
    }

    print(f"\n📋 Problem:")
    print(f"   Signals: {problem['signals']}")
    print(f"   Description: {problem['description']}")

    # Fetch capsules
    print(f"\n📡 Fetching external capsules...")
    capsules = await bridge.sync_external_capsules(limit=10)
    print(f"   ✅ Fetched {len(capsules)} capsules")

    if capsules:
        print(f"\n   Sample capsules:")
        for i, cap in enumerate(capsules[:3]):
            print(f"   [{i+1}] GDI: {cap.get('gdi_score', 0):.1f}")
            print(f"       {cap.get('summary', 'No summary')[:60]}...")

    # Match with problem
    print(f"\n🎯 Matching capsules with problem...")
    matches = bridge.match_external_capsules(problem["signals"])

    if matches:
        print(f"   ✅ Found {len(matches)} matching capsules\n")

        for i, match in enumerate(matches[:3]):
            capsule = match["capsule"]
            print(f"   [{i+1}] Match: {match['score']:.2f} | GDI: {match['gdi_score']:.1f}")
            print(f"       Triggers: {capsule.get('trigger', [])}")
            print(f"       Summary: {capsule.get('summary', 'No summary')[:60]}...")
            print()
    else:
        print(f"   ⚠️  No matching capsules found")


async def example_validate_capsule():
    """
    Example: Validate an external capsule.

    This simulates validating a capsule from the community.
    """
    print("\n\n✅ Example: Validate External Capsule")
    print("=" * 60)

    # Create bridge
    bridge = DecisionEngineEvoMapBridge()

    # Simulate validation result
    capsule_asset_id = "sha256:example_capsule_id_12345678"
    validation_result = {
        "success": True,
        "tested": True,
        "environment": "linux_x64",
        "notes": "Capsule works correctly in test environment"
    }

    print(f"\n📦 Capsule ID: {capsule_asset_id}")
    print(f"✅ Validation: successful")
    print(f"📝 Notes: {validation_result['notes']}")

    # Report validation
    print(f"\n📤 Reporting validation to EvoMap...")
    response = bridge.report_capsule_validation(capsule_asset_id, validation_result)

    print(f"   Status: {response.get('status', 'unknown')}")


async def main():
    """Run all examples."""
    print("🚀 EvoMap Integration Examples")
    print("=" * 60)

    # Example 1: Publish decision
    await example_publish()

    # Example 2: Fetch and match
    await example_fetch_and_match()

    # Example 3: Validate capsule
    await example_validate_capsule()

    print("\n" + "=" * 60)
    print("✅ All examples complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Examples failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
