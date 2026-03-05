# 智能工具选择器 - RSI 实验 #2
"""
根据 URL/场景特征自动选择最佳工具
"""
import re
from urllib.parse import urlparse
from typing import Optional, Dict, List

class ToolSelector:
    """智能工具选择器 - 自动匹配最佳工具"""
    
    def __init__(self):
        self.tool_rules = [
            # 微信文章 - 直接用 Camoufox
            {
                'name': 'camoufox',
                'patterns': [
                    r'mp\.weixin\.qq\.com',
                    r'weixin\.qq\.com',
                ],
                'priority': 100,
                'reason': '微信反爬严格，需要 Camoufox'
            },
            # 小红书 - 需要登录/Cookie
            {
                'name': 'agent_reach_xhs',
                'patterns': [
                    r'xiaohongshu\.com',
                    r'xhslink\.com',
                ],
                'priority': 90,
                'reason': '小红书需要登录态'
            },
            # 抖音 - 需要解析
            {
                'name': 'agent_reach_douyin',
                'patterns': [
                    r'douyin\.com',
                    r'iesdouyin\.com',
                ],
                'priority': 90,
                'reason': '抖音需要特殊解析'
            },
            # 视频平台 - 用 yt-dlp
            {
                'name': 'yt_dlp',
                'patterns': [
                    r'youtube\.com',
                    r'bilibili\.com',
                    r'b23\.tv',
                ],
                'priority': 80,
                'reason': '视频平台用 yt-dlp 提取'
            },
            # 社交 API - 用 xreach
            {
                'name': 'xreach',
                'patterns': [
                    r'twitter\.com',
                    r'x\.com',
                ],
                'priority': 80,
                'reason': 'Twitter/X 用 xreach CLI'
            },
            # 普通网页 - 先用 Scrapling（快速）
            {
                'name': 'scrapling',
                'patterns': [
                    r'.*',  # 匹配所有
                ],
                'priority': 50,
                'fallback': True,
                'reason': '默认用 Scrapling 快速抓取'
            },
            # 最终 fallback - browser
            {
                'name': 'browser',
                'patterns': [],
                'priority': 10,
                'final_fallback': True,
                'reason': '所有方法失败后用 browser'
            }
        ]
    
    def select_tool(self, url_or_task: str, context: Optional[Dict] = None) -> Dict:
        """为给定 URL/任务选择最佳工具"""
        
        # 检查是否是 URL
        parsed = urlparse(url_or_task)
        is_url = bool(parsed.scheme and parsed.netloc)
        
        if is_url:
            return self._select_for_url(url_or_task)
        else:
            return self._select_for_task(url_or_task, context)
    
    def _select_for_url(self, url: str) -> Dict:
        """为 URL 选择工具"""
        url_lower = url.lower()
        
        # 按优先级排序匹配
        matches = []
        for rule in self.tool_rules:
            if rule.get('fallback') or rule.get('final_fallback'):
                continue
            for pattern in rule.get('patterns', []):
                if re.search(pattern, url_lower):
                    matches.append(rule)
                    break
        
        if matches:
            # 按优先级排序
            best = max(matches, key=lambda x: x['priority'])
            return {
                'tool': best['name'],
                'url': url,
                'reason': best['reason'],
                'priority': best['priority'],
                'fallback_chain': self._get_fallback_chain(best['name'])
            }
        
        # 默认 fallback
        return {
            'tool': 'scrapling',
            'url': url,
            'reason': '默认使用 Scrapling 快速抓取',
            'priority': 50,
            'fallback_chain': ['browser', 'camoufox']
        }
    
    def _select_for_task(self, task: str, context: Optional[Dict]) -> Dict:
        """为非 URL 任务选择工具"""
        task_lower = task.lower()
        
        # 任务类型识别
        if any(kw in task_lower for kw in ['微信', '公众号', 'mp.weixin']):
            return {
                'tool': 'camoufox',
                'task': task,
                'reason': '微信内容需要 Camoufox 绕过反爬'
            }
        
        if any(kw in task_lower for kw in ['视频', 'youtube', 'b站', 'bilibili']):
            return {
                'tool': 'yt_dlp',
                'task': task,
                'reason': '视频提取用 yt-dlp'
            }
        
        if any(kw in task_lower for kw in ['搜索', 'search', '查找']):
            return {
                'tool': 'web_search',
                'task': task,
                'reason': '搜索任务用 web_search'
            }
        
        # 默认
        return {
            'tool': 'auto',
            'task': task,
            'reason': '根据上下文自动选择'
        }
    
    def _get_fallback_chain(self, primary_tool: str) -> List[str]:
        """获取失败后的备用链"""
        chains = {
            'scrapling': ['browser', 'camoufox'],
            'browser': ['camoufox'],
            'camoufox': [],  # 最终手段
            'yt_dlp': ['browser'],
        }
        return chains.get(primary_tool, ['browser'])
    
    def get_execution_plan(self, url_or_task: str) -> str:
        """生成执行计划说明"""
        selection = self.select_tool(url_or_task)
        
        plan = f"""
🎯 **工具选择决策**
- 目标: {url_or_task[:60]}...
- 首选工具: **{selection['tool']}**
- 选择原因: {selection['reason']}
"""
        
        if 'fallback_chain' in selection and selection['fallback_chain']:
            plan += f"- 失败后备: {' → '.join(selection['fallback_chain'])}\n"
        
        return plan

# 全局选择器实例
tool_selector = ToolSelector()
