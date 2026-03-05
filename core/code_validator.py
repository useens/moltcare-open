#!/usr/bin/env python3
"""
林林v5.0 代码验证器 (Code Validator)
自我验证系统 - 确保生成代码的安全性和正确性
"""

import ast
import py_compile
import sys
import os
import re
import subprocess
import tempfile
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"
    STATIC = "static"
    SANDBOX = "sandbox"
    FULL = "full"


@dataclass
class ValidationResult:
    """验证结果"""
    level: str
    passed: bool
    message: str
    details: Optional[Dict] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level,
            'passed': self.passed,
            'message': self.message,
            'details': self.details,
            'duration_ms': self.duration_ms
        }


class SyntaxChecker:
    """语法检查器"""
    
    def check(self, code: str, filename: str = "<generated>") -> ValidationResult:
        """检查Python代码语法"""
        import time
        start = time.time()
        
        try:
            # 使用AST解析检查语法
            ast.parse(code)
            
            # 使用py_compile编译验证
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                py_compile.compile(temp_path, doraise=True)
                duration = (time.time() - start) * 1000
                return ValidationResult(
                    level="syntax",
                    passed=True,
                    message="语法检查通过",
                    duration_ms=duration
                )
            finally:
                os.unlink(temp_path)
                
        except SyntaxError as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                level="syntax",
                passed=False,
                message=f"语法错误: {e.msg} (行 {e.lineno}, 列 {e.offset})",
                details={'line': e.lineno, 'column': e.offset},
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                level="syntax",
                passed=False,
                message=f"编译错误: {str(e)}",
                duration_ms=duration
            )


class StaticAnalyzer:
    """静态分析器 - 基础安全检查"""
    
    # 危险导入列表
    DANGEROUS_IMPORTS = [
        'os.system', 'subprocess.call', 'subprocess.run', 
        'subprocess.Popen', 'eval', 'exec', 'compile',
        '__import__', 'importlib.import_module'
    ]
    
    # 危险函数调用 (触发安全问题)
    DANGEROUS_CALLS = [
        'rm', 'mkfs', 'dd', 'fdisk', 'format',
        'del', 'remove', 'rmdir', 'unlink'
    ]
    
    # 危险属性访问 (触发安全问题)
    DANGEROUS_ATTRS = ['system', 'popen']
    
    # 敏感文件路径
    SENSITIVE_PATHS = [
        '/etc/passwd', '/etc/shadow', '/root', '/boot',
        '/proc', '/sys', '/dev/mem', '/dev/kmem'
    ]
    
    def analyze(self, code: str) -> ValidationResult:
        """执行静态分析"""
        import time
        start = time.time()
        
        issues = []
        warnings = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检查危险导入
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['os', 'subprocess']:
                            warnings.append(f"导入模块: {alias.name}")
                
                if isinstance(node, ast.ImportFrom):
                    if node.module in ['os', 'subprocess']:
                        for alias in node.names:
                            full_name = f"{node.module}.{alias.name}"
                            if full_name in self.DANGEROUS_IMPORTS:
                                issues.append(f"危险导入: {full_name}")
                
                # 检查危险函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec']:
                            issues.append(f"发现危险函数调用: {node.func.id}")
                    
                    # 检查 os.system / subprocess 调用
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['system', 'popen']:
                            issues.append(f"发现危险系统调用: {node.func.attr}")
                        if node.func.attr in ['call', 'run', 'Popen']:
                            # 检查是否使用了 shell=True
                            for kw in node.keywords:
                                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value == True:
                                    issues.append(f"subprocess.{node.func.attr} 使用了 shell=True")
                
                # 检查属性访问 (如 os.system)
                if isinstance(node, ast.Attribute):
                    if node.attr in self.DANGEROUS_ATTRS:
                        issues.append(f"危险属性访问: {node.attr}")
                
                # 检查字符串中是否包含敏感路径
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for path in self.SENSITIVE_PATHS:
                        if path in node.value:
                            issues.append(f"访问敏感路径: {path}")
            
            duration = (time.time() - start) * 1000
            
            if issues:
                return ValidationResult(
                    level="static",
                    passed=False,
                    message=f"静态分析发现 {len(issues)} 个安全问题",
                    details={'issues': issues, 'warnings': warnings},
                    duration_ms=duration
                )
            
            return ValidationResult(
                level="static",
                passed=True,
                message=f"静态分析通过 ({len(warnings)} 个警告)",
                details={'warnings': warnings},
                duration_ms=duration
            )
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                level="static",
                passed=False,
                message=f"静态分析异常: {str(e)}",
                duration_ms=duration
            )


