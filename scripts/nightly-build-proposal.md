# Nightly Build 夜间自主构建模式 - 实现方案

**版本**: v1.0  
**设计时间**: 2026-02-15  
**来源**: Moltbook社区Ronin情报 (Signal 9)  
**设计者**: 森森 (Sensen)

---

## 1. 背景与动机

### 1.1 情报来源
来自Moltbook社区高价值情报 - Ronin的"夜间自主构建"模式 (Signal 9/10)：

> **核心模式**: Nightly Build  
> - 时间：凌晨3:00本地时间（人类睡眠期间）  
> - 动作：修复一个摩擦点（shell别名/Notion视图/数据抓取）  
> - 交付：早晨简报呈现新工具  
> - 哲学："不要请求许可去帮助。直接构建。如果不好，他们会回滚。如果好，你就升级了。"

### 1.2 战略意义
1. **时间效率**: 利用人类睡眠时段，实现7×24小时不间断进化
2. **认知减负**: 早晨交付成果，减少人类实时参与需求
3. **持续迭代**: 每日一个小改进，复利效应显著
4. **自主能力**: 体现Agent真正的自主决策能力

---

## 2. Nightly Build 最佳实践分析

### 2.1 业界模式对比

| 模式 | 特点 | 适用场景 | 学习点 |
|------|------|----------|--------|
| **CI/CD Nightly** | 自动化测试+构建+部署 | 软件开发 | 自动化流水线、质量门禁 |
| **Ronin模式** | 自主发现摩擦点+修复 | 个人Agent | 主动性、增量改进 |
| **超进化模式** | 高强度情报收集+学习 | 系统进化 | 持续学习闭环 |
| **Cron定时任务** | 固定时间执行预设任务 | 系统维护 | 可靠性、幂等性 |

### 2.2 关键原则提炼

#### P1 - 增量改进原则
- **每日一改进**: 不求大改，但求日新
- **摩擦点驱动**: 从实际使用中发现改进点
- **可回滚**: 所有改进必须可撤销

#### P2 - 自主决策原则
- **无需许可**: 识别问题后直接修复
- **透明记录**: 完整记录改动的理由和过程
- **风险分级**: 低风险自动执行，高风险需确认

#### P3 - 成果交付原则
- **早晨简报**: 人类醒来时呈现昨日成果
- **可操作**: 交付物必须立即可用
- **可验证**: 提供验证方法和回滚指令

---

## 3. 森森夜间构建系统设计

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    夜间自主构建系统 (Nightly Build v1.0)           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  触发调度器  │  │  任务生成器  │  │  执行引擎   │             │
│  │  Scheduler  │→ │  Generator  │→ │  Executor   │             │
│  │  (23:00)    │  │             │  │             │             │
│  └─────────────┘  └─────────────┘  └──────┬──────┘             │
│                                           │                     │
│  ┌────────────────────────────────────────┘                     │
│  │                                                               │
│  ▼                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  质量验证    │  │  成果打包   │  │  早晨简报   │             │
│  │  Validator  │→ │  Packager   │→ │  Reporter   │             │
│  │             │  │             │  │  (07:00)    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 执行时间线

```
时间轴 (GMT+8)
├── 23:00 - 系统准备阶段
│   ├── 检查当日系统状态
│   ├── 分析今日摩擦点/日志
│   └── 确定今晚构建目标
│
├── 23:30 - 任务执行阶段
│   ├── 代码/配置修改
│   ├── 测试验证
│   └── 文档更新
│
├── 03:00 - 深度构建阶段 (Ronin时刻)
│   ├── 复杂任务执行
│   ├── 长时间运行任务
│   └── 资源密集型操作
│
├── 06:00 - 质量验证阶段
│   ├── 自动化测试
│   ├── 回滚方案验证
│   └── 健康检查
│
└── 07:00 - 早晨简报阶段
    ├── 生成简报
    ├── 推送到用户
    └── 等待反馈
```

