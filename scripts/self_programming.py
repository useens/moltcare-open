#!/usr/bin/env python3
"""
林林v5.0 自我编程系统 - 主入口
整合代码生成器和验证器，提供统一的自编程接口
"""

import sys
import os

# 添加core到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.code_generator import CodeGenerator, RequirementParser
from core.code_validator import CodeValidator, ValidationLevel


class SelfProgrammingSystem:
    """自我编程系统主类"""
    
    def __init__(self, output_dir: str = "examples"):
        self.generator = CodeGenerator()
        self.validator = CodeValidator(sandbox_dir="sandbox")
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_health_check(self, requirement: str, auto_test: bool = True) -> dict:
        """
        创建健康检查脚本
        
        Args:
            requirement: 自然语言需求，如"检查CPU使用率是否超过80%"
            auto_test: 是否自动进行测试
            
        Returns:
            包含生成结果和验证结果的字典
        """
        print(f"\n{'='*60}")
        print(f"需求: {requirement}")
        print('='*60)
        
        # 1. 生成代码
        output_path = os.path.join(
            self.output_dir, 
            f"health_check_{self._sanitize_filename(requirement)}.py"
        )
        
        gen_result = self.generator.generate(requirement, output_path)
        
        if not gen_result['success']:
            print(f"❌ 代码生成失败: {gen_result.get('error')}")
            return {
                'success': False,
                'stage': 'generation',
                'error': gen_result.get('error')
            }
        
        print(f"✅ 代码生成成功")
        print(f"   指标类型: {gen_result['metric_type']}")
        print(f"   输出文件: {output_path}")
        
        if not auto_test:
            return {
                'success': True,
                'stage': 'generation',
                'output_path': output_path
            }
        
        # 2. 验证代码
        print(f"\n🔍 开始代码验证...")
        val_result = self.validator.full_validate(gen_result['code'])
        
        print(self.validator.get_validation_report(val_result))
        
        if not val_result['overall_passed']:
            print(f"\n❌ 代码验证未通过")
            return {
                'success': False,
                'stage': 'validation',
                'generation': gen_result,
                'validation': val_result
            }
        
        print(f"\n✅ 代码验证通过，脚本已准备就绪")
        
        return {
            'success': True,
            'stage': 'complete',
            'output_path': output_path,
            'generation': gen_result,
            'validation': val_result
        }
    
    def batch_create(self, requirements: list) -> list:
        """批量创建脚本"""
        results = []
        for req in requirements:
            result = self.create_health_check(req)
            results.append(result)
        return results
    
    def list_templates(self) -> list:
        """列出可用模板"""
        return self.generator.template_lib.list_templates()
    
    def interactive_mode(self):
        """交互模式"""
        print("\n" + "="*60)
        print("林林v5.0 自我编程系统 - 交互模式")
        print("="*60)
        print("\n可用检查类型:")
        for t in self.list_templates():
            print(f"  - {t}")
        print("\n示例需求:")
        print("  - 检查CPU使用率是否超过80%")
        print("  - 检查内存使用率是否超过90%")
        print("  - 检查磁盘空间是否超过85%")
        print("\n输入 'quit' 退出")
        print("-"*60)
        
        while True:
            try:
                requirement = input("\n请输入需求: ").strip()
                if requirement.lower() in ['quit', 'exit', 'q']:
                    break
                if not requirement:
                    continue
                
                self.create_health_check(requirement)
                
            except KeyboardInterrupt:
                print("\n\n退出")
                break
            except Exception as e:
                print(f"错误: {e}")
    
    def _sanitize_filename(self, text: str) -> str:
        """清理文件名"""
        import re
        # 移除特殊字符，替换空格为下划线
        clean = re.sub(r'[^\w\u4e00-\u9fff]', '_', text)
        clean = re.sub(r'_+', '_', clean)
        return clean[:50]  # 限制长度


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='林林v5.0 自我编程系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python self_programming.py -r "检查CPU使用率是否超过80%"
  python self_programming.py -i  # 交互模式
  python self_programming.py --demo  # 运行演示
        '''
    )
    
    parser.add_argument('-r', '--requirement', help='需求描述')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    parser.add_argument('--demo', action='store_true', help='运行演示')
    parser.add_argument('-o', '--output', default='examples', help='输出目录')
    parser.add_argument('--no-test', action='store_true', help='跳过测试')
    
    args = parser.parse_args()
    
    system = SelfProgrammingSystem(output_dir=args.output)
    
    if args.demo:
        print("运行演示模式...")
        demo_requirements = [
            "检查CPU使用率是否超过80%",
            "检查内存使用率是否超过90%", 
            "检查磁盘空间是否超过85%",
        ]
        results = system.batch_create(demo_requirements)
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n{'='*60}")
        print(f"演示完成: {success_count}/{len(results)} 成功")
        print('='*60)
        
    elif args.interactive:
        system.interactive_mode()
        
    elif args.requirement:
        result = system.create_health_check(
            args.requirement, 
            auto_test=not args.no_test
        )
        sys.exit(0 if result['success'] else 1)
        
    else:
        parser.print_help()
        print("\n提示: 使用 --demo 运行演示")


if __name__ == '__main__':
    main()
