#!/usr/bin/env python3
"""
浏览器自动化演示 - 完整操作链
登录 → 导航 → 点击 → 提取 → 截图
"""

import asyncio
from playwright.async_api import async_playwright


async def browser_automation_demo():
    """完整浏览器自动化流程演示"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 可见模式便于演示
        page = await browser.new_page()
        
        print("="*50)
        print("浏览器自动化演示")
        print("="*50)
        
        # 1. GOTO - 访问页面
        print("\n[1] GOTO: 访问Moltbook")
        await page.goto("https://www.moltbook.com/login")
        await page.wait_for_timeout(2000)
        
        # 2. TYPE - 输入账号（如果有登录框）
        print("\n[2] TYPE: 输入用户名（演示）")
        # await page.fill('input[name="username"]', "LinLin_v1")
        
        # 3. TYPE - 输入密码
        print("[3] TYPE: 输入密码（演示）")
        # await page.fill('input[name="password"]', "********")
        
        # 4. CLICK - 点击登录按钮
        print("\n[4] CLICK: 点击登录按钮")
        # await page.click('button[type="submit"]')
        # await page.wait_for_timeout(3000)
        
        # 5. GOTO - 导航到个人主页
        print("\n[5] GOTO: 导航到主页")
        await page.goto("https://www.moltbook.com/u/LinLin_v1")
        await page.wait_for_timeout(2000)
        
        # 6. SCROLL - 滚动加载更多
        print("\n[6] SCROLL: 滚动页面")
        for i in range(3):
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(500)
            print(f"  滚动 {i+1}/3")
        
        # 7. CLICK - 点击第一个帖子
        print("\n[7] CLICK: 点击第一个帖子")
        post_link = await page.query_selector('a[href^="/post/"]')
        if post_link:
            await post_link.click()
            await page.wait_for_timeout(3000)
            print("  ✓ 已进入帖子详情页")
            
            # 8. TEXT - 提取内容
            print("\n[8] TEXT: 提取帖子内容")
            content = await page.inner_text('article, [class*="content"], body')
            print(f"  内容预览: {content[:200]}...")
            
            # 9. CLICK - 点赞按钮
            print("\n[9] CLICK: 点赞按钮（演示）")
            # await page.click('[class*="upvote"], button:has-text("▲")')
            
            # 10. TYPE - 输入评论
            print("\n[10] TYPE: 输入评论（演示）")
            # await page.fill('textarea', "Great post!")
            # await page.click('button:has-text("Submit")')
        
        # 11. BACK - 返回上一页
        print("\n[11] BACK: 返回主页")
        await page.go_back()
        await page.wait_for_timeout(2000)
        
        # 12. SCREENSHOT - 截图
        print("\n[12] SCREENSHOT: 保存截图")
        await page.screenshot(path="browser_demo.png", full_page=True)
        print("  ✓ 截图已保存: browser_demo.png")
        
        # 13. EVAL - 执行自定义JS
        print("\n[13] EVAL: 执行JavaScript")
        page_info = await page.evaluate('''() => ({
            title: document.title,
            url: window.location.href,
            posts: document.querySelectorAll('a[href^="/post/"]').length
        })''')
        print(f"  页面标题: {page_info['title']}")
        print(f"  当前URL: {page_info['url']}")
        print(f"  帖子数量: {page_info['posts']}")
        
        # 14. HOVER - 悬停（触发下拉菜单等）
        print("\n[14] HOVER: 悬停菜单（演示）")
        # await page.hover('.user-menu')
        # await page.wait_for_timeout(1000)
        
        # 15. SELECT - 下拉选择
        print("\n[15] SELECT: 选择选项（演示）")
        # await page.select_option('select[name="sort"]', "new")
        
        await browser.close()
        
        print("\n" + "="*50)
        print("演示完成！浏览器自动化能力：")
        print("="*50)
        print("""
✓ GOTO    - 访问任意URL
✓ TYPE    - 输入文本（搜索、登录、表单）
✓ CLICK   - 点击元素（按钮、链接、提交）
✓ SCROLL  - 滚动页面（加载更多）
✓ TEXT    - 提取文本内容
✓ SCREENSHOT - 截图存档
✓ BACK/FORWARD - 导航历史
✓ EVAL    - 执行JavaScript
✓ HOVER   - 悬停交互
✓ SELECT  - 下拉选择
✓ WAIT    - 智能等待
        """)


if __name__ == "__main__":
    asyncio.run(browser_automation_demo())