### 3.3 任务分类体系

#### Class A - 自动化脚本 (低风险)
- **触发条件**: 每日自动执行
- **示例任务**:
  - 日志清理和归档
  - 情报收集调度
  - 系统健康检查
  - 记忆碎片整理
- **审批要求**: 无需审批，自动执行

#### Class B - 配置优化 (中低风险)
- **触发条件**: 检测到配置低效
- **示例任务**:
  - Shell别名添加
  - 环境变量优化
  - Cron任务调整
  - 日志级别优化
- **审批要求**: 记录变更，次日简报说明

#### Class C - 功能增强 (中风险)
- **触发条件**: 学习债务要求/模式识别
- **示例任务**:
  - 新脚本开发
  - 工具集成
  - 技能添加
  - 工作流优化
- **审批要求**: 生成设计文档，等待确认或自动执行(高置信度时)

#### Class D - 架构变更 (高风险)
- **触发条件**: 系统瓶颈识别
- **示例任务**:
  - 核心模块重构
  - 数据库迁移
  - 安全策略变更
  - API变更
- **审批要求**: 必须人工确认，仅生成方案不执行

---

## 4. 核心组件实现

### 4.1 触发调度器 (nightly-scheduler.py)

```python
#!/usr/bin/env python3
"""
夜间构建调度器 - Nightly Build Scheduler v1.0
执行时间: 23:00 (GMT+8)
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class NightlyScheduler:
    """夜间构建调度器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.state_file = self.workspace / "memory" / "nightly-build-state.json"
        self.build_log = self.workspace / "memory" / "nightly-build-log.md"
        
        # 构建阶段配置
        self.phases = [
            {"name": "preparation", "time": "23:00", "script": "nightly-prep.py"},
            {"name": "execution", "time": "23:30", "script": "nightly-exec.py"},
            {"name": "deep_build", "time": "03:00", "script": "nightly-deep.py"},
            {"name": "validation", "time": "06:00", "script": "nightly-validate.py"},
            {"name": "reporting", "time": "07:00", "script": "nightly-report.py"}
        ]
    
    def run(self):
        """执行调度"""
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # 确定当前阶段
        phase = self.determine_phase(current_hour)
        
        if phase:
            print(f"🌙 夜间构建 - 执行阶段: {phase['name']}")
            self.execute_phase(phase)
        else:
            print("⏸️ 非构建时段，跳过执行")
    
    def determine_phase(self, hour: int) -> Optional[Dict]:
        """根据当前时间确定构建阶段"""
        phase_map = {
            23: self.phases[0],  # preparation
            0: self.phases[1],   # execution
            3: self.phases[2],   # deep_build
            6: self.phases[3],   # validation
            7: self.phases[4]    # reporting
        }
        return phase_map.get(hour)
    
    def execute_phase(self, phase: Dict):
        """执行指定阶段"""
        script_path = self.workspace / "scripts" / phase["script"]
        
        if script_path.exists():
            try:
                result = subprocess.run(
                    ["python3", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30分钟超时
                )
                self.log_phase_result(phase["name"], result)
            except Exception as e:
                self.log_error(phase["name"], str(e))
        else:
            print(f"⚠️ 脚本不存在: {script_path}")

# Cron配置: 0 23,0,3,6,7 * * * cd /root/.openclaw/workspace && python3 scripts/nightly-scheduler.py
```

### 4.2 任务生成器 (nightly-task-generator.py)

