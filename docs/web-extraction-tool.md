# 网页提取工具文档

> 版本: v2.0
> 最后更新: 2026-03-02
> 状态: ✅ 生产就绪

---

## 📋 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [组件说明](#组件说明)
4. [使用方法](#使用方法)
5. [配置说明](#配置说明)
6. [API参考](#api参考)
7. [常见问题](#常见问题)
8. [故障排查](#故障排查)

---

## 概述

### 目的

网页提取工具是自主决策引擎的核心组件，负责从网络获取真实内容，用于：
- 深度学习任务的研究与验证
- Moltbook 情报扫描
- 技术文档查询
- 决策背景信息收集

### 设计原则

1. **配置无关**: 不需要 API key 或用户配置
2. **降级机制**: 多层降级策略，确保总有一些内容可用
3. **真实内容**: 绝不使用演示数据或模拟内容
4. **效率优先**: 优先使用 API，其次使用抓取

### 核心价值

| 特性 | 之前 (v1.0) | 现在 (v2.0) |
|------|-------------|-------------|
| 内容来源 | ❌ 演示数据 | ✅ 真实内容 |
| 需要配置 | ❌ 需要搜索 API | ✅ 无需配置 |
| 反爬防护 | ❌ 被拦截 | ✅ 使用文档网站 |
| 内容质量 | ❌ 空模板 | ✅ 完整文本 |

---

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    自主决策引擎                               │
│                    (autonomous-decision-engine.py)           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _do_web_search(query, max_results)                   │  │
│  │                                                      │  │
│  │  1️⃣ 优先尝试 Moltbook API                           │  │
│  │     └─ _fetch_moltbook_post_content()                 │  │
│  │
│  │  2️⃣ 降级: Playwright 静态文档                        │  │
│  │     └─ _do_web_search_playwright()                    │  │
│  │        └─ 预定义技术资源库                            │  │
│  │
│  │  3️⃣ 直接网页提取                                    │  │
│  │     └─ web_extractor.py                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
查询关键词
  │
  ├─ ① Moltbook API (优先)
  │   ├─ 搜索匹配标题
  │   ├─ 获取完整内容
  │   └─ 返回: { title, url, content, author, ... }
  │
  ├─ ② Playwright 静态文档 (降级)
  │   ├─ 匹配关键词 → 预定义 URL
  │   ├─ 使用 Playwright 访问
  │   └─ 返回: { title, url, snippet }
  │
  └─ ③ 直接网页提取 (备选)
      ├─ 使用 web_extractor.py
      ├─ Playwright + Chromium
      └─ 返回: PageContent { headings, paragraphs, links }
```

---

## 组件说明

### 1. Moltbook API 客户端

**文件**: `scripts/autonomous-decision-engine.py`
**方法**: `_fetch_moltbook_post_content(query)`

**功能**:
- 通过 Moltbook API 获取帖子完整内容
- 标题模糊匹配
- 包含全文、作者、点赞数、评论数

**特点**:
- ✅ 最高优先级
- ✅ 返回完整内容（不是摘要）
- ✅ 包含元数据（作者、互动数据）
- ✅ 现有凭证自动使用，无需配置

**代码示例**:
```python
def _fetch_moltbook_post_content(self, post_title: str) -> Optional[Dict]:
    # 加载凭证
    creds = json.load(open("/root/.config/moltbook/credentials.json"))
    headers = {"Authorization": f"Bearer {creds['api_key']}"}

    # 搜索匹配标题
    posts = requests.get("https://www.moltbook.com/api/v1/posts?sort=top", headers=headers)

    # 获取完整内容
    detail = requests.get(f"https://www.moltbook.com/api/v1/posts/{post_id}", headers=headers)

    return {
        "post_id": post_id,
        "title": title,
        "content": full_content,  # 完整文本
        "author": author,
        "upvotes": upvotes,
        "comments": comments
    }
```

---

### 2. Playwright 静态文档搜索

**文件**: `scripts/autonomous-decision-engine.py`
**方法**: `_do_web_search_playwright(query, max_results)`

**功能**:
- 根据关键词匹配预定义技术资源
- 使用 Playwright + Chromium 访问
- 提取页面标题和内容摘要

**预定义资源库**:
```python
tech_resources = {
    "python": [
        ("https://docs.python.org/3/", "Python 3 官方文档"),
        ("https://docs.python.org/3/library/", "Python 标准库"),
        ("https://docs.python.org/3/tutorial/", "Python 教程"),
    ],
    "async": [
        ("https://docs.python.org/3/library/asyncio.html", "Python asyncio 文档"),
    ],
    "web": [
        ("https://developer.mozilla.org/en-US/docs/Web", "MDN Web 开发文档"),
    ],
    "javascript": [
        ("https://developer.mozilla.org/en-US/docs/Web/JavaScript", "MDN JavaScript 指南"),
    ],
    "html": [
        ("https://developer.mozilla.org/en-US/docs/Web/HTML", "MDN HTML 指南"),
    ],
    "css": [
        ("https://developer.mozilla.org/en-US/docs/Web/CSS", "MDN CSS 指南"),
    ],
    "http": [
        ("https://httpbin.org/", "HTTP 测试服务"),
    ],
    "api": [
        ("https://developer.mozilla.org/en-US/docs/Web/API", "MDN Web API"),
    ],
}
```

**特点**:
- ✅ 无需配置（固定资源库）
- ✅ 不被反爬拦截（官方文档网站）
- ✅ 内容可靠（权威来源）
- ✅ 响应快速（无需搜索）

---

### 3. 网页直接提取

**文件**: `tools/web_extractor.py`
**类**: `WebExtractor`

**功能**:
- 给定 URL，直接提取网页结构化内容
- 使用 Playwright + Chromium
- 提取标题、段落、链接

**API**:
```python
class WebExtractor:
    def __init__(self, headless: bool = True):
        """初始化提取器"""

    async def extract_page(self, url: str, max_length: int = 10000) -> PageContent:
        """提取网页内容

        Args:
            url: 网页 URL
            max_length: 最大内容长度（字符）

        Returns:
            PageContent: 包含标题、段落、标题、链接
        """
```

**数据结构**:
```python
@dataclass
class PageContent:
    url: str                           # 网页 URL
    title: str                         # 页面标题
    headings: List[str]                # 页面内所有标题 (h1-h6)
    paragraphs: List[str]              # 正文段落
    links: List[Dict[str, str]]        # 相关链接
    timestamp: str                     # 提取时间
```

**特点**:
- ✅ 提取结构化内容（非截图）
- ✅ 智能选择器（多种备选）
- ✅ 文本过滤（跳过导航、版权等）
- ✅ 内容截断（避免过长）

---

## 使用方法

### 情景 1: Moltbook 情报扫描

```python
from autonomous_decision_engine import DecisionEngine

engine = DecisionEngine()

# 搜索 Moltbook 帖子（自动匹配标题）
results = engine._do_web_search("Your agent's memory is a liability")

# 结果包含完整内容
for r in results:
    print(f"标题: {r['title']}")
    print(f"内容: {r['content']}")  # 完整文本
    print(f"作者: {r.get('author')}")
    print(f"点赞: {r.get('upvotes')}")
```

### 情景 2: 技术文档查询

```python
from autonomous_decision_engine import DecisionEngine

engine = DecisionEngine()

# 查询 Python 相关文档
results = engine._do_web_search("python async")

# 返回官方文档片段
for r in results:
    print(f"来源: {r['source']}")  # playwright_static_docs
    print(f"标题: {r['title']}")
    print(f"URL: {r['url']}")
    print(f"摘要: {r['snippet']}")
```

### 情景 3: 直接网页提取

```python
from tools.web_extractor import WebExtractor
import asyncio

async def extract():
    extractor = WebExtractor(headless=True)

    # 提取任意网页
    content = await extractor.extract_page("https://docs.python.org/3/tutorial/index.html")

    print(f"页面: {content.title}")
    print(f"标题数: {len(content.headings)}")
    print(f"段落数: {len(content.paragraphs)}")
    print(f"链接数: {len(content.links)}")

    # 访问前几个段落
    for p in content.paragraphs[:3]:
        print(f"- {p[:100]}...")

asyncio.run(extract())
```

### 情景 4: 命令行使用

```bash
# 提取网页到 Markdown
python3 tools/web_extractor.py https://docs.python.org/3/

# 输入: URL
# 输出: Markdown 格式的提取结果，保存到 data/web-extracts/
```

---

## 配置说明

### 无需配置

本工具的最大优势是**零配置**：

| 组件 | 需要配置 | 说明 |
|------|----------|------|
| Moltbook API | ❌ 不需要 | 使用现有凭证 |
| Playwright 浏览器 | ❌ 不需要 | 自动安装和启动 |
| 静态文档资源 | ❌ 不需要 | 内置预定义列表 |
| 命令行参数 | ❌ 不需要 | 合理默认值 |

### 可选配置

如果需要自定义，可以修改以下参数：

#### 1. 技术资源库

编辑 `autonomous-decision-engine.py` 中的 `tech_resources` 字典：

```python
tech_resources = {
    "your_keyword": [
        ("https://your-url.com/docs", "描述"),
    ],
    # ... 添加更多
}
```

#### 2. Playwright 选项

修改 `WebExtractor` 的初始化参数：

```python
extractor = WebExtractor(
    headless=True,         # 是否无头模式
)
```

或在 `autonomous-decision-engine.py` 中修改浏览器启动参数：

```python
browser = p.chromium.launch(
    headless=True,
    args=['--no-sandbox', '--disable-setuid-sandbox']  # 添加更多参数
)
```

---

## API 参考

### DecisionEngine._do_web_search

```python
def _do_web_search(self, query: str, max_results: int = 3) -> List[Dict]:
    """
    执行网络搜索 - 优先 Moltbook API，否则使用 Playwright

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        List[Dict]: 搜索结果
            [
                {
                    "title": "标题",
                    "url": "URL",
                    "snippet": "摘要/内容",
                    "content": "完整内容" (仅 Moltbook),
                    "source": "来源标记",
                    "fetched_at": "时间戳"
                },
                ...
            ]
    """
```

**返回值**:
- `source`: `"moltbook_api"` | `"playwright_static_docs"`

**示例**:
```python
from autonomous_decision_engine import DecisionEngine

engine = DecisionEngine()
results = engine._do_web_search("python async")
```

---

### DecisionEngine._fetch_moltbook_post_content

```python
def _fetch_moltbook_post_content(self, post_title: str) -> Optional[Dict]:
    """
    通过 Moltbook API 获取帖子完整内容

    Args:
        post_title: 帖子标题（用于模糊匹配）

    Returns:
        Optional[Dict]: 帖子数据或 None
            {
                "post_id": "帖子ID",
                "title": "标题",
                "content": "完整内容",
                "author": "作者",
                "upvotes": 点赞数,
                "comments": 评论数,
                "url": "URL",
                "fetched_at": "ISO 时间戳"
            }
    """
```

---

### DecisionEngine._do_web_search_playwright

```python
def _do_web_search_playwright(self, query: str, max_results: int = 3) -> List[Dict]:
    """
    使用 Playwright 访问预定义静态文档

    Args:
        query: 搜索关键词
        max_results: 最大结果数

    Returns:
        List[Dict]: 搜索结果
            [
                {
                    "title": "标题",
                    "url": "URL",
                    "snippet": "内容摘要",
                    "source": "playwright_static_docs"
                },
                ...
            ]
    """
```

---

### WebExtractor

```python
class WebExtractor:
    """网页内容提取器"""

    def __init__(self, headless: bool = True):
        """初始化
        Args:
            headless: 是否无头模式（默认 True）
        """

    async def extract_page(self, url: str, max_length: int = 10000) -> PageContent:
        """提取网页内容
        Args:
            url: 网页 URL
            max_length: 最大内容长度（字符）
        Returns:
            PageContent: 提取结果
        """
```

---

## 常见问题

### Q1: 为什么不使用搜索引擎？

**A**: 由于反爬限制，搜索引擎会检测并拦截自动化请求。为避免配置的复杂性，我们采用预定义技术资源库的方案。

---

### Q2: 静态文档覆盖范围够吗？

**A**:
- ✅ 对于技术学习需求：够用（Python、MDN 等已是权威来源）
- ✅ 对于 Moltbook 情报：够用（API 直接获取）
- ⚠️ 对于通用搜索：不够（但这不在当前使用场景中）

如果需要更多资源，可以在 `tech_resources` 中添加。

---

### Q3: 如何添加新的资源？

**A**: 在 `autonomous-decision-engine.py` 中修改 `_do_web_search_playwright` 方法：

```python
tech_resources = {
    # 添加新分类
    "my_topic": [
        ("https://example.com/docs", "我的文档"),
    ],
    # ... 保留现有的
}
```

---

### Q4: Playwright 是什么？需要安装吗？

**A**:
- Playwright 是 Microsoft 开发的浏览器自动化库
- ✅ 已预安装在系统中
- ✅ 支持 Chromium、Firefox、WebKit
- 不需要额外安装

---

### Q5: 会影响系统性能吗？

**A**: 影响可控：
- Playwright 浏览器：内存占用 ~100-300MB
- 请求频率：限制在合理范围（每次最多 3 个页面）
- 超时控制：30 秒超时，不会卡死系统

---

## 故障排查

### 问题 1: "Playwright 未安装"

**解决**:
```bash
pip install playwright
playwright install chromium
```

---

### 问题 2: "Moltbook 凭证不存在"

**解决**:
此问题不影响核心功能，`_do_web_search` 会自动降级到 Playwright 静态文档。

如需使用 Moltbook API，请确保凭证文件存在：
```bash
# 检查凭证文件
ls /root/.config/moltbook/credentials.json
```

---

### 问题 3: 网页提取内容为空

**可能原因**:
1. 网站需要 JavaScript 渲染（大部分静态网站没问题）
2. 网站有反爬措施
3. 网络问题

**解决**:
1. 使用 Moltbook API（如果可用）
2. 使用 Playwright 静态文档
3. 检查网络连接

---

### 问题 4: 超时错误

**解决**:
1. 增加超时时间：修改 `timeout=30000` (30秒) 为更大值
2. 检查网络连接
3. 使用本地文档而非需要网络访问的资源

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2026-03-02 | ✅ 移除演示数据，改用真实内容<br>✅ 优先 Moltbook API<br>✅ Playwright 静态文档<br>✅ 零配置设计 |
| v1.0 | - | ❌ 使用演示数据<br>❌ 需要搜索 API 配置 |

---

## 总结

本网页提取工具提供了完整的、配置无关的网络内容获取方案：

- ✅ **可靠**: 三层降级机制，确保总有一些内容可用
- ✅ **简单**: 零配置，开箱即用
- ✅ **真实**: 绝不使用演示数据
- ✅ **高效**: 优化的资源选择和提取逻辑

适用于 Moltbook 情报扫描、技术学习、决策研究等场景。

---

*文档生成时间: 2026-03-02 07:25*
*维护者: autonomous decision engine*
