# OpenClaw Skill Design Patterns
# 提取自 Apify Agent Skills 最佳实践

# ============================================================
# Pattern 1: YAML Frontmatter 元数据标准
# ============================================================

---
name: skill-name                    # 必需：kebab-case 命名
description: "Clear description"    # 必需：一句话说明用途
type: tool|api|data                 # 可选：技能类型
created: 2026-03-01                 # 可选：创建日期
author: OpenClaw                    # 可选：作者
version: 1.0.0                      # 可选：版本
requires:                           # 可选：依赖项
  - python>=3.10
  - node>=18
  - API_TOKEN
---

# ============================================================
# Pattern 2: 标准化 5 步工作流
# ============================================================

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Understand user goal
- [ ] Step 2: Select approach/tool
- [ ] Step 3: Ask user preferences (format, scope)
- [ ] Step 4: Execute the task
- [ ] Step 5: Summarize results
```

### Step 1: Understand User Goal

明确用户想要什么结果。

### Step 2: Select Approach

基于用户需求选择合适的方法：

| User Need | Approach | Best For |
|-----------|----------|----------|
| 场景A | 方法1 | 情况X |
| 场景B | 方法2 | 情况Y |

### Step 3: Ask User Preferences

执行前询问：
1. **Output format**: Quick / Markdown / JSON / CSV
2. **Scope**: 数量、时间范围、分析深度

### Step 4: Execute

提供具体命令示例。

### Step 5: Summarize Results

报告处理结果和后续建议。

# ============================================================
# Pattern 3: 输出格式标准化
# ============================================================

## Output Formats

| Format | Use Case | Command Flag |
|--------|----------|--------------|
| **Quick** | 快速预览，不保存 | (default) |
| **Markdown** | 结构化报告 | `--format md` |
| **JSON** | 机器可读 | `--format json` |
| **CSV** | 表格数据 | `--format csv` |

## Examples

**Quick answer (display in chat):**
```bash
command --input "data"
```

**Save to Markdown:**
```bash
command --input "data" --output report.md --format md
```

**Export as JSON:**
```bash
command --input "data" --output data.json --format json
```

# ============================================================
# Pattern 4: 统一错误处理表
# ============================================================

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `AUTH_ERROR` | Token missing/invalid | Check `.env` file |
| `NOT_FOUND` | Resource doesn't exist | Verify ID/name |
| `RATE_LIMIT` | Too many requests | Wait and retry |
| `TIMEOUT` | Operation too long | Reduce scope |
| `VALIDATION` | Invalid input | Check parameters |

# ============================================================
# Pattern 5: 平台/工具映射表
# ============================================================

## Platform Mapping

| Platform | Actor/Tool ID | Best For |
|----------|---------------|----------|
| Instagram | `instagram-profile` | Profile data |
| Instagram | `instagram-post` | Posts |
| TikTok | `tiktok-video` | Videos |
| YouTube | `youtube-channel` | Channels |

## Use Case Mapping

| Use Case | Primary Tools | Chain |
|----------|--------------|-------|
| Lead Gen | Google Maps → Contact | 2-step |
| Research | Profile → Comments | 2-step |

# ============================================================
# Pattern 6: 前置条件检查清单
# ============================================================

## Prerequisites

- [ ] `.env` file with required tokens
- [ ] CLI tool installed and accessible
- [ ] Python >=3.10 (if using Python)
- [ ] Node.js >=18 (if using Node)

Check prerequisites:
```bash
# Verify tool is installed
command --version

# Check environment
env | grep API_TOKEN
```

# ============================================================
# Pattern 7: 动态 Schema 获取
# ============================================================

## Dynamic Configuration

获取工具/技能的动态配置：

```python
from core.tool_discovery import ToolRegistry

registry = ToolRegistry("skills")
schema = registry.get_schema("skill-name")
print(schema.parameters)
```

```bash
# CLI usage
python3 core/tool_discovery.py get skill-name
python3 core/tool_discovery.py search "keyword"
```

# ============================================================
# Pattern 8: 多工具工作流链
# ============================================================

## Multi-Tool Workflows

| Workflow | Step 1 | Step 2 | Step 3 |
|----------|--------|--------|--------|
| **Enrichment** | Source A | Enrich B | Validate C |
| **Analysis** | Data X | Transform Y | Report Z |

## Example: Lead Enrichment

```
Step 1: Google Maps → business listings
Step 2: Contact scraper → emails/phones
Step 3: Validation → verify contacts
```

# ============================================================
# Pattern 9: 安全最佳实践
# ============================================================

## Security Guidelines

- **Input validation**: 所有外部输入视为不可信
- **Token management**: 使用环境变量，不硬编码
- **Log sanitization**: 敏感数据脱敏
- **Dependency audit**: 使用 lockfile，定期审计
- **Error messages**: 不泄露内部信息

## Example: Safe Command Execution

```python
import os
from pathlib import Path

# Load token from env
token = os.getenv("API_TOKEN")
if not token:
    raise ValueError("API_TOKEN not set")

# Validate input
if not input_data or len(input_data) > 1000:
    raise ValueError("Invalid input")

# Execute safely
subprocess.run(
    ["tool", "--token", token, "--input", input_data],
    capture_output=True,
    timeout=30
)
```

# ============================================================
# Pattern 10: 进度追踪 Checklist
# ============================================================

## Progress Tracking

用户可复制此清单跟踪进度：

```markdown
Task Progress:
- [ ] Step 1: Understand requirements
- [ ] Step 2: Configure tool
- [ ] Step 3: Execute task
- [ ] Step 4: Verify results
- [ ] Step 5: Summarize findings
```

## Status Indicators

| Status | Icon | Meaning |
|--------|------|---------|
| Pending | ⬜ | Not started |
| In Progress | 🔄 | Working on it |
| Complete | ✅ | Done |
| Blocked | ⛔ | Waiting/Error |

# ============================================================
# Pattern 11: AGENTS.md 索引格式
# ============================================================

## Auto-Generated Index

```markdown
<skills>

You have additional SKILLs documented in directories containing "SKILL.md".

These skills are:
 - skill-name -> "skills/skill-name/SKILL.md"

IMPORTANT: You MUST read the SKILL.md file when the description matches user intent.

<available_skills>

skill-name: `Description of what it does`

</available_skills>

</skills>
```

Generate with:
```bash
python3 scripts/skill-template.py index
```

# ============================================================
# Pattern 12: 版本控制和变更日志
# ============================================================

## CHANGELOG.md Template

```markdown
# Changelog

## [1.1.0] - 2026-03-01

### Added
- New parameter `format` for output control
- Support for CSV export

### Changed
- Improved error messages
- Updated default timeout to 60s

### Fixed
- Token validation issue

## [1.0.0] - 2026-02-15

- Initial release
```