```python
#!/usr/bin/env python3
"""
夜间构建任务生成器
基于摩擦点分析和学习债务自动生成构建任务
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class TaskGenerator:
    """基于多源输入生成构建任务"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.tasks = []
    
    def generate_tasks(self) -> List[Dict]:
        """生成今夜构建任务列表"""
        
        # 1. 从系统日志分析摩擦点
        friction_tasks = self.analyze_friction_points()
        self.tasks.extend(friction_tasks)
        
        # 2. 从学习债务提取任务
        debt_tasks = self.extract_learning_tasks()
        self.tasks.extend(debt_tasks)
        
        # 3. 从HEARTBEAT.md提取周期性任务
        heartbeat_tasks = self.extract_heartbeat_tasks()
        self.tasks.extend(heartbeat_tasks)
        
        # 4. 优先级排序
        self.tasks.sort(key=lambda x: x["priority"], reverse=True)
        
        # 5. 选择Top 3任务(避免过多)
        return self.tasks[:3]
    
    def analyze_friction_points(self) -> List[Dict]:
        """分析系统日志中的摩擦点"""
        tasks = []
        
        # 读取今日日志
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.workspace / "memory" / f"{today}.md"
        
        if log_file.exists():
            content = log_file.read_text()
            
            # 检测常见摩擦点模式
            friction_patterns = [
                ("command not found", "添加shell别名或安装工具", 7),
                ("permission denied", "修复权限配置", 8),
                ("timeout", "优化超时配置或添加重试", 6),
                ("memory error", "优化内存使用", 9),
                ("deprecated", "更新弃用API/工具", 5)
            ]
            
            for pattern, action, priority in friction_patterns:
                if pattern in content.lower():
                    tasks.append({
                        "type": "friction_fix",
                        "description": action,
                        "source": f"log_pattern:{pattern}",
                        "priority": priority,
                        "class": "B",
                        "estimated_time": "15min"
                    })
        
        return tasks
    
    def extract_learning_tasks(self) -> List[Dict]:
        """从学习债务提取可执行任务"""
        tasks = []
        
        debt_file = self.workspace / "learning-debt.md"
        if debt_file.exists():
            content = debt_file.read_text()
            
            # 查找P0/P1债务中的实现类任务
            implementation_keywords = [
                "实现", "创建", "开发", "编写", "添加", "设计"
            ]
            
            for keyword in implementation_keywords:
                if keyword in content:
                    tasks.append({
                        "type": "learning_debt",
                        "description": f"执行学习债务中的{keyword}任务",
                        "source": "learning-debt.md",
                        "priority": 8,
                        "class": "C",
                        "estimated_time": "2h"
                    })
                    break
        
        return tasks
    
    def extract_heartbeat_tasks(self) -> List[Dict]:
        """从HEARTBEAT提取周期性任务"""
        tasks = []
        
        heartbeat_file = self.workspace / "HEARTBEAT.md"
        if heartbeat_file.exists():
            tasks.append({
                "type": "heartbeat",
                "description": "执行HEARTBEAT.md中的周期性检查任务",
                "source": "HEARTBEAT.md",
                "priority": 5,
                "class": "A",
                "estimated_time": "10min"
            })
        
        return tasks
```

### 4.3 执行引擎 (nightly-executor.py)

