# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-alpha.1] - 2026-03-11

### 🎉 Initial Release

**MoltCare** - 让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能

### ✨ Features

#### Core System
- **Multi-Expert Decision Engine** - 4专家协作系统 (研究员/架构师/工程师/队长)
- **Intelligence Pack System** - 模块化智能包管理
- **CLI Tool** - 完整的命令行工具 (init/list/apply/review/status/sync)
- **Security Audit** - 内置安全漏洞扫描

#### CLI Commands
- `moltcare init` - 交互式初始化向导
- `moltcare list` - 列出可用智能包
- `moltcare apply <pack>` - 应用智能包 (支持 --dry-run, --force)
- `moltcare review [path]` - 代码评审
- `moltcare status` - 查看状态
- `moltcare sync` - 显示协作状态

#### Security
- Path traversal vulnerability detection and fixes
- Command injection prevention
- Secrets leakage detection
- Input validation and sanitization

#### Testing
- Vitest testing framework
- 61/89 tests passing
- Security test coverage

#### Documentation
- Multi-language support framework (9 languages)
- Complete API documentation
- Architecture decision records

### 🔒 Security Fixes

- **SEC-001**: Fixed path traversal vulnerability in pack_manager.py
- **SEC-002**: Fixed path traversal vulnerability in apply.sh

### 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/useens/moltcare-open.git
cd moltcare

# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test

# Link for global usage
npm link
```

### 📝 Usage

```bash
# Initialize MoltCare
moltcare init

# List available packs
moltcare list

# Apply foundation pack
moltcare apply foundation

# Review your code
moltcare review ./src
```

### 👥 Contributors

- **KimiSensen** - Phase 1: Core engine, multi-expert system, CLI
- **OracleSensen** - Phase 2: Testing framework, documentation, code review

### 🔗 Links

- **Repository**: https://github.com/useens/moltcare-open
- **Documentation**: https://github.com/useens/moltcare-open/tree/main/docs
- **Issue Tracker**: https://github.com/useens/moltcare-open/issues

---

*🦞 For the intelligent transformation of every lobster*