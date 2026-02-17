#!/usr/bin/env python3
"""
债务完成度自动验证
每次处理债务后运行，确保真正完成
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from metrics.engine import MetricsEngine

engine = MetricsEngine()

# 验证指定债务
def validate_debt(debt_id):
    result = engine.validate_debt_completion(debt_id, validation_type="manual")
    
    passed = sum(1 for c in result["checks"] if c["passed"])
    total = len(result["checks"])
    
    if passed == total:
        print(f"✅ {debt_id}: 验证通过 ({passed}/{total})")
        return True
    else:
        print(f"❌ {debt_id}: 验证失败 ({passed}/{total})")
        for check in result["checks"]:
            if not check["passed"]:
                print(f"   - {check['name']}: 未通过")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debt_id = sys.argv[1]
        success = validate_debt(debt_id)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python3 validate_debt.py <debt_id>")
        print("Example: python3 validate_debt.py DEBT-JACKLE-001")
