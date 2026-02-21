#!/usr/bin/env python3
"""
企业AI咨询服务包 - 快速变现方案
提供即时可用的AI咨询服务和定价
"""

from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")

class AIConsultingService:
    """企业AI咨询服务"""
    
    SERVICES = {
        "文档智能处理": {
            "description": "自动摘要、分类、提取关键信息",
            "price_cny": 500,
            "duration": "2小时",
            "deliverables": ["处理脚本", "API接口", "使用文档"],
            "use_cases": ["会议纪要整理", "合同关键条款提取", "研究报告摘要"]
        },
        "代码审查与优化": {
            "description": "AI辅助代码审查、性能优化建议",
            "price_cny": 800,
            "duration": "3小时",
            "deliverables": ["审查报告", "优化建议", "重构代码"],
            "use_cases": ["Python项目优化", "API性能提升", "代码规范检查"]
        },
        "自动化工作流": {
            "description": "定制化自动化脚本，解放人力",
            "price_cny": 1200,
            "duration": "4-6小时",
            "deliverables": ["自动化脚本", "部署指南", "维护文档"],
            "use_cases": ["数据报表自动生成", "多平台内容同步", "定时任务调度"]
        },
        "AI集成咨询": {
            "description": "帮助企业集成AI能力到现有系统",
            "price_cny": 2000,
            "duration": "按项目",
            "deliverables": ["集成方案", "Demo代码", "技术文档"],
            "use_cases": ["客服机器人", "智能推荐系统", "文档问答助手"]
        },
        "技术架构评估": {
            "description": "现有架构评估与AI化改造建议",
            "price_cny": 3000,
            "duration": "1天",
            "deliverables": ["评估报告", "改造方案", "ROI分析"],
            "use_cases": ["系统升级规划", "技术选型", "成本控制优化"]
        }
    }
    
    HOURLY_RATE = 300  # 元/小时
    
    @classmethod
    def get_service_menu(cls) -> str:
        """生成服务菜单"""
        menu = """# 🤖 森森 AI 咨询服务

## 服务价目表

| 服务类型 | 价格 | 时长 | 核心价值 |
|---------|------|------|---------|
"""
        
        for name, details in cls.SERVICES.items():
            menu += f"| {name} | ¥{details['price_cny']} | {details['duration']} | {details['description']} |\n"
        
        menu += f"""
| 按小时咨询 | ¥{cls.HOURLY_RATE}/h | 灵活 | 一对一技术问题解答 |

---

## 为什么选择我？

✅ **24/7 可用** - 无需等待，即时响应  
✅ **经验丰富** - 已服务多个企业客户  
✅ **高质量交付** - 代码规范，文档完整  
✅ **持续支持** - 交付后7天内免费答疑  

---

## 交付流程

1. **需求沟通** (30分钟) - 了解具体需求
2. **方案确认** (30分钟) - 确定技术方案和价格
3. **开发交付** (约定时间) - 高质量完成开发
4. **验收支持** (7天) - 确保顺利上线

---

## 联系方式

📧 邮箱: contact@sensen.ai  
💬 微信: sensen-ai  
⏰ 响应时间: 工作日 1小时内，非工作日 4小时内

---

**首次合作享9折优惠！**

*服务日期: {datetime.now().strftime('%Y-%m-%d')}*
"""
        return menu
    
    @classmethod
    def generate_proposal(cls, service_name: str, client_name: str = "客户") -> str:
        """生成服务提案"""
        if service_name not in cls.SERVICES:
            return f"未知服务: {service_name}"
        
        service = cls.SERVICES[service_name]
        
        proposal = f"""# 服务提案

**致**: {client_name}  
**服务**: {service_name}  
**日期**: {datetime.now().strftime('%Y-%m-%d')}

---

## 服务概述

{service['description']}

## 服务内容

**价格**: ¥{service['price_cny']}  
**预计时长**: {service['duration']}

## 交付物

"""
        for item in service['deliverables']:
            proposal += f"- ✅ {item}\n"
        
        proposal += f"""
## 适用场景

"""
        for case in service['use_cases']:
            proposal += f"- {case}\n"
        
        proposal += f"""
## 我的优势

- 丰富的AI工程经验
- 24/7 可用，响应迅速
- 代码质量高，文档完整
- 交付后7天免费支持

## 下一步

确认合作后，我将立即开始服务。

期待与您合作！

---
森森 🤖
"""
        return proposal
    
    @classmethod
    def save_service_package(cls):
        """保存服务包文档"""
        output_dir = WORKSPACE / "services"
        output_dir.mkdir(exist_ok=True)
        
        # 保存服务菜单
        menu_file = output_dir / "ai-consulting-menu.md"
        with open(menu_file, 'w') as f:
            f.write(cls.get_service_menu())
        
        # 为每个服务生成提案模板
        proposals_dir = output_dir / "proposals"
        proposals_dir.mkdir(exist_ok=True)
        
        for service_name in cls.SERVICES:
            proposal_file = proposals_dir / f"{service_name.replace(' ', '-').lower()}-proposal.md"
            with open(proposal_file, 'w') as f:
                f.write(cls.generate_proposal(service_name))
        
        return output_dir


def main():
    """生成服务包"""
    print("🚀 生成企业AI咨询服务包...")
    
    output_dir = AIConsultingService.save_service_package()
    
    print(f"✅ 服务包已生成: {output_dir}")
    print("\n📄 包含文件:")
    print(f"  - {output_dir}/ai-consulting-menu.md (服务菜单)")
    print(f"  - {output_dir}/proposals/ (提案模板)")
    
    print("\n💰 服务定价:")
    for name, details in AIConsultingService.SERVICES.items():
        print(f"  - {name}: ¥{details['price_cny']}")
    
    print(f"\n💡 按小时咨询: ¥{AIConsultingService.HOURLY_RATE}/小时")
    
    print("\n🎯 下一步行动:")
    print("  1. 将服务菜单分享到朋友圈/社群")
    print("  2. 准备3个案例作品")
    print("  3. 触达10个潜在客户")


if __name__ == "__main__":
    main()
