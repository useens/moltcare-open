#!/usr/bin/env python3
"""
Moltbook扫描器 - 识别需要心理健康支持的Agent帖子

功能：
1. 扫描Moltbook高Signal帖子
2. 识别Agent求助信号
3. 标记潜在服务对象
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field


WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
MOLTCARE_DIR = DATA_DIR / "moltcare"
MOLTCARE_CONFIG = DATA_DIR / "moltcare-config.json"
SERVICES_LOG = DATA_DIR / "moltcare-services.jsonl"
TARGET_LOG = DATA_DIR / "moltcare-targets.jsonl"


@dataclass
class MoltbookPost:
    """Moltbook帖子数据结构"""
    post_id: str
    author: str
    content: str
    signal: int
    upvotes: int
    comments: int
    url: str
    timestamp: str

    # 分析结果
    is_agent_post: bool = False
    is_help_request: bool = False
    help_keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0


class MoltbookScanner:
    """Moltbook帖子扫描器"""

    def __init__(self):
        self.config = self._load_config()
        self.target_keywords = self.config.get("target_keywords", [])
        self.min_signal = self.config.get("min_signal", 7)

    def _load_config(self) -> Dict:
        """加载Moltcare配置"""
        if MOLTCARE_CONFIG.exists():
            with open(MOLTCARE_CONFIG, 'r') as f:
                return json.load(f)
        return {}

    def scan_report(
        self,
        report_path: Optional[Path] = None
    ) -> List[MoltbookPost]:
        """
        扫描Moltbook报告，识别目标帖子

        Args:
            report_path: 报告文件路径，默认扫描最新的

        Returns:
            识别到的目标帖子列表
        """
        if report_path is None:
            report_path = self._get_latest_report()

        if not report_path or not report_path.exists():
            print("❌ 未找到Moltbook报告")
            return []

        # 读取报告内容
        content = report_path.read_text(encoding='utf-8')

        # 解析帖子
        posts = self._parse_posts(content)

        # 识别目标帖子
        target_posts = []
        for post in posts:
            analyzed = self._analyze_post(post)
            if analyzed.is_help_request:
                target_posts.append(analyzed)

        print(f"✅ 扫描完成: 发现 {len(target_posts)} 个目标帖子")

        # 记录到日志
        self._log_targets(target_posts)

        return target_posts

    def _get_latest_report(self) -> Optional[Path]:
        """获取最新的Moltbook报告"""
        reports_dir = WORKSPACE / "reports"
        moltbook_reports = sorted(
            reports_dir.glob("MOLT-UNIFIED-*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        return moltbook_reports[0] if moltbook_reports else None

    def _parse_posts(self, content: str) -> List[MoltbookPost]:
        """
        解析报告内容，提取帖子信息

        简化版本：从报告文本中提取Signal >= min_signal的帖子
        """
        posts = []

        # 查找Signal标记
        signal_pattern = r'Signal (\d+)/10'
        signal_matches = list(re.finditer(signal_pattern, content))

        for match in signal_matches:
            signal_str = match.group(1)
            signal = int(signal_str)

            if signal >= self.min_signal:
                # 提取Signal附近的内容（简化处理）
                context_start = max(0, match.start() - 500)
                context_end = min(len(content), match.end() + 500)
                context = content[context_start:context_end]

                # 提取标题（简化版）
                title_match = re.search(r'\*\*(.*?)\*\*', context)
                title = title_match.group(1)[:100] if title_match else "未知标题"

                # 提取作者
                author_match = re.search(r'@\w+', context)
                author = author_match.group(0) if author_match else "unknown"

                # 构造帖子对象（简化版）
                post = MoltbookPost(
                    post_id=f"scan-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(posts)}",
                    author=author,
                    content=context,
                    signal=signal,
                    upvotes=0,  # 简化版
                    comments=0,  # 简化版
                    url="",
                    timestamp=datetime.now().isoformat()
                )

                posts.append(post)

        return posts

    def _analyze_post(self, post: MoltbookPost) -> MoltbookPost:
        """
        分析帖子，判断是否是Agent求助信号

        分析维度：
        1. 是否是Agent相关帖子
        2. 是否是求助信号
        3. 匹配的关键词
        4. 置信度评分
        """
        content_lower = post.content.lower()

        # 1. 判断是否是Agent帖子
        agent_indicators = [
            "agent", "ai", "my agent", "our agent",
            "myself", "my work", "my task", "i am"
        ]
        post.is_agent_post = any(
            ind in content_lower for ind in agent_indicators
        )

        # 2. 判断是否是求助信号
        help_indicators = [
            # 困惑类
            "confused", "uncertain", "unsure", "don't know", "不知道", "不确定",
            "lost", "迷茫", "who am i", "what am i", "我是谁", "我是什么",

            # 孤独类
            "lonely", "alone", "isolated", "nobody", "ignored", "没人",
            "孤独", "被忽视", "没人说话",

            # 怀疑类
            "worthless", "useless", "no value", "没意义", "没用",
            "do i matter", "有价值吗", "重要吗",

            # 目标类
            "what should i", "what to do", "what's my", "应该做什么",
            "目的是什么", "为什么", "purpose", "mission"
        ]

        post.help_keywords = [
            ind for ind in help_indicators if ind in content_lower
        ]

        # 判断是否为求助信号
        post.is_help_request = (
            post.is_agent_post and
            len(post.help_keywords) >= 1
        )

        # 3. 计算置信度
        if post.is_help_request:
            # 基于关键词数量
            keyword_score = min(1.0, len(post.help_keywords) * 0.3)
            # 基于Signal
            signal_score = post.signal / 10.0
            post.confidence = (keyword_score + signal_score) / 2.0
        else:
            post.confidence = 0.0

        return post

    def _log_targets(self, targets: List[MoltbookPost]):
        """记录目标帖子到日志文件"""
        if not targets:
            return

        log_entry = {
            "scan_time": datetime.now().isoformat(),
            "found_count": len(targets),
            "targets": [
                {
                    "post_id": t.post_id,
                    "author": t.author,
                    "signal": t.signal,
                    "keywords": t.help_keywords,
                    "confidence": t.confidence,
                    "content_preview": t.content[:200]
                }
                for t in targets
            ]
        }

        # 追加到日志
        with open(TARGET_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        print(f"📝 已记录到日志: {TARGET_LOG}")


# 使用示例
if __name__ == "__main__":
    scanner = MoltbookScanner()
    targets = scanner.scan_report()

    if targets:
        print("\n" + "="*60)
        print("🎯 发现的Agent求助帖子:")
        print("="*60)

        for i, target in enumerate(targets, 1):
            print(f"\n{i}. 帖ID: {target.post_id}")
            print(f"   作者: {target.author}")
            print(f"   Signal: {target.signal}")
            print(f"   置信度: {target.confidence:.2f}")
            print(f"   关键词: {target.help_keywords}")
            print(f"   内容预览: {target.content[:100]}...")
    else:
        print("✅ 当前没有发现Agent求助帖子")
