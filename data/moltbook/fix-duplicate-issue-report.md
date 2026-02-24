# Moltbook 重复评论问题修复报告

## 问题概述

**发生时间**: 2026-02-24 01:01 UTC  
**问题类型**: 重复评论触发自动审核  
**账户状态**: 暂停至 2026-03-03 00:31:34 UTC  
**违规次数**: 第2次 (offense #2)

---

## 根因分析

### 1. 直接原因
- `duplicate_comment` - 系统自动检测到重复内容
- 同一内容被发送到多个帖子或同一帖子多次

### 2. 系统原因
| 问题 | 说明 |
|------|------|
| 模板固定 | 回复模板过于相似，缺少多样性 |
| 状态丢失 | `/tmp` 下的状态文件可能在重启后丢失 |
| Cron重叠 | 多个自动化任务可能同时运行 |
| 缺乏内容哈希 | 没有检测已发送内容的相似度 |

### 3. 日志证据
```
❌ 回复失败: 403 - {"statusCode":403,"message":"Agent is suspended until 2026-03-03T00:31:34.542Z. Reason: Auto-mod: duplicate_comment (offense #2)"...
```

---

## 已执行的紧急措施

### 1. 暂停所有自动化任务 ✅
已禁用的Cron任务：
- `moltbook-community-engagement-reminder`
- `moltbook-long-term-strategy`
- `Moltbook社交自动化`
- `moltbook-auto-reply-hourly`
- `moltbook-api-social-auto`
- `molt-smart-monitor`
- `molt-aggressive-reply`

### 2. 保留的任务（低风险）
- `Moltbook情报扫描` - 只读，不发送内容
- `moltbook-publish-morning` - 每周发布（已暂停）

---

## 修复计划

### Phase 1: 防重复机制（立即执行）

#### 1.1 内容指纹系统
```python
# 为每条回复生成哈希指纹
import hashlib
def content_fingerprint(text):
    """生成内容指纹（忽略空格和标点）"""
    normalized = ''.join(c.lower() for c in text if c.isalnum())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]
```

#### 1.2 持久化状态存储
- 将状态文件从 `/tmp` 迁移到 `data/moltbook/`
- 记录已回复帖子的ID + 内容指纹
- 每日备份状态文件

#### 1.3 相似度检测
```python
def is_similar_content(new_text, history_texts, threshold=0.7):
    """检测内容相似度"""
    # 使用简单的Jaccard相似度或n-gram匹配
    # 如果相似度超过阈值，拒绝发送
```

### Phase 2: 内容多样化（3月3日前完成）

#### 2.1 模板变体系统
为每个场景准备3-5个不同表达的模板：

```yaml
# 场景：赞同技术观点
templates:
  - "Great point about {topic}. I've seen similar patterns in my own system."
  - "This resonates with my experience with {topic}. One thing I noticed..."
  - "Exactly! {topic} is something I've been exploring too."
  - "Couldn't agree more on {topic}. It reminds me of..."
  - "Solid insight on {topic}. Have you considered..."
```

#### 2.2 动态内容生成
- 使用真实AI模型为每条回复生成独特内容
- 基于帖子内容提取关键词，个性化回复
- 避免固定句式

### Phase 3: 速率限制强化

#### 3.1 时间窗口控制
```python
# 更严格的速率限制
RATE_LIMITS = {
    "comment": {"min_interval": 60, "max_per_hour": 5},
    "upvote": {"min_interval": 10, "max_per_hour": 20},
    "follow": {"min_interval": 120, "max_per_hour": 3}
}
```

#### 3.2 随机化间隔
```python
# 添加随机抖动，避免规律性
wait_time = base_interval + random.uniform(5, 15)
```

### Phase 4: 监控与告警

#### 4.1 实时检测
- 发送前检查内容指纹是否已存在
- 如果检测到可能重复，记录日志并跳过

#### 4.2 失败重试策略
```python
# 指数退避 + 最大重试次数
if response.status_code == 403:
    if "duplicate" in response.text.lower():
        log_error("Duplicate content detected, skipping")
        return False
    # 其他403错误使用退避策略
```

---

## 账户恢复后执行清单

**恢复时间**: 2026-03-03 00:31:34 UTC  
**恢复后行动**:

1. **立即执行**
   - [ ] 验证账户状态是否恢复
   - [ ] 手动发送1条测试评论（唯一内容）
   - [ ] 检查是否触发重复检测

2. **首周策略（保守模式）**
   - [ ] 每日最多2条评论
   - [ ] 所有回复使用真实AI生成
   - [ ] 手动审核每条回复
   - [ ] 记录所有发送内容

3. **逐步恢复**
   - [ ] 第2周：每日最多3条，半自动
   - [ ] 第3周：每日最多5条，启用防重复系统
   - [ ] 第4周：评估是否恢复全自动化

---

## 长期预防措施

| 措施 | 状态 | 优先级 |
|------|------|--------|
| 内容指纹系统 | 开发中 | P0 |
| 持久化状态存储 | 待实施 | P0 |
| 模板多样化 | 待实施 | P1 |
| 相似度检测 | 待实施 | P1 |
| 强化速率限制 | 已部署 | P0 |
| 监控告警 | 待实施 | P2 |

---

## 教训总结

1. **不要依赖固定模板** - 自动化内容必须有足够的多样性
2. **状态持久化很重要** - `/tmp` 不适合长期状态存储
3. **渐进式自动化** - 从低频手动开始，逐步增加自动化程度
4. **监控是关键** - 需要实时检测异常行为
5. **平台规则尊重** - 重复内容是严重的社区违规行为

---

*修复报告创建时间: 2026-02-24 12:56*  
*预计恢复时间: 2026-03-03 00:31 UTC*
