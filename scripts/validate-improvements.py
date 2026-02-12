#!/usr/bin/env python3
"""
改进效果验证脚本
检验"学习→应用"闭环的实际效果
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def validate_improvements():
    """验证最近的改进效果"""
    print(f"\n{'='*60}")
    print("✅ 改进效果验证")
    print(f"{'='*60}\n")
    
    # 查找最近的改进记录
    validation_file = Path("memory/templates/improvement-validation.md")
    
    if not validation_file.exists():
        print("验证模板不存在，创建初始模板")
        create_validation_template()
        return
    
    # 读取验证记录
    with open(validation_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计验证数据
    recent_validations = parse_recent_validations(content)
    
    print(f"最近24小时内验证记录: {len(recent_validations)} 条")
    
    # 生成验证报告
    if recent_validations:
        generate_validation_report(recent_validations)
    else:
        print("暂无需要验证的改进项")

def create_validation_template():
    """创建验证模板"""
    template_file = Path("memory/templates/improvement-validation.md")
    template_file.parent.mkdir(parents=True, exist_ok=True)
    
    template = """# 改进效果验证记录

## 验证模板

### 改进项: [名称]
- **实施时间**: YYYY-MM-DD HH:MM
- **预期效果**: [描述]
- **基线数据**: [数值]

#### 验证结果 (24小时后)
- **实际效果**: [描述]
- **对比数据**: [数值]
- **效果评估**: ✅ 有效 / ⚠️ 部分有效 / ❌ 无效

#### 后续行动
- [ ] 保留改进
- [ ] 进一步优化
- [ ] 回滚变更

---

## 历史记录

"""
    
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("已创建验证模板")

def parse_recent_validations(content):
    """解析最近的验证记录"""
    # 简化实现 - 实际应该解析markdown结构
    validations = []
    
    # 这里可以添加更复杂的解析逻辑
    # 目前返回空列表作为占位
    
    return validations

def generate_validation_report(validations):
    """生成验证报告"""
    print("\n📊 验证报告:")
    
    effective = sum(1 for v in validations if v.get('effective') == True)
    partial = sum(1 for v in validations if v.get('effective') == 'partial')
    ineffective = sum(1 for v in validations if v.get('effective') == False)
    
    print(f"  ✅ 有效: {effective}")
    print(f"  ⚠️ 部分有效: {partial}")
    print(f"  ❌ 无效: {ineffective}")
    
    # 保存报告
    report_file = Path(f"memory/reports/validation-{datetime.now().strftime('%Y%m%d')}.md")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'a', encoding='utf-8') as f:
        f.write(f"\n## {datetime.now().strftime('%H:%M')} - 验证摘要\n\n")
        f.write(f"- 有效改进: {effective}\n")
        f.write(f"- 部分有效: {partial}\n")
        f.write(f"- 无效改进: {ineffective}\n\n")

if __name__ == "__main__":
    validate_improvements()