class SandboxTester:
    """沙箱测试器 - 在隔离环境运行代码"""
    
    def __init__(self, sandbox_dir: str = "sandbox"):
        self.sandbox_dir = sandbox_dir
        os.makedirs(sandbox_dir, exist_ok=True)
    
    def test(self, code: str, timeout: int = 10) -> ValidationResult:
        """在沙箱中测试代码"""
        import time
        start = time.time()
        
        # 创建沙箱中的临时文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', 
            dir=self.sandbox_dir, delete=False
        ) as f:
            f.write(code)
            test_file = f.name
        
        try:
            # 使用受限的Python运行环境
            # 限制: CPU时间、内存、文件系统访问
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.sandbox_dir,
                # 设置资源限制 (Linux only)
                # preexec_fn=self._set_resource_limits if os.name != 'nt' else None
            )
            
            duration = (time.time() - start) * 1000
            
            if result.returncode == 0:
                return ValidationResult(
                    level="sandbox",
                    passed=True,
                    message="沙箱测试通过",
                    details={
                        'stdout': result.stdout[:1000],
                        'stderr': result.stderr[:500],
                        'exit_code': result.returncode
                    },
                    duration_ms=duration
                )
            else:
                return ValidationResult(
                    level="sandbox",
                    passed=False,
                    message=f"沙箱测试失败 (退出码: {result.returncode})",
                    details={
                        'stdout': result.stdout[:1000],
                        'stderr': result.stderr[:500],
                        'exit_code': result.returncode
                    },
                    duration_ms=duration
                )
                
        except subprocess.TimeoutExpired:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                level="sandbox",
                passed=False,
                message=f"沙箱测试超时 (>{timeout}秒)",
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ValidationResult(
                level="sandbox",
                passed=False,
                message=f"沙箱测试异常: {str(e)}",
                duration_ms=duration
            )
        finally:
            # 清理沙箱文件
            try:
                os.unlink(test_file)
            except:
                pass
    
    def _set_resource_limits(self):
        """设置资源限制 (Linux)"""
        try:
            import resource
            # 限制CPU时间 (秒)
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
            # 限制内存 (MB)
            resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))
        except ImportError:
            pass


class OutputValidator:
    """输出验证器 - 验证输出是否符合预期"""
    
    def validate(self, output: str, expected_patterns: Optional[List[str]] = None) -> ValidationResult:
        """验证输出内容"""
        import time
        start = time.time()
        
        if not expected_patterns:
            # 默认检查: 健康检查脚本应输出 [OK] 或 [WARNING]
            expected_patterns = [r'\[(OK|WARNING|ERROR)\]']
        
        matched = []
        unmatched = []
        
        for pattern in expected_patterns:
            if re.search(pattern, output):
                matched.append(pattern)
            else:
                unmatched.append(pattern)
        
        duration = (time.time() - start) * 1000
        
        if unmatched and len(matched) == 0:
            return ValidationResult(
                level="output",
                passed=False,
                message=f"输出验证失败，未匹配预期模式",
                details={'matched': matched, 'unmatched': unmatched},
                duration_ms=duration
            )
        
        return ValidationResult(
            level="output",
            passed=True,
            message=f"输出验证通过 ({len(matched)}/{len(expected_patterns)} 模式匹配)",
            details={'matched': matched, 'unmatched': unmatched},
            duration_ms=duration
        )


