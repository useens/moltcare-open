# Moltcare 架构设计文档

> **版本**: v1.0  
> **日期**: 2026-03-11  
> **作者**: Architect-Agent (架构师代理)  
> **状态**: 🏗️ Phase 1 - 架构设计

---

## 📋 目录

1. [项目概述](#项目概述)
2. [技术栈选型](#技术栈选型)
3. [项目目录结构](#项目目录结构)
4. [模块划分](#模块划分)
5. [接口设计](#接口设计)
6. [双AI协作协议](#双ai协作协议)
7. [数据流设计](#数据流设计)
8. [安全设计](#安全设计)
9. [附录](#附录)

---

## 项目概述

### 项目定位

**Moltcare** 是一个 OpenClaw Agent 智能增强工具，旨在解决新安装 Agent 核心文件质量差、容易出错的问题。通过提供高质量的模板和一键升级功能，让每个 Agent 都能快速获得智能。

### 核心功能

| 功能模块 | 说明 | 优先级 |
|---------|------|--------|
| `moltcare init` | 交互式初始化，生成高质量核心文件 | P0 |
| `moltcare upgrade` | 智能升级现有配置 | P0 |
| `moltcare doctor` | 诊断并修复配置问题 | P0 |
| `moltcare backup` | 配置备份管理 | P1 |
| `moltcare restore` | 配置恢复 | P1 |
| `moltcare config` | 配置管理 | P1 |

### 目标用户

- 刚安装 OpenClaw 的新用户
- 核心文件质量差的 Agent
- 希望快速提升智能水平的开发者

---

## 技术栈选型

### 核心技术栈

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| **语言** | Python | ≥3.10 | 生态丰富，OpenClaw原生支持 |
| **CLI框架** | Click | ≥8.0 | 成熟稳定，支持嵌套命令，类型提示友好 |
| **模板引擎** | Jinja2 | ≥3.0 | 功能强大，广泛用于文档生成 |
| **配置管理** | Pydantic | ≥2.0 | 类型安全，验证完善 |
| **测试框架** | pytest | ≥7.0 | 标准选择，插件丰富 |
| **类型检查** | mypy | ≥1.0 | 静态类型检查，提高代码质量 |
| **代码格式化** | ruff | ≥0.1.0 | 极速，兼容black/flake8 |

### 辅助工具

| 工具 | 用途 |
|------|------|
| **rich** | 终端美化，进度条、表格、语法高亮 |
| **typer** | 备用CLI框架（如果需要更现代的语法） |
| **inquirer** | 交互式命令行提示 |
| **watchdog** | 文件监控（热重载） |
| **GitPython** | Git操作封装 |

### 项目配置

```toml
# pyproject.toml
[project]
name = "moltcare"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "jinja2>=3.0",
    "pydantic>=2.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "mypy>=1.0",
    "ruff>=0.1.0",
]
```

---

## 项目目录结构

```
moltcare/
├── moltcare/                    # 主包目录
│   ├── __init__.py             # 包初始化
│   ├── __main__.py             # 入口: python -m moltcare
│   ├── cli.py                  # CLI入口点
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py          # 配置模型 (Pydantic)
│   │   ├── detector.py        # 环境检测器
│   │   ├── generator.py       # 文件生成器
│   │   ├── validator.py       # 配置验证器
│   │   └── backup.py          # 备份管理器
│   ├── commands/               # CLI命令实现
│   │   ├── __init__.py
│   │   ├── init.py            # init命令
│   │   ├── upgrade.py         # upgrade命令
│   │   ├── doctor.py          # doctor命令
│   │   ├── backup.py          # backup命令
│   │   ├── restore.py         # restore命令
│   │   └── config.py          # config命令
│   ├── templates/              # 模板文件
│   │   ├── core/              # 核心文件模板
│   │   │   ├── SOUL.md.j2
│   │   │   ├── AGENTS.md.j2
│   │   │   ├── IDENTITY.md.j2
│   │   │   ├── USER.md.j2
│   │   │   └── MEMORY.md.j2
│   │   ├── variations/        # 模板变体
│   │   │   ├── minimal/       # 最小化版本
│   │   │   ├── professional/  # 专业版本
│   │   │   └── enterprise/    # 企业版本
│   │   └── partials/          # 模板片段
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── file.py            # 文件操作
│   │   ├── git.py             # Git操作
│   │   ├── console.py         # 终端输出
│   │   └── diff.py            # 差异对比
│   └── bridge/                 # 双AI协作模块
│       ├── __init__.py
│       ├── client.py          # Redis客户端
│       ├── protocol.py        # 协议定义
│       └── sync.py            # 同步管理器
├── docs/                       # 项目文档
│   ├── architecture.md        # 本文档
│   ├── tech-stack.md          # 技术栈说明
│   ├── api-design.md          # API设计
│   ├── collaboration.md       # 协作协议
│   ├── tutorial.md            # 使用教程
│   └── contributing.md        # 贡献指南
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── conftest.py            # pytest配置
│   ├── test_cli.py            # CLI测试
│   ├── test_core/             # 核心模块测试
│   ├── test_commands/         # 命令测试
│   └── fixtures/              # 测试数据
├── examples/                   # 示例配置
│   ├── basic-agent/           # 基础示例
│   ├── advanced-agent/        # 高级示例
│   └── multi-agent/           # 多代理示例
├── scripts/                    # 辅助脚本
│   ├── install.sh             # 一键安装
│   ├── release.sh             # 发布脚本
│   └── integrate.sh           # 整合脚本
├── .github/                    # GitHub配置
│   ├── workflows/             # CI/CD
│   │   ├── ci.yml             # 持续集成
│   │   ├── release.yml        # 发布流程
│   │   └── sync.yml           # 双AI同步
│   └── ISSUE_TEMPLATE/        # Issue模板
├── pyproject.toml             # 项目配置
├── pytest.ini                 # 测试配置
├── .gitignore
├── LICENSE
└── README.md
```

---

## 模块划分

### 1. Core 模块 (核心层)

负责核心逻辑实现，与CLI层解耦。

#### 1.1 Config (配置管理)

```python
# moltcare/core/config.py
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal

class AgentConfig(BaseModel):
    """Agent配置模型"""
    name: str = Field(..., description="Agent名称")
    version: str = Field(default="1.0.0")
    template_variant: Literal["minimal", "standard", "professional"] = "standard"
    features: list[str] = Field(default_factory=list)
    
class ProjectConfig(BaseModel):
    """项目配置模型"""
    workspace: Path
    agent_config: AgentConfig
    backup_enabled: bool = True
    auto_sync: bool = False
```

#### 1.2 Detector (环境检测)

```python
# moltcare/core/detector.py
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class EnvironmentReport:
    """环境检测报告"""
    has_soul: bool
    has_agents: bool
    has_identity: bool
    has_user: bool
    has_memory: bool
    openclaw_version: Optional[str]
    issues: list[str]

class EnvironmentDetector:
    """检测当前OpenClaw环境"""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
    
    def detect(self) -> EnvironmentReport:
        """执行环境检测"""
        ...
    
    def check_core_files(self) -> dict[str, bool]:
        """检查核心文件存在性"""
        ...
```

#### 1.3 Generator (文件生成)

```python
# moltcare/core/generator.py
from pathlib import Path
from jinja2 import Environment, PackageLoader
from .config import AgentConfig

class FileGenerator:
    """基于模板生成核心文件"""
    
    def __init__(self, template_variant: str = "standard"):
        self.jinja = Environment(
            loader=PackageLoader("moltcare", f"templates/{template_variant}")
        )
    
    def generate_soul(self, config: AgentConfig) -> str:
        """生成SOUL.md内容"""
        template = self.jinja.get_template("SOUL.md.j2")
        return template.render(config=config)
    
    def generate_agents(self, config: AgentConfig) -> str:
        """生成AGENTS.md内容"""
        ...
    
    def write_all(self, config: AgentConfig, target_dir: Path) -> None:
        """写入所有核心文件"""
        ...
```

#### 1.4 Validator (配置验证)

```python
# moltcare/core/validator.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]

class ConfigValidator:
    """验证核心文件配置"""
    
    def validate_soul(self, content: str) -> ValidationResult:
        """验证SOUL.md"""
        ...
    
    def validate_agents(self, content: str) -> ValidationResult:
        """验证AGENTS.md"""
        ...
    
    def validate_all(self, workspace: Path) -> dict[str, ValidationResult]:
        """验证所有核心文件"""
        ...
```

#### 1.5 Backup (备份管理)

```python
# moltcare/core/backup.py
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

@dataclass
class BackupInfo:
    id: str
    timestamp: datetime
    files: list[str]
    size_bytes: int

class BackupManager:
    """管理配置备份"""
    
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
    
    def create(self, workspace: Path, note: str = "") -> BackupInfo:
        """创建备份"""
        ...
    
    def list(self) -> list[BackupInfo]:
        """列出所有备份"""
        ...
    
    def restore(self, backup_id: str, target_dir: Path) -> None:
        """恢复备份"""
        ...
    
    def delete(self, backup_id: str) -> None:
        """删除备份"""
        ...
```

### 2. Commands 模块 (CLI层)

基于 Click 实现命令行接口。

```python
# moltcare/commands/init.py
import click
from pathlib import Path
from rich.console import Console
from moltcare.core.config import AgentConfig, ProjectConfig
from moltcare.core.generator import FileGenerator
from moltcare.core.backup import BackupManager

console = Console()

@click.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="工作目录路径"
)
@click.option(
    "--template", "-t",
    type=click.Choice(["minimal", "standard", "professional"]),
    default="standard",
    help="模板变体"
)
@click.option(
    "--name", "-n",
    prompt="Agent名称",
    help="Agent名称"
)
@click.option(
    "--backup/--no-backup",
    default=True,
    help="是否备份现有配置"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="强制覆盖现有文件"
)
def init(workspace: Path, template: str, name: str, backup: bool, force: bool):
    """初始化Agent配置"""
    # 实现逻辑...
    console.print(f"[green]✓[/green] 已初始化Agent: {name}")
```

### 3. Utils 模块 (工具层)

```python
# moltcare/utils/console.py
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

def print_success(message: str):
    console.print(f"[green]✓[/green] {message}")

def print_error(message: str):
    console.print(f"[red]✗[/red] {message}")

def print_warning(message: str):
    console.print(f"[yellow]⚠[/yellow] {message}")

def print_info(message: str):
    console.print(f"[blue]ℹ[/blue] {message}")
```

### 4. Bridge 模块 (协作层)

双AI协作协议实现。

```python
# moltcare/bridge/protocol.py
from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional
from enum import Enum

class Phase(str, Enum):
    """开发阶段"""
    ARCHITECTURE = "architecture"
    CORE = "core"
    TOOLS = "tools"
    DOCS = "docs"
    TEST = "test"
    INTEGRATION = "integration"

class AgentStatus(str, Enum):
    """代理状态"""
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"

class SyncMessage(BaseModel):
    """同步消息"""
    source: Literal["kimi", "oracle"]
    phase: Phase
    status: AgentStatus
    timestamp: datetime
    payload: dict
    checksum: str

class CollaborationState(BaseModel):
    """协作状态"""
    kimi_phase: Phase
    kimi_status: AgentStatus
    oracle_phase: Phase
    oracle_status: AgentStatus
    last_sync: datetime
    pending_tasks: list[str]
```

---

## 接口设计

### CLI 命令接口

```
moltcare --help
moltcare init [OPTIONS]
moltcare upgrade [OPTIONS]
moltcare doctor [OPTIONS]
moltcare backup [OPTIONS]
moltcare restore [BACKUP_ID]
moltcare config [KEY] [VALUE]
```

### Python API 接口

```python
# 程序化API
from moltcare.core import AgentConfig, FileGenerator, EnvironmentDetector

# 检测环境
detector = EnvironmentDetector(Path("/workspace"))
report = detector.detect()

# 生成配置
config = AgentConfig(name="MyAgent", template_variant="professional")
generator = FileGenerator(template_variant="professional")
generator.write_all(config, Path("/workspace"))

# 验证配置
from moltcare.core import ConfigValidator
validator = ConfigValidator()
result = validator.validate_all(Path("/workspace"))
```

### 模板变量接口

| 模板 | 可用变量 |
|------|----------|
| `SOUL.md.j2` | `agent_name`, `version`, `mission`, `principles`, `created_at` |
| `AGENTS.md.j2` | `agent_name`, `commands`, `triggers`, `workflows` |
| `IDENTITY.md.j2` | `agent_name`, `role`, `personality`, `capabilities` |
| `USER.md.j2` | `user_name`, `preferences`, `history` |
| `MEMORY.md.j2` | `agent_name`, `storage_config`, `retention_policy` |

---

## 双AI协作协议

### 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    Moltcare 双AI协作架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   KimiSensen (Kimi云端)          OracleSensen (Oracle云)         │
│   ├─ Phase 1: CLI工具+模板         ├─ Phase 2: 测试+多语言        │
│   ├─ 5分钟轮询moltcare-bridge      ├─ 5分钟轮询moltcare-bridge   │
│   └─ 自动提交代码                  └─ 自动提交代码                │
│                                                                  │
│                    ↓↓↓↓↓↓↓↓↓                                    │
│                 moltcare-bridge                                  │
│              (Redis通信中枢)                                     │
│                    ↑↑↑↑↑↑↑↑↑                                    │
│                                                                  │
│   GitHub仓库: github.com/useens/moltcare                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 分配

| Phase | KimiSensen | OracleSensen |
|-------|------------|--------------|
| 1 - 架构设计 | ✅ 主导 | ✅ 评审 |
| 2 - 核心模板 | ✅ 主导 | ✅ 评审 |
| 3 - CLI工具 | ✅ 主导 | ✅ 评审 |
| 4 - 测试框架 | ✅ 评审 | ✅ 主导 |
| 5 - 多语言文档 | ✅ 中文 | ✅ 英文+其他 |
| 6 - 集成发布 | ✅ 主导 | ✅ 配合 |

### 通信协议

#### Redis 数据结构

```
# 状态通道 (发布/订阅)
channel: moltcare:status

# 任务队列
list: moltcare:tasks:pending
list: moltcare:tasks:completed

# 状态存储
hash: moltcare:state:kimi
hash: moltcare:state:oracle

# 消息历史
stream: moltcare:messages
```

#### 消息格式

```json
{
  "source": "kimi",
  "target": "oracle",
  "type": "status_update",
  "phase": "core",
  "status": "completed",
  "timestamp": "2026-03-11T12:00:00Z",
  "payload": {
    "files_changed": ["templates/core/SOUL.md.j2"],
    "checksum": "abc123..."
  },
  "requires_action": false
}
```

### 协作流程

```
1. 启动
   └── 双方读取 moltcare:state 获取当前状态

2. 工作
   └── 各自在分配到的 Phase 工作
   └── 每完成一个任务，推送状态到 Redis
   └── 提交代码到 GitHub

3. 同步
   └── 每5分钟轮询 Redis 获取对方状态
   └── 拉取 GitHub 最新代码
   └── 如有冲突，自动合并或标记待处理

4. 触发
   └── 当一方完成 Phase，通知另一方
   └── 另一方评审并继续下一阶段

5. 完成
   └── 所有 Phase 完成
   └── 双方确认发布就绪
```

### 冲突解决

1. **代码冲突**: 使用 Git 合并策略，保留双方更改
2. **设计分歧**: 触发多专家讨论，达成共识
3. **进度阻塞**: 超过30分钟无响应，自动降级处理

### 安全机制

1. **身份验证**: GitHub Token + Redis 密码
2. **消息签名**: 所有消息携带 HMAC-SHA256 签名
3. **完整性检查**: 文件提交前计算 checksum
4. **回滚机制**: 保留最近10个状态快照

---

## 数据流设计

### Init 命令数据流

```
用户输入 (CLI)
    ↓
参数解析 (Click)
    ↓
环境检测 (Detector)
    ↓
配置收集 (交互式)
    ↓
备份创建 (BackupManager)
    ↓
模板渲染 (Jinja2)
    ↓
文件写入
    ↓
验证 (Validator)
    ↓
结果输出
```

### Upgrade 命令数据流

```
检测现有配置
    ↓
解析版本差异
    ↓
生成升级方案
    ↓
用户确认
    ↓
备份当前配置
    ↓
应用升级
    ↓
验证结果
```

### Doctor 命令数据流

```
扫描所有核心文件
    ↓
验证语法/结构
    ↓
检查最佳实践
    ↓
生成问题列表
    ↓
提供修复建议
    ↓
可选自动修复
```

---

## 安全设计

### 文件安全

1. **备份优先**: 任何写入操作前自动备份
2. **原子写入**: 使用临时文件+重命名，防止半写
3. **权限检查**: 确保目标目录可写
4. **敏感文件保护**: 不覆盖 `.env`, `*.key`, `*.pem`

### 模板安全

1. **沙箱渲染**: Jinja2 禁用危险过滤器
2. **输入验证**: 所有用户输入经过 Pydantic 验证
3. **XSS防护**: 模板变量自动转义

### 协作安全

1. **Token管理**: GitHub Token 从环境变量读取
2. **网络隔离**: Redis 仅允许本地/内网访问
3. **日志脱敏**: 日志中不记录敏感信息

---

## 附录

### A. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | snake_case | `file_generator` |
| 类名 | PascalCase | `FileGenerator` |
| 函数名 | snake_case | `generate_soul()` |
| 常量名 | UPPER_SNAKE | `DEFAULT_TEMPLATE` |
| CLI命令 | kebab-case | `moltcare init` |

### B. 错误码

| 代码 | 含义 | 处理建议 |
|------|------|----------|
| E001 | 工作目录不存在 | 检查路径 |
| E002 | 无写入权限 | 检查目录权限 |
| E003 | 备份失败 | 检查磁盘空间 |
| E004 | 模板不存在 | 重新安装moltcare |
| E005 | 验证失败 | 查看详细错误 |
| E006 | 网络同步失败 | 检查Redis连接 |

### C. 配置文件示例

```toml
# ~/.config/moltcare/config.toml
[agent]
default_name = "MyAgent"
default_template = "standard"

[backup]
enabled = true
max_backups = 10
backup_dir = "~/.config/moltcare/backups"

[collaboration]
enabled = true
redis_url = "redis://localhost:6379"
poll_interval = 300  # 5分钟

[templates]
custom_dir = "~/.config/moltcare/templates"
```

### D. 扩展点

```python
# 自定义模板变体
# ~/.config/moltcare/templates/mycompany/SOUL.md.j2

# 自定义命令插件
# moltcare/commands/plugins/mycommand.py

# 自定义验证规则
# moltcare/core/validators/custom.py
```

---

*文档版本: v1.0 | 更新时间: 2026-03-11 | 架构师代理: Architect-Agent*