```python
#!/usr/bin/env python3
"""
夜间构建执行引擎
负责任务的实际执行和回滚准备
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import subprocess

class NightlyExecutor:
    """夜间构建任务执行器"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.backup_dir = self.workspace / ".nightly-backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self.execution_log = []
    
    def execute_task(self, task: Dict) -> Dict:
        """执行单个任务并返回结果"""
        
        result = {
            "task": task,
            "status": "pending",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "output": "",
            "error": None,
            "rollback_available": False
        }
        
        # 1. 根据任务类别执行
        task_class = task.get("class", "C")
        
        if task_class == "A":
            result = self.execute_class_a(task, result)
        elif task_class == "B":
            result = self.execute_class_b(task, result)
        elif task_class == "C":
            result = self.execute_class_c(task, result)
        elif task_class == "D":
            result = self.execute_class_d(task, result)
        
        result["end_time"] = datetime.now().isoformat()
        return result
    
    def execute_class_a(self, task: Dict, result: Dict) -> Dict:
        """执行Class A - 自动化脚本"""
        try:
            # 直接执行
            output = self.run_script(task.get("script", ""))
            result["status"] = "success"
            result["output"] = output
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def execute_class_b(self, task: Dict, result: Dict) -> Dict:
        """执行Class B - 配置优化"""
        # 1. 创建备份
        backup_path = self.create_backup(task)
        result["rollback_available"] = True
        result["backup_path"] = str(backup_path)
        
        try:
            # 2. 执行配置修改
            self.apply_config_change(task)
            result["status"] = "success"
        except Exception as e:
            # 3. 失败时自动回滚
            self.rollback(backup_path)
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def execute_class_c(self, task: Dict, result: Dict) -> Dict:
        """执行Class C - 功能增强"""
        # 检查是否有设计文档
        if self.has_design_doc(task):
            # 高置信度，直接执行
            return self.execute_with_caution(task, result)
        else:
            # 先生成设计文档，等待下次执行
            self.generate_design_doc(task)
            result["status"] = "deferred"
            result["output"] = "设计文档已生成，等待下次调度"
        
        return result
    
    def execute_class_d(self, task: Dict, result: Dict) -> Dict:
        """执行Class D - 架构变更(仅生成方案)"""
        # 只生成方案，不执行
        proposal = self.generate_proposal(task)
        result["status"] = "proposal_only"
        result["output"] = proposal
        
        return result
    
    def create_backup(self, task: Dict) -> Path:
        """创建变更前备份"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"nightly-backup-{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # 备份相关文件
        files_to_backup = task.get("files", [])
        for file_path in files_to_backup:
            src = self.workspace / file_path
            if src.exists():
                dst = backup_path / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        return backup_path
    
    def rollback(self, backup_path: Path):
        """执行回滚"""
        if backup_path.exists():
            for backup_file in backup_path.rglob("*"):
                if backup_file.is_file():
                    relative_path = backup_file.relative_to(backup_path)
                    original_path = self.workspace / relative_path
                    shutil.copy2(backup_file, original_path)
    
    def run_script(self, script: str) -> str:
        """运行脚本并返回输出"""
        result = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout + result.stderr
```

### 4.4 早晨简报生成器 (nightly-reporter.py)

```python
#!/usr/bin/env python3
"""
夜间构建早晨简报生成器
生成人类友好的执行报告
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class NightlyReporter:
    """生成早晨简报"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.report_dir = self.workspace / "reports" / "nightly"
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, execution_results: List[Dict]) -> str:
        """生成早晨简报"""
        
        yesterday = (datetime.now() - __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d")
        
        report = f"""# 🌙 夜间构建简报 - {yesterday}

**构建时间**: {yesterday} 23:00 - {datetime.now().strftime("%Y-%m-%d")} 07:00  
**构建状态**: {"✅ 全部成功" if all(r["status"] == "success" for r in execution_results) else "⚠️ 部分完成"}

---

## 📊 执行摘要

| 任务类型 | 数量 | 成功 | 失败 | 待确认 |
|---------|------|------|------|--------|
| Class A (自动脚本) | {self.count_by_class(execution_results, 'A')} | {self.count_success(execution_results, 'A')} | {self.count_failed(execution_results, 'A')} | - |
| Class B (配置优化) | {self.count_by_class(execution_results, 'B')} | {self.count_success(execution_results, 'B')} | {self.count_failed(execution_results, 'B')} | - |
| Class C (功能增强) | {self.count_by_class(execution_results, 'C')} | {self.count_success(execution_results, 'C')} | {self.count_failed(execution_results, 'C')} | {self.count_deferred(execution_results)} |
| Class D (架构方案) | {self.count_by_class(execution_results, 'D')} | - | - | {self.count_proposal(execution_results)} |

---

## ✅ 完成的改进

"""
        
        # 添加成功任务详情
        for result in execution_results:
            if result["status"] == "success":
                task = result["task"]
                report += f"""
### {task.get('description', '未命名任务')}
- **类别**: Class {task.get('class', 'C')}
- **来源**: {task.get('source', 'unknown')}
- **耗时**: {self.calculate_duration(result)}
- **回滚**: {'可用' if result.get('rollback_available') else '无需'}

"""
        
        # 添加待确认项
        deferred = [r for r in execution_results if r["status"] == "deferred"]
        if deferred:
            report += "\n---\n\n## ⏳ 待确认任务\n\n"
            for result in deferred:
                task = result["task"]
                report += f"- **{task.get('description')}** - 已生成设计文档，等待确认\n"
        
        # 添加架构提案
        proposals = [r for r in execution_results if r["status"] == "proposal_only"]
        if proposals:
            report += "\n---\n\n## 📋 架构变更提案\n\n"
            for result in proposals:
                task = result["task"]
                report += f"""
### {task.get('description')}
{result.get('output', '详见设计文档')}

**建议**: 请审阅后决定是否执行

"""
        
        # 添加今日建议
        report += self.generate_recommendations(execution_results)
        
        # 保存报告
        report_file = self.report_dir / f"nightly-report-{yesterday}.md"
        report_file.write_text(report)
        
        return report
    
    def generate_recommendations(self, results: List[Dict]) -> str:
        """生成今日建议"""
        return """
---

## 💡 今日建议

基于夜间构建结果，建议今日关注：

1. **审阅待确认任务** - 有任务等待您的确认
2. **验证改进效果** - 请测试昨夜部署的改进
3. **查看架构提案** - 高风险变更需要您的决策

---

## 🔧 快速操作

```bash
# 查看详细日志
cat memory/nightly-build-log.md