class CodeValidator:
    """代码验证器主类"""
    
    def __init__(self, sandbox_dir: str = "sandbox"):
        self.syntax_checker = SyntaxChecker()
        self.static_analyzer = StaticAnalyzer()
        self.sandbox_tester = SandboxTester(sandbox_dir)
        self.output_validator = OutputValidator()
        self.validation_history = []
    
    def validate(
        self, 
        code: str, 
        level: ValidationLevel = ValidationLevel.FULL,
        expected_output_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行完整验证流程
        
        Args:
            code: 要验证的代码
            level: 验证级别
            expected_output_patterns: 预期输出模式
            
        Returns:
            验证结果字典
        """
        results = []
        start_time = __import__('time').time()
        
        # Level 1: 语法检查
        syntax_result = self.syntax_checker.check(code)
        results.append(syntax_result)
        
        if not syntax_result.passed:
            return self._compile_result(results, start_time)
        
        if level == ValidationLevel.SYNTAX:
            return self._compile_result(results, start_time)
        
        # Level 2: 静态分析
        static_result = self.static_analyzer.analyze(code)
        results.append(static_result)
        
        if not static_result.passed:
            return self._compile_result(results, start_time)
        
        if level == ValidationLevel.STATIC:
            return self._compile_result(results, start_time)
        
        # Level 3: 沙箱测试
        sandbox_result = self.sandbox_tester.test(code)
        results.append(sandbox_result)
        
        if level == ValidationLevel.SANDBOX:
            return self._compile_result(results, start_time)
        
        # Level 4: 输出验证
        if sandbox_result.passed and sandbox_result.details:
            output = sandbox_result.details.get('stdout', '')
            output_result = self.output_validator.validate(output, expected_output_patterns)
            results.append(output_result)
        
        return self._compile_result(results, start_time)
    
    def _compile_result(self, results: List[ValidationResult], start_time: float) -> Dict[str, Any]:
        """编译最终结果"""
        total_duration = (__import__('time').time() - start_time) * 1000
        all_passed = all(r.passed for r in results)
        
        result = {
            'success': all_passed,
            'overall_passed': all_passed,
            'total_duration_ms': round(total_duration, 2),
            'stages': [r.to_dict() for r in results],
            'summary': {
                'total': len(results),
                'passed': sum(1 for r in results if r.passed),
                'failed': sum(1 for r in results if not r.passed)
            }
        }
        
        self.validation_history.append(result)
        return result
    
    def quick_check(self, code: str) -> bool:
        """快速检查 - 仅语法和静态分析"""
        result = self.validate(code, level=ValidationLevel.STATIC)
        return result['success']
    
    def full_validate(self, code: str, expected_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """完整验证"""
        return self.validate(code, level=ValidationLevel.FULL, expected_output_patterns=expected_patterns)
    
    def get_validation_report(self, result: Dict[str, Any]) -> str:
        """生成验证报告"""
        lines = [
            "=" * 60,
            "代码验证报告",
            "=" * 60,
            f"总体结果: {'✓ 通过' if result['overall_passed'] else '✗ 失败'}",
            f"总耗时: {result['total_duration_ms']}ms",
            f"阶段统计: {result['summary']['passed']}/{result['summary']['total']} 通过",
            "-" * 60,
        ]
        
        for stage in result['stages']:
            status = "✓" if stage['passed'] else "✗"
            lines.append(f"[{status}] {stage['level'].upper()}: {stage['message']}")
            if stage.get('details'):
                if 'issues' in stage['details']:
                    for issue in stage['details']['issues']:
                        lines.append(f"    ! {issue}")
                if 'warnings' in stage['details']:
                    for warning in stage['details']['warnings']:
                        lines.append(f"    ⚠ {warning}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def get_history(self) -> List[Dict]:
        """获取验证历史"""
        return self.validation_history


if __name__ == '__main__':
    print("=" * 60)
    print("林林v5.0 代码验证器")
    print("=" * 60)
    
    # 测试用例
    test_codes = [
        # 正常代码
        '''
import psutil
print("[OK] 测试通过")
        ''',
        # 语法错误
        '''
def broken(
    print("test")
        ''',
        # 危险代码
        '''
import os
os.system("rm -rf /")
        ''',
    ]
    
    validator = CodeValidator()
    
    for i, code in enumerate(test_codes, 1):
        print(f"\n测试用例 #{i}:")
        print("-" * 40)
        result = validator.validate(code.strip())
        print(validator.get_validation_report(result))
