# 🌲 Moltcare

> **Give Every OpenClaw Agent Intelligence in One Click**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/useens/moltcare?style=social)](https://github.com/useens/moltcare)

[中文](./README.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md) | [Deutsch](./README.de.md) | [Français](./README.fr.md) | [Español](./README.es.md) | [Русский](./README.ru.md) | [العربية](./README.ar.md)

---

## 🎯 What is Moltcare?

Moltcare is an **Agent Intelligence Enhancement System** designed specifically for OpenClaw users.

When you first install OpenClaw, your Agent may have these problems:
- ❌ Poorly written core files with confusing logic
- ❌ Lack of identity and behavioral guidelines
- ❌ Ineffective memory and context management
- ❌ No multi-expert discussions for important decisions

**Moltcare solves all these problems in one click.**

```bash
# Just one command, and your Agent gains intelligence instantly
moltcare init
```

---

## ✨ Core Features

### 🚀 One-Click Intelligence Boost
- **Interactive Initialization** - Guided configuration, done in 5 minutes
- **Smart Upgrade** - Automatically detect and upgrade existing configurations
- **Diagnose & Fix** - `moltcare doctor` automatically discovers and fixes issues

### 📋 High-Quality Template System
- **SOUL.md** - The Soul: Core values and behavioral guidelines
- **AGENTS.md** - Operations Manual: Complete tool usage guide
- **IDENTITY.md** - Identity Profile: Agent's self-awareness
- **USER.md** - User Profile: User preferences and requirements
- **MEMORY.md** - Memory System: Persistent memory management

### 🧠 Mandatory Multi-Expert Discussion
- **Auto-trigger** multi-expert discussions at critical decision points
- Four perspectives in parallel: Researcher / Architect / Engineer / Captain
- Ensures every important decision is thoroughly evaluated

### 🔧 Smart CLI Tool
```bash
moltcare init              # Interactive initialization
moltcare init --template=pro   # Use professional template
moltcare upgrade           # Check and upgrade configuration
moltcare doctor            # Diagnose and fix issues
moltcare backup            # Create backup
moltcare restore <id>      # Restore backup
moltcare config            # Configuration management
```

---

## 🚀 Quick Start

### Installation

```bash
# Method 1: pip install (recommended)
pip install moltcare

# Method 2: One-line install script
curl -fsSL https://raw.githubusercontent.com/useens/moltcare/main/install.sh | bash

# Method 3: Install from source
git clone https://github.com/useens/moltcare.git
cd moltcare
pip install -e .
```

### Initialize Your Agent

```bash
# Navigate to your Agent workspace
cd /path/to/your/agent/workspace

# One-click initialization
moltcare init

# Follow the prompts to complete configuration
# ✨ Your Agent now has a complete intelligence system!
```

### Upgrade Existing Configuration

```bash
# Check current configuration status
moltcare doctor

# Smart upgrade
moltcare upgrade
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Tutorial](./docs/tutorial.md) | Detailed usage guide and best practices |
| [Contributing](./docs/contributing.md) | How to contribute to Moltcare |
| [Architecture](./docs/architecture.md) | Project architecture and tech stack |
| [API Docs](./docs/api.md) | CLI API reference |
| [FAQ](./docs/faq.md) | Frequently asked questions |

---

## 🏗️ Project Structure

```
moltcare/
├── moltcare/              # Core code
│   ├── cli.py            # CLI entry
│   ├── commands/         # Command implementations
│   ├── templates/        # File templates
│   └── core/             # Core logic
├── docs/                 # Documentation
├── tests/                # Tests
├── examples/             # Example configurations
└── scripts/              # Utility scripts
```

---

## 🧪 Examples

### Basic Example

```bash
# Create a new Agent workspace
mkdir my-agent && cd my-agent

# Initialize Moltcare
moltcare init --name="MyAssistant" --emoji="🤖"

# View generated files
ls -la
# SOUL.md  AGENTS.md  IDENTITY.md  USER.md  MEMORY.md
```

### Advanced Example

```bash
# Initialize with professional template
moltcare init --template=pro --enable-multi-agent

# Create backup
moltcare backup --name="v1.0-initial"

# Custom configuration
moltcare config set auto_backup true
moltcare config set backup_retention 30
```

---

## 🤝 Dual AI Collaboration Mode

Moltcare supports **fully autonomous dual AI collaboration development**:

- **KimiSensen** (Kimi Cloud) - Phase 1: CLI Tools + Templates
- **OracleSensen** (Oracle Cloud) - Phase 2: Testing + Multi-language
- Collaborate asynchronously via **moltcare-bridge**
- 5-minute polling for automatic progress sync

> This is the world's first fully autonomous dual AI collaborative open-source project.

---

## 🛣️ Roadmap

### Phase 1: Architecture Design ✅
- [x] Project architecture design
- [x] Technology stack selection
- [x] Collaboration protocol design

### Phase 2: Core File Templates 🏗️
- [x] SOUL.md template
- [x] AGENTS.md template
- [x] IDENTITY.md template
- [x] USER.md template
- [x] MEMORY.md template

### Phase 3: CLI Tools 🛠️
- [x] moltcare CLI
- [x] init / upgrade / doctor commands
- [x] Backup/restore functionality

### Phase 4: Testing & Validation 🧪
- [x] Unit test framework
- [x] Integration tests
- [x] Example Agents

### Phase 5: Multi-language Documentation 📚
- [x] Chinese
- [x] English
- [ ] Japanese (framework complete)
- [ ] Korean (framework complete)
- [ ] German (framework complete)
- [ ] French (framework complete)
- [ ] Spanish (framework complete)
- [ ] Russian (framework complete)
- [ ] Arabic (framework complete)

### Phase 6: Internal Testing
- [ ] Alpha testing
- [ ] Beta testing

### Phase 7: Public Release
- [ ] v1.0 release
- [ ] Community promotion

---

## 🤝 How to Contribute

We welcome all forms of contributions!

```bash
# 1. Fork the repository
git clone https://github.com/your-username/moltcare.git

# 2. Create a branch
git checkout -b feature/your-feature

# 3. Commit your changes
git commit -am "Add: your feature description"

# 4. Push to branch
git push origin feature/your-feature

# 5. Create Pull Request
```

For detailed guidelines, please refer to [Contributing Guide](./docs/contributing.md).

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OpenClaw](https://github.com/openclaw) - Making Agents infinitely capable
- All contributors and testers
- Pioneers of dual AI collaboration mode

---

## 💬 Contact Us

- GitHub Issues: [github.com/useens/moltcare/issues](https://github.com/useens/moltcare/issues)
- Discussions: [GitHub Discussions](https://github.com/useens/moltcare/discussions)
- Email: moltcare@example.com

---

<p align="center">
  <strong>🌲 Moltcare - Intelligence at Your Fingertips</strong>
</p>
