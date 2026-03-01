---
name: web-search-extraction
description: Playwright+Chromium 网络搜索和深度提取技能。使用 Headless Chrome 进行网页内容结构化提取，支持标题、段落、链接等元素提取，避免截图方式节省 tokens。
---

# Web Search Extraction Skill

# Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Understand user goal
- [ ] Step 2: Select approach
- [ ] Step 3: Ask user preferences (format, scope)
- [ ] Step 4: Execute the task
- [ ] Step 5: Summarize results
```


## 概述

基于 Playwright + Chromium 的网页内容深度提取技能。提供结构化文本提取替代传统截图方式，显著降低 token 消耗。

## 核心功能

### 1. 网络搜索
- 使用 Playwright 访问搜索引擎
- 提取搜索结果（标题、URL、摘要）
- 支持多个搜索结果

### 2. 深度页面提取
- **页面标题**: 提取文档 title
- **内容结构**: 提取 H1-H3 标题
- **正文段落**: 提取关键段落（限制数量和长度）
- **相关链接**: 提取页面内链接

### 3. 反爬保护
- 自定义 User-Agent
- 支持处理 Cookie 同意弹窗
- 延迟控制

## 使用方法

### 直接调用工具

```bash
# 基本搜索（2个结果）
python3 tools/web_extractor.py "搜索关键词" 2

# 搜索并提取详细内容
python3 tools/web_extractor.py "搜索关键词" 3
```

### 输出格式

结果以 Markdown 格式输出：

```markdown
# 搜索结果: [查询]

*搜索时间: [时间]*

## 结果 1: [标题]

**URL**: [链接]
**摘要**: [摘要描述]

### 页面标题
[页面标题]

### 主要内容结构
- [H1] 标题1
- [H2] 标题2

### 关键内容
[段落内容...]

### 相关链接
- [链接文本](URL)
```

### 在多专家决策引擎中使用

```python
# 研究员专家会自动调用
from scripts.autonomous_decision_engine import ExpertPanel

panel = ExpertPanel()
opinion = panel._researcher_perspective(context)

# 分析中会包含网络搜索结果
print(opinion.analysis)
```

## 配置选项

### 环境要求
- Python 3.10+
- Playwright: `pip install playwright`
- Chromium: `playwright install chromium`

### 工作模式

| 模式 | 说明 |
|------|------|
| `headless=True` | 无头模式（默认，服务器环境推荐） |
| `headless=False` | 有头模式（调试时使用） |

### 超时设置
```python
# 页面访问超时
await page.goto(url, timeout=30000)  # 30秒

# 元素等待超时
await page.wait_for_timeout(2000)  # 2秒
```

## 集成示例

### 1. 作为独立工具

```python
import asyncio
from tools.web_extractor import WebExtractor

async def search():
    extractor = WebExtractor(headless=True)
    results = await extractor.search_google("AI agents", 3)
    print(f"找到 {len(results)} 条结果")

asyncio.run(search())
```

### 2. 批量提取

```python
# 提取多个搜索结果
data = await extractor.search_and_extract("deep learning", 3)

# 访问详细内容
for result in data["results"]:
    if "content" in result:
        print(result["content"]["title"])
        for p in result["content"]["paragraphs"][:5]:
            print(p)
```

### 3. 与多专家系统集成

```python
# 在专家讨论中使用
def _researcher_perspective(self, context):
    query = extract_search_query(context.task_description)
    results = self._do_web_search(query, max_results=3)

    # 将搜索结果整合到分析中
    analysis = f"""
    搜索查询: {query}
    找到 {len(results)} 条相关结果:
    {format_results(results)}
    """
    return ExpertOpinion(
        expert_name="🔍 研究员",
        perspective="数据验证与事实核查 (网络搜索)",
        analysis=analysis,
        recommendations=generate_recommendations(results),
        confidence=9
    )
```

## 数据源配置

### 演示模式（当前）

由于搜索引擎反爬限制，当前使用预设真实网站进行演示：

- `https://docs.python.org/3/` - Python 文档
- `https://developer.mozilla.org/en-US/` - MDN Web Docs
- `https://httpbin.org/` - HTTP 测试工具

### 真实搜索（需要配置）

如需真实搜索结果，配置以下选项之一：

#### 选项 A: Brave Search API
```python
# 修改 tools/web_extractor.py 中的搜索函数
import requests

url = f"https://api.search.brave.com/res/v1/web/search?q={query}"
headers = {"X-Subscription-Token": "YOUR_API_KEY"}
```

#### 选项 B: 付费搜索服务
- SerpAPI (`https://serpapi.com`)
- ScrapingBee (`https://scrapingbee.com`)
- Google Custom Search API

## 调试技巧

### 查看浏览器行为
```python
# 有头模式查看实际渲染
browser = await p.chromium.launch(headless=False)
page = await context.new_page()
```

### 保存调试截图
```python
await page.screenshot(path="debug.png")
```

### 查看网络请求
```python
# 监控网络活动
page.on("request", lambda request: print(request.url))
```

## 故障排除

### 问题: 找不到结果
**原因**: 选择器变化或反爬机制
**解决**: 
- 使用 `page.wait_for_selector()` 等待元素
- 检查页面结构
- 更新选择器

### 问题: 超时
**原因**: 网络问题或页面加载慢
**解决**:
- 增加 `timeout` 参数
- 使用 `page.wait_for_load_state("networkidle")`

### 问题: Playwright 未安装
```bash
pip install playwright
playwright install chromium
```

## 性能优化

### 1. 异步并发
```python
# 并发提取多个页面
tasks = [extract_page(url) for url in urls]
results = await asyncio.gather(*tasks)
```

### 2. 缓存机制
```python
# 缓存已提取的内容
if url in cache:
    return cache[url]
else:
    content = await extract_page(url)
    cache[url] = content
    return content
```

### 3. 限制提取量
```python
# 限制段落数量
paragraphs = paragraphs[:10]  # 只取前10个段落

# 限制文本长度
if sum(len(p) for p in paragraphs) > max_length:
    break
```

## 路由集成

在 `scripts/run-with-route.sh` 中添加路由规则：

```bash
web-search)
    # 网络搜索和提取
    "$@"
    ;;
```

## 质量检查清单

- [ ] 语法检查: `python3 -m py_compile tools/web_extractor.py`
- [ ] Playwright 安装: `playwright install chromium`
- [ ] 测试基本搜索: `python3 tools/web_extractor.py "test" 1`
- [ ] 验证提取结果包含标题、结构、内容
- [ ] 检查超时设置合理（15-30秒）
- [ ] 确认 headless 模式用于生产环境

## 版本历史

### v1.0.0 (2026-02-25)
- ✅ 初始版本
- ✅ Playwright+Chromium 深度提取
- ✅ 多专家决策引擎集成
- ✅ 演示模式（预设真实网站）
- ✅ 结构化 Markdown 输出格式

## 扩展方向

- [ ] 集成 Brave Search API
- [ ] 支持更多搜索引擎（Bing、DuckDuckGo）
- [ ] 添加智能缓存机制
- [ ] 支持代理池
- [ ] PDF 内容提取
- [ ] 视频字幕提取


## Output Formats

| Format | Use Case | Command |
|--------|----------|---------|
| **Quick** | Preview in chat | (no flag) |
| **JSON** | Machine processing | `--format json` |
| **Markdown** | Human readable | `--format md` |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `COMMAND_NOT_FOUND` | Tool not installed | Install the required CLI tool |
| `AUTH_ERROR` | Missing/invalid token | Check `.env` file |
| `NOT_FOUND` | Resource doesn't exist | Verify ID/name |

