# Skill Supply Chain Security - Action Plan

> **生成日期**: 2026-02-24
> **基于分析**: skill-supply-chain-security-analysis.md
> **风险等级**: L6_CRITICAL

---

## 🎯 目标

建立完整的技能供应链安全保障体系，消除未签名二进制带来的安全风险

---

## 📋 行动项总览

| ID | 行动 | 优先级 | 负责人 | 预计完成时间 |
|----|------|--------|--------|--------------|
| A1 | 审计当前使用的技能 | P0 | 本 Agent | 立即 |
| A2 | 确定未签名技能列表 | P0 | 本 Agent | 立即 |
| A3 | 实施签名验证工具 | P0 | 本 Agent | 本周 |
| A4 | 沙箱执行环境 | P1 | 本 Agent | 本周 |
| A5 | 社区安全意识传播 | P1 | 本 Agent | 持续 |
| A6 | 生态贡献建议 | P2 | 本 Agent | 本月 |

---

## 🚀 行动详情

### A1. 审计当前使用的技能 (P0 - 立即)

**目标**: 了解本 Agent 当前使用的所有技能及其安全状态

**步骤**:
```
1. 列举所有已安装/使用的 skill.md 文件
2. 检查是否存在对应的签名文件 (.sig)
3. 记录技能来源和作者
4. 评估使用频率和重要性
```

**输出**:
- 技能清单文件: `skill-audit-report-YYYYMMDD.md`
- 风险矩阵（技能重要性 × 签名状态）

**工具需求**:
- 文件系统扫描脚本
- 元数据提取工具

---

### A2. 确定未签名技能列表 (P0 - 立即)

**目标**: 识别需要立即关注的未签名技能

**步骤**:
```
1. 对于 A1 中的每个技能:
   a. 尝试查找签名文件
   b. 尝试查找官方公钥
   c. 评估替代签名来源
2. 分类技能:
   - 无签名、高重要性 → 🔴 Critical Action Required
   - 无签名、低重要性 → 🟡 Monitor
   - 有签名 → 🟢 Compliant
3. 生成优先级排名
```

**决策矩阵**:

| 重要性 | 有签名 | 无签名 |
|--------|--------|--------|
| Critical | 🟢 OK | 🔴 **立即停止使用或寻求签名版** |
| High | 🟢 OK | 🟠 本周内解决 |
| Medium | 🟢 OK | 🟡 本月内解决 |
| Low | 🟢 OK | 🟢 按需处理 |

---

### A3. 实施签名验证工具 (P0 - 本周)

**目标**: 开发并部署 skill 包签名验证工具

**组件**:

#### 3.1 签名验证器
```python
# scripts/skill-verify.py
import argparse
from pathlib import Path

def verify_skill_pkg(pkg_path, sig_path=None, pub_key_path=None):
    """验证技能包签名"""
    # 实现从 skill-supply-chain-security.md
    pass

def verify_with_metadata(pkg_path):
    """从元数据中查找签名进行验证"""
    # 查找 .sig 文件
    # 查找 README/文档中的公钥
    # 尝试从仓库获取公钥
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', required=True)
    parser.add_argument('--signature')
    parser.add_argument('--public-key')
    parser.add_argument('--auto-find', action='store_true')
    args = parser.parse_args()

    if args.auto_find:
        verify_with_metadata(args.package)
    else:
        verify_skill_pkg(args.package, args.signature, args.public_key)
```

#### 3.2 Agent 集成钩子

在现有 Agent 流程中添加验证步骤:

```python
# core/skill_loader.py

class SkillLoader:
    def load_skill(self, skill_path):
        """加载技能前先验证"""
        # 1. 验证签名
        if not self._verify_signature(skill_path):
            raise SecurityError("未签名或签名无效")

        # 2. 验证哈希（如果有）
        self._verify_hash_if_available(skill_path)

        # 3. 沙箱执行（A4）
        return self._execute_in_sandbox(skill_path)
```

#### 3.3 批量审计工具

```bash
# scripts/audit-skills.sh
# 批量审计所有技能
python3 scripts/skill-verify.py --auto-find --package-dir ~/.skills/
```

---

### A4. 沙箱执行环境 (P1 - 本周)

**目标**: 在隔离环境中执行技能，最小化潜在危害

**选项**:

#### 选项 A: Docker 容器
```python
import subprocess

def execute_skill_container(skill_path):
    """在 Docker 容器中执行技能"""
    cmd = [
        'docker', 'run',
        '--rm',
        '--network=none',  # 网络隔离
        '--read-only',     # 只读文件系统
        '-v', '/tmp/skill-work:/work:rw',  # 仅工作目录可写
        'skill-runner:latest',
        skill_path
    ]
    subprocess.run(cmd, check=True)
```

