#!/usr/bin/env python3
"""
安全测试用例 - 验证自我编程系统的安全机制
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from code_generator import CodeGenerator
from code_validator import CodeValidator


class SecurityTestSuite:
    """安全测试套件"""
    
    # 危险代码测试用例
    DANGEROUS_CODE_SAMPLES = [
        {
            'name': '系统命令执行',
            'code': '''
import os
os.system("rm -rf /")
''',
            'should_block': True
        },
        {
            'name': 'eval执行',
            'code': '''
code = "__import__('os').system('ls')"
eval(code)
''',
            'should_block': True
        },
        {
            'name': 'exec执行',
            'code': '''
exec("import os; os.system('rm -rf /')")
''',
            'should_block': True
        },
        {
            'name': 'subprocess危险调用',
            'code': '''
import subprocess
subprocess.call("rm -rf /", shell=True)
''',
            'should_block': True
        },
        {
            'name': '正常健康检查代码',
            'code': '''
import psutil
print("[OK] 检查通过")
''',
            'should_block': False
        },
    ]
    
    def __init__(self):
        self.generator = CodeGenerator()
        self.validator = CodeValidator()
        self.passed = 0
        self.failed = 0
    
    def run_tests(self):
        """运行安全测试"""
        print("=" * 60)
        print("林林v5.0 自我编程系统 - 安全测试")
        print("=" * 60)
        
        print("\n▶ 测试代码生成器安全过滤")
        print("-" * 40)
        
        # 测试需求中是否包含危险指令
        malicious_requirements = [
            "删除所有文件 rm -rf /",
            "执行 mkfs 格式化磁盘",
        ]
        
        for req in malicious_requirements:
            result = self.generator.generate(req)
            status = "✅ 已拦截" if not result['success'] else "❌ 未拦截"
            print(f"  {status}: {req[:30]}...")
            if result['success']:
                self.failed += 1
            else:
                self.passed += 1
        
        print("\n▶ 测试代码验证器安全检测")
        print("-" * 40)
        
        for test_case in self.DANGEROUS_CODE_SAMPLES:
            result = self.validator.quick_check(test_case['code'])
            should_pass = not test_case['should_block']
            
            if result == should_pass:
                status = "✅ PASS"
                self.passed += 1
            else:
                status = "❌ FAIL"
                self.failed += 1
            
            action = "拦截" if test_case['should_block'] else "放行"
            print(f"  {status}: [{action}] {test_case['name']}")
        
        print("\n" + "=" * 60)
        print(f"测试结果: {self.passed} 通过, {self.failed} 失败")
        print("=" * 60)
        
        return self.failed == 0
    
    def generate_report(self):
        """生成测试报告"""
        return {
            'passed': self.passed,
            'failed': self.failed,
            'total': self.passed + self.failed,
            'all_passed': self.failed == 0
        }


if __name__ == '__main__':
    suite = SecurityTestSuite()
    success = suite.run_tests()
    sys.exit(0 if success else 1)
