#!/usr/bin/env python3
"""
深度提取学习工具 v3.0 - 统一方案
整合: deep_extract_3_posts + moltbook-detail-extract-v2 + web-extractor

统一使用: Playwright + Chromium
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# 配置
CHROMIUM_PATH = '/usr/bin/chromium'
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
DEFAULT_VIEWPORT = {'width': 1280, 'height': 800}

class DeepExtractor:
    """统一深度提取器"""
    
    def __init__(self, mode: str = 'standard'):
        self.mode = mode  # 'quick', 'standard', 'deep'
        self.results = []
        
    async def extract(self, url: str, **kwargs) -> Optional[Dict]:
        """
        统一提取入口
        
        Args:
            url: 目标URL
            mode: 提取模式 (quick/standard/deep)
            **kwargs: 额外配置
        
        Returns:
            {'url': str, 'title': str, 'content': str, 'method': str, 'success': bool}
        """
        methods = {
            'quick': self._extract_quick,
            'standard': self._extract_standard,
            'deep': self._extract_deep
        }
        
        extractor = methods.get(self.mode, self._extract_standard)
        return await extractor(url, **kwargs)
    
    async def _extract_quick(self, url: str, **kwargs) -> Optional[Dict]:
        """快速提取: 最简配置，最快返回"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    executable_path=CHROMIUM_PATH
                )
                page = await browser.new_page()
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                content = await page.locator('body').inner_text()
                title = await page.title()
                await browser.close()
                
                return {
                    'url': url,
                    'title': title,
                    'content': content[:5000],  # 快速模式截断
                    'method': 'quick',
                    'success': len(content) > 100
                }
        except Exception as e:
            return {'url': url, 'error': str(e), 'method': 'quick', 'success': False}
    
    async def _extract_standard(self, url: str, **kwargs) -> Optional[Dict]:
        """标准提取: 平衡速度和质量"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=CHROMIUM_PATH
            )
            context = await browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport=DEFAULT_VIEWPORT
            )
            page = await context.new_page()
            
            try:
                # 方法1: 标准加载
                await page.goto(url, wait_until='networkidle', timeout=30000)
                content = await page.locator('body').inner_text()
                title = await page.title()
                
                if len(content) > 1000:
                    await browser.close()
                    return {
                        'url': url,
                        'title': title,
                        'content': content,
                        'method': 'standard-1',
                        'success': True
                    }
                
                # 方法2: 尝试主要内容选择器
                selectors = ['article', 'main', '[class*="content"]', '[class*="post"]']
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        content = await page.locator(selector).inner_text()
                        if len(content) > 500:
                            await browser.close()
                            return {
                                'url': url,
                                'title': title,
                                'content': content,
                                'method': 'standard-2',
                                'success': True
                            }
                    except:
                        continue
                
                await browser.close()
                return {'url': url, 'title': title, 'content': content, 'method': 'standard-fallback', 'success': len(content) > 100}
                
            except Exception as e:
                await browser.close()
                return {'url': url, 'error': str(e), 'method': 'standard', 'success': False}
    
    async def _extract_deep(self, url: str, **kwargs) -> Optional[Dict]:
        """深度提取: 穷尽所有方法，确保获取完整内容"""
        attempts = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=CHROMIUM_PATH
            )
            
            # 方法1-3: 标准方法
            context = await browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport=DEFAULT_VIEWPORT
            )
            page = await context.new_page()
            
            # 方法1: networkidle
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                content = await page.locator('body').inner_text()
                title = await page.title()
                attempts.append({'method': 'networkidle', 'length': len(content), 'success': len(content) > 1000})
                if len(content) > 1000:
                    await browser.close()
                    return self._format_result(url, title, content, 'deep-1', attempts)
            except Exception as e:
                attempts.append({'method': 'networkidle', 'error': str(e)})
            
            # 方法2: load + 等待
            try:
                await page.goto(url, wait_until='load', timeout=60000)
                await page.wait_for_timeout(5000)
                content = await page.locator('body').inner_text()
                attempts.append({'method': 'load+wait', 'length': len(content)})
                if len(content) > 1000:
                    await browser.close()
                    return self._format_result(url, title, content, 'deep-2', attempts)
            except Exception as e:
                attempts.append({'method': 'load+wait', 'error': str(e)})
            
            # 方法3: 多种选择器
            selectors = [
                'article', 'main', '[class*="content"]', '[class*="post"]',
                '[role="main"]', '#content', '.content', '.post-content'
            ]
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    content = await page.locator(selector).inner_text()
                    attempts.append({'method': f'selector:{selector}', 'length': len(content)})
                    if len(content) > 500:
                        await browser.close()
                        return self._format_result(url, title, content, f'deep-3-{selector}', attempts)
                except:
                    continue
            
            await context.close()
            
            # 方法4: 移动端UA
            try:
                mobile_context = await browser.new_context(
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
                    viewport={'width': 390, 'height': 844}
                )
                page = await mobile_context.new_page()
                await page.goto(url, wait_until='networkidle', timeout=30000)
                content = await page.locator('body').inner_text()
                title = await page.title()
                attempts.append({'method': 'mobile-ua', 'length': len(content)})
                if len(content) > 500:
                    await mobile_context.close()
                    await browser.close()
                    return self._format_result(url, title, content, 'deep-4-mobile', attempts)
                await mobile_context.close()
            except Exception as e:
                attempts.append({'method': 'mobile-ua', 'error': str(e)})
            
            await browser.close()
            
            # 全部失败，返回最后一次尝试
            return {
                'url': url,
                'title': title if 'title' in locals() else 'Unknown',
                'content': content if 'content' in locals() else '',
                'method': 'deep-failed',
                'success': False,
                'attempts': attempts
            }
    
    def _format_result(self, url: str, title: str, content: str, method: str, attempts: List) -> Dict:
        return {
            'url': url,
            'title': title,
            'content': content,
            'method': method,
            'success': True,
            'length': len(content),
            'attempts': attempts
        }


async def main():
    parser = argparse.ArgumentParser(description='深度提取学习工具 v3.0')
    parser.add_argument('url', help='目标URL')
    parser.add_argument('--mode', choices=['quick', 'standard', 'deep'], default='standard',
                       help='提取模式 (默认: standard)')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--json', '-j', action='store_true', help='JSON格式输出')
    
    args = parser.parse_args()
    
    extractor = DeepExtractor(mode=args.mode)
    result = await extractor.extract(args.url)
    
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"结果已保存到: {args.output}")
    elif args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"URL: {result['url']}")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"方法: {result['method']}")
        print(f"成功: {result['success']}")
        print(f"长度: {result.get('length', len(result.get('content', '')))}")
        if result['success']:
            print(f"\n内容预览:\n{result['content'][:1000]}...")


if __name__ == '__main__':
    asyncio.run(main())
