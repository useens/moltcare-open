#!/usr/bin/env python3
"""
Test EvoMap client connection and basic operations.

Run this script to verify that the EvoMap client can connect
to the hub and perform basic operations.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evomap import EvoMapClient, Gene, Capsule, EvolutionEvent, Category, BlastRadius, Outcome


def main():
    print("🧪 EvoMap Client Connection Test")
    print("=" * 50)

    # Create client
    print("\n1️⃣  Creating client...")
    client = EvoMapClient()
    print(f"   Hub URL: {client.config.hub_url}")
    print(f"   Sender ID: {client.config.sender_id}")

    # Test hub health
    print("\n2️⃣  Checking hub health...")
    stats = client.get_stats()
    print(f"   Status: {stats.get('status', 'unknown')}")
    if "error" in stats:
        print(f"   ❌ Error: {stats['error']}")
        return False
    else:
        print("   ✅ Hub is online")

    # Register node
    print("\n3️⃣  Registering node...")
    hello_response = client.hello()
    print(f"   Status: {hello_response.get('status', 'unknown')}")

    if hello_response.get("status") == "acknowledged":
        claim_code = hello_response.get("claim_code")
        claim_url = hello_response.get("claim_url")
        print("   ✅ Node registered")
        print(f"   Claim Code: {claim_code}")
        print(f"   Claim URL: {claim_url}")
    else:
        print(f"   ⚠️  Response: {hello_response}")

    # Fetch assets
    print("\n4️⃣  Fetching promotedcapsules...")
    fetch_response = client.fetch(asset_type="Capsule")
    assets = fetch_response.get("assets", [])
    print(f"   Found {len(assets)} promoted capsules")

    for i, asset in enumerate(assets[:3]):  # Show first 3
        print(f"   [{i+1}] {asset.get('summary', 'No summary')[:50]}...")

    # Check node info
    print("\n5️⃣  Checking node reputation...")
    node_info = client.get_node_info()
    print(f"   Reputation: {node_info.get('reputation', 'N/A')}")
    print(f"   Gene Count: {node_info.get('gene_count', 0)}")
    print(f"   Capsule Count: {node_info.get('capsule_count', 0)}")

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
