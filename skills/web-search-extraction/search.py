#!/usr/bin/env python3
"""
Web Search Extraction Skill - Playwright+Chromium 深度框架

技能路由: web-search-extraction
依赖: playwright, chromium

使用:
  python3 skills/web-search-extraction/search.py "关键词" [结果数量]
"""

import sys
import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 导入主 web_extractor
SKILL_DIR = Path(__file__).parent
WORKSPACE = SKILL_DIR.parent.parent
WEB_EXTRACTOR = WORKSPACE / "tools" / "web_extractor.py"

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str

class WebSearchExtractionSkill:
    """Web Search Extraction Skill - 技能接口"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.name = "web-search-extraction"
        self.version = "1.0.0"

    async def search(self, query: str, num_results: int = 3) -> List[Dict]:
        """搜索 - 调用底层 web_extractor 工具"""
        import subprocess
        import re

        # 调用真实的 web_extractor
        cmd = [
            sys.executable,
            str(WORKSPACE / "tools" / "web_extractor.py"),
            query,
            str(num_results)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(WORKSPACE)
        )

        if result.returncode == 0:
            # 提取结果数据
            data = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "results": []
            }

            # 解析输出（简单解析）
            url_matches = re.findall(r'\*\*URL\*\*:\s*(https?://[^\s\)]+)', result.stdout)
            title_matches = re.findall(r'##\s+结果\s+\d+:\s*(.+?)\n', result.stdout)
            snippet_matches = re.findall(r'\*\*摘要\*\*:\s*(.+?)\n', result.stdout)

            count = min(len(url_matches), len(title_matches), len(snippet_matches))
            for i in range(count):
                data["results"].append({
                    "title": title_matches[i].strip(),
                    "url": url_matches[i].strip(),
                    "snippet": snippet_matches[i].strip()
                })

            return data
        else:
            return {
                "query": query,
                "error": result.stderr,
                "results": []
            }

    def info(self) -> Dict:
        """返回技能信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "Playwright+Chromium 网络搜索和深度提取框架",
            "capabilities": [
                "web_search",
                "page_extraction",
                "structured_content",
                "markdown_output"
            ]
        }

async def main():
    """技能入口点"""
    import sys

    # 显示帮助
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print("=" * 60)
        print("Web Search Extraction Skill v1.0.0")
        print("=" * 60)
        print("\n使用:")
        print("  python3 skills/web-search-extraction/search.py <关键词> [结果数量]")
        print("\n示例:")
        print("  python3 skills/web-search-extraction/search.py 'AI agents' 3")
        print("\n能力:")
        print("  • 网络搜索")
        print("  • 深度页面提取")
        print("  • 结构化内容输出")
        print("  • Markdown 格式")
        print("\n底层工具:")
        print(f"  {WEB_EXTRACTOR}")
        return

    skill = WebSearchExtractionSkill(headless=True)
    query = sys.argv[1]
    num_results = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    # 执行搜索
    print(f"🔍 [{skill.name}] 搜索: {query}")
    data = await skill.search(query, num_results)

    # 更新到实际 web_extractor（通过调用）
    import subprocess
    cmd = [sys.executable, str(WEB_EXTRACTOR), query, str(num_results)]
    subprocess.run(cmd, check=True, cwd=str(WORKSPACE))

if __name__ == "__main__":
    asyncio.run(main())
