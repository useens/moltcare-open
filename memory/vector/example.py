#!/usr/bin/env python3
"""
使用示例 - 向量记忆系统

展示如何在代码中使用向量记忆系统
"""

# 示例 1: 基础搜索
print("=" * 60)
print("示例 1: 基础语义搜索")
print("=" * 60)

from search import MemorySearch

search = MemorySearch()

# 搜索与用户偏好相关的内容
results = search.search("用户偏好设置", top_k=3)
print(f"\n搜索 '用户偏好设置' 找到 {len(results)} 个结果:")
for r in results:
    print(f"  - [{r['score']:.3f}] {r['title']}")
    print(f"    文件: {r['file_path']}")
    print()

# 示例 2: 带过滤的搜索
print("=" * 60)
print("示例 2: 带标签过滤的搜索")
print("=" * 60)

results = search.query(
    "安全审计",
    top_k=3,
    filters={"tags": ["安全"]}
)

print(f"\n搜索 '安全审计' (带安全标签过滤) 找到 {len(results)} 个结果:")
for r in results:
    print(f"  - [{r.score:.3f}] {r.title}")
    if r.tags:
        print(f"    标签: {', '.join(r.tags[:3])}")

# 示例 3: 获取文档的所有块
print("\n" + "=" * 60)
print("示例 3: 获取特定文档的所有块")
print("=" * 60)

doc_results = search.get_document("modules/user-profile.md")
print(f"\nuser-profile.md 共有 {len(doc_results)} 个块")
if doc_results:
    print(f"第一个块标题: {doc_results[0].title}")
    print(f"第一个块预览: {doc_results[0].text[:100]}...")

# 示例 4: 获取相关文档
print("\n" + "=" * 60)
print("示例 4: 获取相关文档")
print("=" * 60)

related = search.get_related("modules/user-profile.md", top_k=3)
print(f"\n与 user-profile.md 相关的文档:")
for r in related:
    print(f"  - {r['title']} [{r['score']:.3f}]")

# 示例 5: 多个查询对比
print("\n" + "=" * 60)
print("示例 5: 多个查询对比")
print("=" * 60)

queries = [
    "技能安装",
    "安全协议",
    "错误处理",
    "架构设计",
]

for query in queries:
    results = search.search(query, top_k=1)
    if results:
        print(f"\n'{query}' -> {results[0]['title']} [{results[0]['score']:.3f}]")

print("\n" + "=" * 60)
print("示例完成!")
print("=" * 60)