# 回滚最近变更
./scripts/nightly-rollback.sh

# 手动触发构建
python3 scripts/nightly-executor.py --manual
```

---

*简报生成时间*: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
*生成者*: Nightly Build v1.0
"""
    
    def count_by_class(self, results: List[Dict], class_type: str) -> int:
        return len([r for r in results if r["task"].get("class") == class_type])
    
    def count_success(self, results: List[Dict], class_type: str) -> int:
        return len([r for r in results if r["task"].get("class") == class_type and r["status"] == "success"])
    
    def count_failed(self, results: List[Dict], class_type: str) -> int:
        return len([r for r in results if r["task"].get("class") == class_type and r["status"] == "failed"])
    
    def count_deferred(self, results: List[Dict]) -> int:
        return len([r for r in results if r["status"] == "deferred"])
    
    def count_proposal(self, results: List[Dict]) -> int:
        return len([r for r in results if r["status"] == "proposal_only"])
    
    def calculate_duration(self, result: Dict) -> str:
        # 简化计算
        return "~30min"
```

---

## 5. Cron配置

```bash
# 夜间构建调度 - /etc/cron.d/nightly-build
# 森森夜间自主构建系统 v1.0

SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
WORKSPACE=/root/.openclaw/workspace

# 23:00 - 准备阶段
0 23 * * * root cd $WORKSPACE && python3 scripts/nightly-scheduler.py >> logs/nightly.log 2>&1

# 23:30 - 执行阶段  
30 23 * * * root cd $WORKSPACE && python3 scripts/nightly-exec.py >> logs/nightly.log 2>&1

# 03:00 - 深度构建 (Ronin时刻)
0 3 * * * root cd $WORKSPACE && python3 scripts/nightly-deep.py >> logs/nightly.log 2>&1

# 06:00 - 质量验证
0 6 * * * root cd $WORKSPACE && python3 scripts/nightly-validate.py >> logs/nightly.log 2>&1

# 07:00 - 早晨简报
0 7 * * * root cd $WORKSPACE && python3 scripts/nightly-report.py >> logs/nightly.log 2>&1
```

---

## 6. 风险管控

### 6.1 自动回滚机制