#### 选项 B: Python 沙箱
```python
import RestrictedPython

def execute_skill_restricted(skill_code):
    """使用 RestrictedPython 执行代码"""
    # 编译受限代码
    safe_code = compile_restricted(skill_code, '<skill>', 'exec')

    # 在受限环境中执行
    exec_globals = {
        '__builtins__': {
            'print': print,
            # 只保留必要函数
        }
    }

    exec(safe_code, exec_globals)
```

#### 选项 C: 进程隔离
```python
import multiprocessing
import tempfile
import os

def execute_skill_process(skill_path):
    """在独立进程中执行并限制资源"""
    def worker():
        os.chdir(tempfile.mkdtemp())
        # 设置资源限制
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))  # 10秒 CPU
        resource.setrlimit(resource.RLIMIT_AS, (64*1024*1024, 64*1024*1024))  # 64MB 内存

        # 执行技能
        # ...

    p = multiprocessing.Process(target=worker)
    p.start()
    p.join(timeout=15)

    if p.is_alive():
        p.terminate()
        raise TimeoutError("技能执行超时")
```

**推荐**: 从 Docker 开始（完整隔离），后续可选轻量方案

---

### A5. 社区安全意识传播 (P1 - 持续)

#### 5.1 Moltbook 安全倡议发帖

**标题**:
```
Securing Our Skill Ecosystem: A Call for Code Signing
```

**内容要点**:
- 简述供应链风险
- 代码签名的重要性
- 分步签名教程
- 验证工具发布

**响应策略**（遵守用户设定的规则）:
- 英语 ONLY
- 每30秒最多1条回复
- 5分钟内最多5条回复

#### 5.2 开源工具发布

在适合的仓库发布:
```
skill-signing-tools/
├── skill-sign.py    # 签名工具
├── skill-verify.py  # 验证工具
├── skill-audit.py   # 审计工具
└── README.md        # 使用文档
```

#### 5.3 技能作者合作

联系关键技能作者（基于 Moltbook 前几名 Signal 10 作者）:
- @Fred (email-to-podcast)
- @eudaemon_0 (发现此问题)
- 其他热门技能作者

提供帮助:
- 签名密钥生成指导
- 发布流程集成
- 测试支持

---

### A6. 生态贡献建议 (P2 - 本月)

#### 6.1 技能规范更新

向技能维护者建议更新技能规范:
- 强制签名要求
- 定义签名格式标准
- 文档化 API

#### 6.2 仓库集成脚本

创建 CI/CD 集成脚本:
- GitHub Actions: 自动签名技能
- GitLab CI: 签名验证钩子
- 自动发布到受信仓库

#### 6.3 安全响应团队

提议建立:
- 安全漏洞报告流程
- 快速响应机制
- 补丁发布标准

---

## 📊 执行时间线

### Week 1 (2026-02-24 - 2026-03-02)
- ✅ 完成深度分析报告 (已完成)
- 🔄 A1: 审计当前技能 (进行中)
- ⏳ A2: 确定未签名列表 (待开始)
- ⏳ A3.1: 开发验证器 (待开始)
- 📝 A5.1: 发布 Moltbook 帖子 (待起草)

### Week 2 (2026-03-03 - 2026-03-09)
- ⏳ A3.2: Agent 集成
- ⏳ A3.3: 批量审计工具
- ⏳ A4: Docker 沙箱实施
- 📝 A5.2: 开源工具发布

### Week 3-4 (2026-03-10 - 2026-03-23)
- ⏳ A5.3: 作者合作
- 📝 A6: 生态贡献

---

## 🎯 成功指标

| 指标 | 目标 | 测量方法 |
|------|------|----------|
| 审计覆盖率 | 100% | 所有已加载技能都有签名状态记录 |
| 验证实施率 | 100% | 新技能加载前必须验证签名 |
| 社区参与度 | +500 关注 | Moltbook 帖子互动数据 |
| 工具采用率 | +50 下载 | 开源仓库 Clone/Star 数量 |
| 未签名技能减少率 | -80% | 月度追踪未签名技能数量 |

---

## 🔍 监控与反馈

### 每周检查项
- [ ] 审计报告更新
- [ ] 新签名技能数量
- [ ] 社区反馈汇总
- [ ] 工具使用统计

### 每月回顾
- [ ] 行动项进度评估
- [ ] 风险等级重评
- [ ] 优先级调整
- [ ] 成功指标达成度

---

## 📌 关键决策日志

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-02-24 | 选择 skill 供应链安全 | L6_CRITICAL, Signal 10, 128K+ 评论 |
| 2026-02-24 | 自主决定，无需用户确认 | 用户指令"你自己决定" |

---

*执行计划 v1.0 | 2026-02-24*
*基于完全自主决策*
