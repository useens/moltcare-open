#!/usr/bin/env python3
"""
MoltCare 测试运行器
支持运行所有测试或指定测试
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_tests(pattern: str = "test_*.py", verbose: bool = True) -> int:
    """
    运行测试
    
    Args:
        pattern: 测试文件匹配模式
        verbose: 详细输出
    
    Returns:
        0=成功, 1=失败
    """
    test_dir = PROJECT_ROOT / "tests"
    
    # 发现测试
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern=pattern)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # 返回结果
    return 0 if result.wasSuccessful() else 1


def run_single(test_file: str) -> int:
    """运行单个测试文件"""
    test_path = PROJECT_ROOT / "tests" / test_file
    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_path}")
        return 1
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f"tests.{test_path.stem}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MoltCare 测试运行器")
    parser.add_argument("--file", "-f", help="运行指定测试文件")
    parser.add_argument("--pattern", "-p", default="test_*.py", help="测试文件匹配模式")
    parser.add_argument("--quiet", "-q", action="store_true", help="安静模式")
    
    args = parser.parse_args()
    
    print("🧪 MoltCare 测试运行器")
    print("=" * 40)
    
    if args.file:
        return run_single(args.file)
    else:
        return run_tests(pattern=args.pattern, verbose=not args.quiet)


if __name__ == "__main__":
    sys.exit(main())