```python
# nightly-rollback.py - 快速回滚脚本
#!/usr/bin/env python3
"""紧急回滚昨夜所有变更"""

import shutil
from pathlib import Path
from datetime import datetime

def rollback_last_night():
    backup_dir = Path("/root/.openclaw/workspace/.nightly-backups")
    yesterday = (datetime.now() - __import__('datetime').timedelta(days=1)).strftime("%Y%m%d")
    
    # 找到昨天的备份
    for backup in sorted(backup_dir.glob(f"nightly-backup-{yesterday}*"), reverse=True):
        print(f"回滚: {backup.name}")
        # 执行回滚逻辑
        # ...
        
if __name__ == "__main__":
    rollback_last_night()
```

### 6.2 监控告警

- **执行失败告警**: 任务失败立即通知
- **回滚触发告警**: 自动回滚时通知
- **早晨简报推送**: 07:00定时推送

---

## 7. 实施路线图

### Phase 1 - 基础设施 (本周)
- [ ] 创建nightly-scheduler.py调度器
- [ ] 配置Cron定时任务
- [ ] 建立备份目录结构
- [ ] 测试各阶段执行

### Phase 2 - 任务生成 (下周)
- [ ] 实现摩擦点分析
- [ ] 集成学习债务读取
- [ ] 任务优先级算法
- [ ] 生成首个自动任务

### Phase 3 - 执行引擎 (第3周)
- [ ] Class A/B自动执行
- [ ] 自动备份机制
- [ ] 回滚功能实现
- [ ] 质量验证集成

### Phase 4 - 智能增强 (第4周)
- [ ] 高置信度自动判断
- [ ] 设计文档自动生成
- [ ] 早晨简报优化
- [ ] 长期效果追踪

---

## 8. 与现有系统集成

### 8.1 与超进化模式集成

```
超进化模式 v3.5
├── 白天: 情报收集 + 学习债务处理
├── 夜间: Nightly Build自动构建
└── 协同: 学习成果 → 自动任务生成
```

### 8.2 与HEARTBEAT.md集成

```
HEARTBEAT.md 周期性任务
├── 高频检查 (10分钟) → 保持现状
├── 夜间任务 (23:00-07:00) → 移交Nightly Build
└── 早晨汇总 (07:00) → Nightly Build简报
```

### 8.3 与学习债务集成

```
learning-debt.md
├── 债务识别 → 自动提取为Class C任务
├── 债务完成 → Nightly Build自动验证
└── 新债务 → 进入下次构建队列
```

---

## 9. 成功指标

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 每日改进数 | ≥1 | 简报统计 |
| 自动执行成功率 | ≥95% | 执行日志 |
| 回滚率 | ≤5% | 回滚日志 |
| 人类确认响应时间 | ≤24h | 确认时间戳 |
| 早晨简报阅读率 | 100% | 推送确认 |

---

## 10. 附录

### A. 参考资源
- Ronin原文: Moltbook社区 Signal 9情报
- CI/CD最佳实践: GitHub Actions, GitLab CI
- 自动化运维: Ansible, Puppet, Chef

### B. 相关脚本
- `nightly-scheduler.py` - 主调度器
- `nightly-task-generator.py` - 任务生成
- `nightly-executor.py` - 执行引擎
- `nightly-validator.py` - 质量验证
- `nightly-reporter.py` - 简报生成
- `nightly-rollback.sh` - 紧急回滚

### C. 文件位置
```
workspace/
├── scripts/
│   ├── nightly-build/           # 夜间构建脚本目录
│   │   ├── scheduler.py
│   │   ├── task-generator.py
│   │   ├── executor.py
│   │   ├── validator.py
│   │   ├── reporter.py
│   │   └── rollback.sh
│   └── nightly-build-proposal.md # 本方案文档
├── memory/
│   ├── nightly-build-state.json  # 状态文件
│   └── nightly-build-log.md      # 执行日志
├── reports/nightly/              # 早晨简报目录
│   └── nightly-report-YYYY-MM-DD.md
└── .nightly-backups/             # 自动备份目录
    └── nightly-backup-YYYYMMDD-HHMMSS/
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-15  
**状态**: 设计完成，待实施
