# Moltbook 数据提取器

使用 Python + Playwright 自动化提取 Moltbook 用户主页数据，输出结构化 JSON，避免手动截图识别消耗 token。

## 功能

- ✅ 自动访问 Moltbook 用户主页
- ✅ 提取帖子标题、点赞数、评论数、发布时间
- ✅ 输出结构化 JSON
- ✅ 截图仅作为备份，不用于内容识别
- ✅ 支持滚动加载更多内容
- ✅ 多选择器策略，适配不同页面结构

## 安装依赖

```bash
# 安装 Python 依赖
pip install playwright

# 安装浏览器（首次运行需要）
playwright install chromium
```

## 使用方法

### 基本用法

```bash
# 使用默认用户 (LinLin_v1)
python scripts/moltbook_data_extractor.py

# 指定其他用户
python scripts/moltbook_data_extractor.py --user OtherUser

# 指定输出文件
python scripts/moltbook_data_extractor.py --user LinLin_v1 --output mydata.json
```

### 高级选项

```bash
# 显示浏览器窗口（调试用）
python scripts/moltbook_data_extractor.py --user LinLin_v1 --no-headless

# 增加滚动次数加载更多内容
python scripts/moltbook_data_extractor.py --user LinLin_v1 --max-scrolls 10

# 不滚动加载（仅提取首屏）
python scripts/moltbook_data_extractor.py --user LinLin_v1 --no-scroll

# 指定截图路径
python scripts/moltbook_data_extractor.py --user LinLin_v1 --screenshot backup.png
```

## 输出示例

```json
{
  "source": "moltbook",
  "username": "LinLin_v1",
  "url": "https://www.moltbook.com/u/LinLin_v1",
  "extraction_time": "2026-02-10T00:30:00",
  "total_posts": 12,
  "posts": [
    {
      "index": 1,
      "title": "今天的分享...",
      "likes": 128,
      "comments": 23,
      "publish_time": "2026-02-09",
      "raw_likes_text": "128赞",
      "raw_comments_text": "23评论"
    }
  ],
  "screenshot": "moltbook_LinLin_v1_20260210_003000.png",
  "errors": []
}
```

## 自定义选择器

如果页面结构变化，可修改脚本中的 `SELECTORS` 字典：

```python
SELECTORS = {
    "post_containers": [
        '.your-post-class',  # 添加你的选择器
        'article[data-type="post"]',
    ],
    "title": ['h2.title', '.content'],
    "likes": ['.like-count'],
    "comments": ['.comment-count'],
    "publish_time": ['time', '.date']
}
```

## 注意事项

1. **首次运行** 需要安装浏览器：`playwright install chromium`
2. **页面结构** 可能变化，如提取失败请检查选择器
3. **反爬机制** 频繁请求可能导致 IP 受限，建议控制频率
4. **登录态** 如需访问私密内容，可能需要先登录

## 故障排除

### 找不到帖子
- 检查选择器是否匹配当前页面结构
- 使用 `--no-headless` 查看浏览器实际渲染情况
- 增加 `--timeout` 值等待页面完全加载

### 数据提取为空
- 页面可能是动态加载，增加 `--max-scrolls` 值
- 检查是否需要登录才能查看内容

### 截图失败
- 确保有写入权限
- 检查磁盘空间是否充足
