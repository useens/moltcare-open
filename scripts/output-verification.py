#!/usr/bin/env python3
"""
输出预验证脚本 - 第7.1项绝对原则
验证准备输出的内容是否合理、真实、正确
"""

import sys
import re
from pathlib import Path

class OutputVerification:
    """输出内容预验证器"""
    
    CHECKS = {
        'data_authenticity': {
            'name': '数据真实性',
            'description': '基于实际数据而非估算',
            'red_flags': ['大约', '估计', '可能', '应该', '大概', '左右', '约']
        },
        'information_freshness': {
            'name': '信息时效性',
            'description': '使用最新信息而非缓存',
            'red_flags': ['之前', '上次', '以前', '曾经', '过时']
        },
        'logical_consistency': {
            'name': '逻辑合理性',
            'description': '推理自洽无矛盾',
            'red_flags': ['但是', '然而', '不过']  # 需要结合上下文判断
        },
        'source_traceability': {
            'name': '来源可追溯',
            'description': '关键结论有数据来源',
            'red_flags': []  # 检查是否有数据引用
        },
        'security_compliance': {
            'name': '安全合规性',
            'description': '无敏感信息泄露',
            'red_flags': ['password', 'secret', 'key', 'token', 'credential']
        }
    }
    
    def __init__(self, content: str):
        self.content = content
        self.issues = []
        
    def verify_all(self) -> dict:
        """执行所有验证"""
        results = {}
        
        for check_id, check_config in self.CHECKS.items():
            result = self._run_check(check_id, check_config)
            results[check_id] = result
            if not result['passed']:
                self.issues.append(result['issue'])
        
        return {
            'passed': len(self.issues) == 0,
            'issues': self.issues,
            'details': results
        }
    
    def _run_check(self, check_id: str, config: dict) -> dict:
        """执行单个验证"""
        content = self.content.lower()
        
        # 检查红旗词汇
        red_flags_found = []
        for flag in config['red_flags']:
            if flag.lower() in content:
                red_flags_found.append(flag)
        
        # 特殊检查：数据真实性 - 检查是否有数字但无来源
        if check_id == 'data_authenticity':
            has_numbers = bool(re.search(r'\d+', self.content))
            has_source = '来源' in self.content or '数据' in self.content or '实际' in self.content
            
            if has_numbers and not has_source and red_flags_found:
                return {
                    'passed': False,
                    'issue': f"⚠️ {config['name']}: 发现估算词汇({', '.join(red_flags_found)})，建议用实际数据替代",
                    'red_flags': red_flags_found
                }
        
        # 特殊检查：来源可追溯
        if check_id == 'source_traceability':
            has_data_claim = bool(re.search(r'\d+\s*(次|条|个|小时|分钟|天)', self.content))
            has_source_mark = '来源' in self.content or '文件' in self.content or '实际' in self.content
            
            if has_data_claim and not has_source_mark:
                return {
                    'passed': False,
                    'issue': f"⚠️ {config['name']}: 声称具体数据但未标注来源，建议添加数据来源",
                    'red_flags': []
                }
        
        if red_flags_found:
            return {
                'passed': False,
                'issue': f"⚠️ {config['name']}: 发现可疑词汇({', '.join(red_flags_found)})",
                'red_flags': red_flags_found
            }
        
        return {
            'passed': True,
            'issue': None,
            'red_flags': []
        }
    
    def print_report(self):
        """打印验证报告"""
        result = self.verify_all()
        
        print("="*60)
        print("🔍 输出预验证报告")
        print("="*60)
        
        for check_id, detail in result['details'].items():
            status = "✅" if detail['passed'] else "❌"
            name = self.CHECKS[check_id]['name']
            print(f"{status} {name}")
            if detail['issue']:
                print(f"   {detail['issue']}")
        
        print("="*60)
        
        if result['passed']:
            print("🎉 所有验证通过！可以输出。")
        else:
            print(f"🔴 发现 {len(result['issues'])} 个问题，需要修正：")
            for issue in result['issues']:
                print(f"   - {issue}")
        
        return result['passed']

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 从文件读取
        content = Path(sys.argv[1]).read_text()
    else:
        # 从stdin读取
        content = sys.stdin.read()
    
    verifier = OutputVerification(content)
    passed = verifier.print_report()
    
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
