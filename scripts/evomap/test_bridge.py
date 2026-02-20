#!/usr/bin/env python3
"""
Test EvoMap bridge integration.

Tests the decision engine bridge functionality.
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evomap.bridge import DecisionEngineEvoMapBridge, test_bridge


def main():
    print("🧪 EvoMap Bridge Integration Test")
    print("=" * 60)

    try:
        # Run bridge test
        bridge = asyncio.run(test_bridge())
        return True
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
