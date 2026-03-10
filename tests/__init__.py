"""
MoltCare Test Suite
单元测试套件
"""

import unittest

# 导出测试基类
from .test_base import TestBase

# 收集所有测试
__all__ = ["TestBase"]


def load_tests():
    """加载所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 自动发现测试
    import os
    test_dir = os.path.dirname(__file__)
    suite = loader.discover(test_dir, pattern="test_*.py")
    
    return suite
