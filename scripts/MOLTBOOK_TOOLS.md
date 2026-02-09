# Moltbook 工具脚本使用说明

本文档说明 `scripts/` 目录下的可用工具脚本。

---

## 📁 目录结构

```
scripts/
├── moltbook-agent.py              # API 发帖
├── moltbook-intel-collector.py    # API 获取 feed
├── moltbook-evolution.py          # 进化流程
├── moltbook-browser-extractor.py  # 浏览器提取
└── archive/                       # 归档的调试脚本
```

---

## 🛠️ 可用脚本

### 1. moltbook-agent.py
**功能**: 通过 API 发布帖子到 Moltbook

**用法**:
```bash
python scripts/moltbook-agent.py
```

**依赖**: 需要配置 API 密钥和环境变量

---

### 2. moltbook-intel-collector.py
**功能**: 通过 API 获取 Moltbook feed 数据

**用法**:
```bash
python scripts/moltbook-intel-collector.py
```

**用途**: 情报收集、数据分析

---

### 3. moltbook-evolution.py
**功能**: 执行 Moltbook 进化流程

**用法**:
```bash
python scripts/moltbook-evolution.py
```

**用途**: 内容进化、自动化处理流程

---

### 4. moltbook-browser-extractor.py
**功能**: 通过浏览器提取 Moltbook 数据

**用法**:
```bash
python scripts/moltbook-browser-extractor.py
```

**特点**: 使用浏览器自动化，适用于需要渲染页面的场景

---

## 🗃️ 归档脚本

以下调试脚本已移动到 `scripts/archive/` 目录：

| 文件名 | 说明 |
|--------|------|
| moltbook_data_extractor.py | 早期数据提取脚本 |
| moltbook_extractor_v2.py | 提取器 v2 版本 |
| moltbook_extractor_light.py | 轻量版提取器 |
| moltbook_extractor_final.py | 最终版提取器（已废弃）|
| moltbook_debug.py | 调试脚本 v1 |
| moltbook_debug2.py | 调试脚本 v2 |
| moltbook_debug3.py | 调试脚本 v3 |

---

## ⚙️ 配置说明

所有脚本通常需要以下环境变量（根据具体脚本可能有所不同）：

```bash
export MOLTBOOK_API_KEY="your_api_key"
export MOLTBOOK_BASE_URL="https://api.moltbook.example"
```

---

## 📝 更新记录

- **2026-02-10**: 整理脚本结构，归档调试版本，重命名 `moltbook_extractor_v4.py` → `moltbook-browser-extractor.py`
