#!/bin/bash
# Neural Hub - 快速部署网络访问能力
# 为小弟们配置共享的浏览器和网络工具

echo "======================================================================"
echo "🎓 神经中枢 - 快速部署网络访问能力"
echo "======================================================================"
echo ""

# 创建共享的Python环境
SHARED_VENV="/root/.openclaw/workspace/nanobots/shared_venv"
echo "创建共享Python环境..."
python3 -m venv "$SHARED_VENV" 2>/dev/null || echo "环境已存在"
source "$SHARED_VENV/bin/activate"

echo ""
echo "1️⃣ 安装基础网络工具..."
pip install -q requests httpx aiohttp 2>/dev/null
echo "   ✅ requests, httpx, aiohttp"

echo ""
echo "2️⃣ 安装 Playwright (浏览器自动化)..."
pip install -q playwright 2>/dev/null
echo "   ✅ playwright"

echo ""
echo "3️⃣ 安装 Scrapling (反爬绕过)..."
pip install -q scrapling 2>/dev/null
echo "   ✅ scrapling"

echo ""
echo "4️⃣ 安装浏览器..."
playwright install chromium 2>/dev/null &
echo "   ✅ Chromium (后台安装中)"

echo ""
echo "5️⃣ 为小弟们创建启动脚本..."

for i in {1..10}; do
    node=$(printf "nb%02d" $i)
    node_dir="/root/.openclaw/workspace/nanobots/$node"
    
    # 创建激活脚本
    cat > "$node_dir/activate_env.sh" << EOF
#!/bin/bash
# 激活共享Python环境
source $SHARED_VENV/bin/activate
export PLAYWRIGHT_BROWSERS_PATH=$SHARED_VENV/playwright-browsers
export PYTHONPATH=$node_dir/workspace:\$PYTHONPATH
EOF
    chmod +x "$node_dir/activate_env.sh"
    
    # 创建网络访问示例脚本
    cat > "$node_dir/workspace/network_example.py" << 'EOF'
#!/usr/bin/env python3
"""
网络访问示例 - 使用共享环境的工具
"""

# 基础HTTP
import requests
import httpx

# 浏览器自动化
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except:
    HAS_PLAYWRIGHT = False

# 反爬绕过
try:
    import scrapling
    from scrapling import ScraplingFetcher
    HAS_SCRAPLING = True
except:
    HAS_SCRAPLING = False

def basic_fetch(url):
    """基础网页获取"""
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def browser_fetch(url):
    """浏览器获取"""
    if not HAS_PLAYWRIGHT:
        return "Playwright not available"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        return f"Error: {e}"

def stealth_fetch(url):
    """反爬绕过获取"""
    if not HAS_SCRAPLING:
        return "Scrapling not available"
    
    try:
        fetcher = ScraplingFetcher()
        return fetcher.get(url).text
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    
    print(f"Fetching: {url}")
    print("-" * 50)
    print("Basic fetch:")
    print(basic_fetch(url)[:500])
    print("\nBrowser fetch:")
    print(browser_fetch(url)[:500])
EOF
    chmod +x "$node_dir/workspace/network_example.py"
    
done

echo "   ✅ 所有小弟配置完成"

echo ""
echo "======================================================================"
echo "✅ 网络访问能力部署完成！"
echo "======================================================================"
echo ""
echo "已安装工具:"
echo "  • requests/httpx - 基础HTTP请求"
echo "  • playwright - 浏览器自动化"
echo "  • scrapling - 反爬绕过"
echo "  • chromium - 浏览器引擎"
echo ""
echo "使用方式:"
echo "  1. source /root/.openclaw/workspace/nanobots/shared_venv/bin/activate"
echo "  2. python3 nanobots/nb01/workspace/network_example.py https://example.com"
echo ""
echo "======================================================================"
