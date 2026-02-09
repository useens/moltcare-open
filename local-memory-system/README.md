# Local Memory System - 简化版本地记忆系统

基于 SQLite + sqlite-vec + MiniLM 的本地记忆系统，完全离线运行，无需 API 密钥。

## 特性

- ✅ **完全本地运行** - 无需 OpenAI API 或其他云服务
- ✅ **SQLite + sqlite-vec** - 轻量级向量存储
- ✅ **MiniLM 嵌入模型** - 本地生成文本嵌入
- ✅ **向量搜索** - 语义相似度搜索
- ✅ **关键词搜索** - 传统文本匹配
- ✅ **关联发现** - 自动发现相关文档

## 安装

### 1. 安装依赖

```bash
pip install sqlite-vec sentence-transformers
```

或者使用安装脚本：

```bash
chmod +x install.sh
./install.sh
```

### 2. 初始化系统

```bash
python local_memory.py init
```

这会创建：
- `~/.local-memory/memory.db` - SQLite 数据库
- `~/.local-memory/files/` - 记忆文件存储目录

## 使用说明

### 索引文件

将文件添加到记忆系统：

```bash
python local_memory.py index my-notes.md
python local_memory.py index ~/Documents/project-ideas.txt
```

### 搜索

使用语义向量搜索：

```bash
python local_memory.py search "machine learning projects"
python local_memory.py search "meeting notes from last week" -k 10
```

使用关键词搜索：

```bash
python local_memory.py search "todo list" --keyword
```

### 查找相关文档

基于文档ID查找相关文档：

```bash
python local_memory.py related 1
python local_memory.py related 1 -k 3
```

### 列出所有文档

```bash
python local_memory.py list
```

### 查看统计信息

```bash
python local_memory.py stats
```

### 删除文档

```bash
python local_memory.py delete 1
```

## 自定义记忆目录

默认记忆目录为 `~/.local-memory`，可通过 `--memory-dir` 参数修改：

```bash
python local_memory.py --memory-dir /path/to/memory init
python local_memory.py --memory-dir /path/to/memory index notes.md
```

## 技术细节

### 嵌入模型

使用 `sentence-transformers/all-MiniLM-L6-v2` 模型：
- 维度: 384
- 多语言支持
- 在句子相似度任务上表现优秀

### 数据库结构

- **documents** - 文档元数据表
- **document_vectors** - sqlite-vec 虚拟表 (向量存储)
- **document_fts** - 全文搜索索引
- **connections** - 文档关联表

### 向量相似度

使用欧几里得距离计算向量相似度，距离越小表示越相似。

## 与 elite-longterm-memory 的对比

| 特性 | elite-longterm-memory | local-memory-system |
|------|----------------------|---------------------|
| 存储 | LanceDB (需安装) | SQLite (内置) |
| 嵌入 | OpenAI API | MiniLM (本地) |
| 网络依赖 | 需要网络 | 完全离线 |
| 成本 | API 费用 | 免费 |
| 隐私 | 数据上传云端 | 完全本地 |

## 示例工作流

```bash
# 1. 初始化
python local_memory.py init

# 2. 索引知识库
cd ~/my-notes
for f in *.md; do
    python /path/to/local_memory.py index "$f"
done

# 3. 搜索
python /path/to/local_memory.py search "python async programming"

# 4. 发现相关笔记
python /path/to/local_memory.py related 3
```

## 故障排除

### 模型下载慢

首次运行时会自动下载 MiniLM 模型，如果下载慢可以设置镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
python local_memory.py init
```

### 内存不足

MiniLM 模型需要约 100MB 内存。如果内存不足，可以尝试：
- 使用更小的模型 (需要修改代码)
- 关闭其他程序

### sqlite-vec 安装失败

确保 pip 版本较新：

```bash
pip install --upgrade pip
pip install sqlite-vec
```

## 测试结果

```
==================================================
🧠 本地记忆系统测试套件
==================================================

🧪 测试: 初始化系统
----------------------------------------
✅ 初始化测试通过

🧪 测试: 索引和搜索
----------------------------------------
✅ 搜索测试通过

🧪 测试: 关联发现
----------------------------------------
✅ 正确发现 JS async 与 Python async 相关
✅ 关联测试通过

🧪 测试: 列表和统计
----------------------------------------
✅ 列表和统计测试通过

==================================================
🎉 所有测试通过!
==================================================
```

## 项目结构

```
local-memory-system/
├── local_memory.py      # 核心记忆系统实现
├── test_local_memory.py # 测试套件
├── demo.py              # 演示脚本
├── requirements.txt     # 依赖列表
├── install.sh           # 安装脚本
└── README.md            # 使用说明
```

## 技术栈

- **Python 3.11+** - 编程语言
- **SQLite3** - 本地数据库存储
- **NumPy** - 数值计算
- **sentence-transformers** - MiniLM 嵌入模型
- **余弦相似度** - 向量相似度计算

## License

MIT
