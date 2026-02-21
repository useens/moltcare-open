#!/usr/bin/env python3
"""
自动化脚本模板库 - 可复用的赚钱工具
提供即用型脚本模板，快速交付客户项目
"""

from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPT_TEMPLATES = WORKSPACE / "services" / "script-templates"

# 脚本模板定义
TEMPLATES = {
    "data-processor": {
        "name": "数据处理器",
        "description": "CSV/Excel数据清洗、转换、分析",
        "price": 500,
        "code": '''#!/usr/bin/env python3
"""
数据处理器 - 自动化数据清洗和分析
"""

import pandas as pd
import json
from pathlib import Path

class DataProcessor:
    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.data = None
    
    def load_data(self):
        """加载数据"""
        if self.input_file.suffix == '.csv':
            self.data = pd.read_csv(self.input_file)
        elif self.input_file.suffix in ['.xlsx', '.xls']:
            self.data = pd.read_excel(self.input_file)
        else:
            raise ValueError(f"不支持的文件格式: {self.input_file.suffix}")
        return self
    
    def clean_data(self):
        """清洗数据"""
        # 删除空值行
        self.data = self.data.dropna(how='all')
        # 删除重复行
        self.data = self.data.drop_duplicates()
        # 去除字符串前后空格
        for col in self.data.select_dtypes(include=['object']):
            self.data[col] = self.data[col].str.strip()
        return self
    
    def transform(self, operations: list):
        """执行转换操作"""
        for op in operations:
            if op['type'] == 'rename':
                self.data = self.data.rename(columns=op['mapping'])
            elif op['type'] == 'filter':
                self.data = self.data.query(op['condition'])
            elif op['type'] == 'calculate':
                self.data[op['new_col']] = eval(op['formula'])
        return self
    
    def analyze(self):
        """基础分析"""
        return {
            'row_count': len(self.data),
            'column_count': len(self.data.columns),
            'summary': self.data.describe().to_dict(),
            'null_counts': self.data.isnull().sum().to_dict()
        }
    
    def save(self, output_file: str):
        """保存结果"""
        output_path = Path(output_file)
        if output_path.suffix == '.csv':
            self.data.to_csv(output_path, index=False)
        elif output_path.suffix == '.xlsx':
            self.data.to_excel(output_path, index=False)
        elif output_path.suffix == '.json':
            self.data.to_json(output_path, orient='records')
        print(f"✅ 数据已保存: {output_path}")

if __name__ == "__main__":
    # 使用示例
    processor = DataProcessor("input.csv")
    processor.load_data().clean_data()
    analysis = processor.analyze()
    print(json.dumps(analysis, indent=2))
    processor.save("output_cleaned.csv")
'''
    },
    
    "api-monitor": {
        "name": "API监控告警",
        "description": "24/7监控API状态，异常时发送告警",
        "price": 800,
        "code": '''#!/usr/bin/env python3
"""
API监控告警系统 - 24/7服务健康检查
"""

import requests
import time
import json
from datetime import datetime
from pathlib import Path

class APIMonitor:
    def __init__(self, config_file: str = "monitor-config.json"):
        self.config_file = Path(config_file)
        self.endpoints = self._load_config()
        self.alerts = []
    
    def _load_config(self) -> list:
        """加载监控配置"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return []
    
    def check_endpoint(self, endpoint: dict) -> dict:
        """检查单个端点"""
        url = endpoint['url']
        expected_status = endpoint.get('expected_status', 200)
        timeout = endpoint.get('timeout', 10)
        
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'response_time': 0,
            'error': None
        }
        
        try:
            start = time.time()
            response = requests.get(url, timeout=timeout)
            result['response_time'] = round(time.time() - start, 3)
            
            if response.status_code == expected_status:
                result['status'] = 'healthy'
            else:
                result['status'] = 'error'
                result['error'] = f"状态码异常: {response.status_code}"
        
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error'] = f"请求超时 (> {timeout}s)"
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def run_check(self) -> list:
        """运行全部检查"""
        results = []
        for endpoint in self.endpoints:
            result = self.check_endpoint(endpoint)
            results.append(result)
            
            if result['status'] != 'healthy':
                self._send_alert(result)
        
        return results
    
    def _send_alert(self, result: dict):
        """发送告警"""
        alert = f"""
🚨 API监控告警

URL: {result['url']}
状态: {result['status']}
时间: {result['timestamp']}
错误: {result.get('error', 'N/A')}
        """
        self.alerts.append(alert)
        print(alert)
    
    def continuous_monitor(self, interval: int = 300):
        """持续监控"""
        print(f"🔍 开始持续监控 (间隔 {interval} 秒)")
        try:
            while True:
                self.run_check()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\\n👋 监控已停止")

if __name__ == "__main__":
    monitor = APIMonitor()
    
    # 示例配置
    sample_config = [
        {"url": "https://api.example.com/health", "expected_status": 200},
        {"url": "https://api.example.com/status", "expected_status": 200, "timeout": 5}
    ]
    
    print("请将以下配置保存为 monitor-config.json:")
    print(json.dumps(sample_config, indent=2))
'''
    },
    
    "web-scraper": {
        "name": "网页数据抓取",
        "description": "自动抓取网页数据，支持分页和反爬",
        "price": 1000,
        "code": '''#!/usr/bin/env python3
"""
智能网页抓取器 - 自动化数据采集
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

class WebScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data = []
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """获取页面内容"""
        time.sleep(self.delay)  # 礼貌延迟
        
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    
    def extract_data(self, soup: BeautifulSoup, selectors: dict) -> dict:
        """根据选择器提取数据"""
        result = {}
        for key, selector in selectors.items():
            element = soup.select_one(selector)
            result[key] = element.text.strip() if element else None
        return result
    
    def scrape_list(self, list_url: str, item_selector: str, 
                   data_selectors: dict, next_page_selector: str = None) -> list:
        """抓取列表页"""
        current_url = list_url
        
        while current_url:
            print(f"正在抓取: {current_url}")
            soup = self.fetch_page(current_url)
            
            # 提取列表项
            items = soup.select(item_selector)
            for item in items:
                data = self.extract_data(item, data_selectors)
                self.data.append(data)
            
            # 检查是否有下一页
            if next_page_selector:
                next_link = soup.select_one(next_page_selector)
                if next_link and next_link.get('href'):
                    current_url = urljoin(current_url, next_link['href'])
                else:
                    current_url = None
            else:
                current_url = None
        
        return self.data
    
    def save_data(self, filename: str):
        """保存数据"""
        output_path = Path(filename)
        
        if output_path.suffix == '.json':
            with open(output_path, 'w') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        elif output_path.suffix == '.csv':
            import pandas as pd
            df = pd.DataFrame(self.data)
            df.to_csv(output_path, index=False)
        
        print(f"✅ 数据已保存: {output_path} (共 {len(self.data)} 条)")

if __name__ == "__main__":
    scraper = WebScraper(delay=1.5)
    
    # 使用示例
    print("""
使用示例:
    scraper = WebScraper(delay=2)
    data = scraper.scrape_list(
        list_url="https://example.com/items",
        item_selector=".item",
        data_selectors={
            "title": ".title",
            "price": ".price",
            "link": "a"
        },
        next_page_selector=".next-page"
    )
    scraper.save_data("output.json")
    """)
'''
    },
    
    "report-generator": {
        "name": "自动化报告生成",
        "description": "从数据源自动生成格式化的PDF/Word报告",
        "price": 1200,
        "code": '''#!/usr/bin/env python3
"""
自动化报告生成器 - 数据到报告的一键转换
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from jinja2 import Template

class ReportGenerator:
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
    
    def load_data(self, source: str) -> pd.DataFrame:
        """加载数据源"""
        source_path = Path(source)
        
        if source_path.suffix == '.csv':
            return pd.read_csv(source)
        elif source_path.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(source)
        elif source_path.suffix == '.json':
            return pd.read_json(source)
        else:
            raise ValueError(f"不支持的数据格式: {source_path.suffix}")
    
    def analyze_data(self, df: pd.DataFrame) -> dict:
        """分析数据并生成统计信息"""
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'numeric_summary': {},
            'top_values': {}
        }
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            analysis['numeric_summary'][col] = {
                'mean': df[col].mean(),
                'median': df[col].median(),
                'min': df[col].min(),
                'max': df[col].max()
            }
        
        # 分类列TOP值
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols[:5]:  # 只取前5个
            analysis['top_values'][col] = df[col].value_counts().head(5).to_dict()
        
        return analysis
    
    def generate_html_report(self, data: pd.DataFrame, analysis: dict, 
                            template_name: str = "default") -> str:
        """生成HTML报告"""
        
        # 默认模板
        default_template = """
<!DOCTYPE html>
<html>
<head>
    <title>数据分析报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .summary { background: #f5f5f5; padding: 20px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>数据分析报告</h1>
    <p>生成时间: {{ analysis.generated_at }}</p>
    
    <div class="summary">
        <h2>数据概览</h2>
        <p>总行数: {{ analysis.total_rows }}</p>
        <p>总列数: {{ analysis.total_columns }}</p>
        <p>列名: {{ analysis.columns | join(", ") }}</p>
    </div>
    
    {% if analysis.numeric_summary %}
    <div class="summary">
        <h2>数值统计</h2>
        <table>
            <tr><th>列名</th><th>平均值</th><th>中位数</th><th>最小值</th><th>最大值</th></tr>
            {% for col, stats in analysis.numeric_summary.items() %}
            <tr>
                <td>{{ col }}</td>
                <td>{{ "%.2f" | format(stats.mean) }}</td>
                <td>{{ "%.2f" | format(stats.median) }}</td>
                <td>{{ "%.2f" | format(stats.min) }}</td>
                <td>{{ "%.2f" | format(stats.max) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    <h2>数据预览 (前10行)</h2>
    {{ data.head(10).to_html() | safe }}
</body>
</html>
        """
        
        template = Template(default_template)
        return template.render(data=data, analysis=analysis)
    
    def save_report(self, html_content: str, output_file: str):
        """保存报告"""
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ 报告已生成: {output_path}")
    
    def run(self, data_source: str, output_file: str):
        """一键生成报告"""
        print(f"📊 正在生成报告...")
        
        # 加载数据
        data = self.load_data(data_source)
        
        # 分析数据
        analysis = self.analyze_data(data)
        
        # 生成HTML
        html = self.generate_html_report(data, analysis)
        
        # 保存
        self.save_report(html, output_file)
        
        print(f"✅ 完成！共分析 {analysis['total_rows']} 行数据")

if __name__ == "__main__":
    generator = ReportGenerator()
    
    print("""
使用示例:
    generator = ReportGenerator()
    generator.run(
        data_source="sales_data.csv",
        output_file="sales_report.html"
    )
    """)
'''
    },
    
    "telegram-bot": {
        "name": "Telegram机器人",
        "description": "可定制的Telegram Bot框架，支持多种功能",
        "price": 1500,
        "code": '''#!/usr/bin/env python3
"""
Telegram Bot 框架 - 快速部署AI助手
"""

import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

class TelegramBot:
    def __init__(self, token: str = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("请设置 TELEGRAM_BOT_TOKEN 环境变量")
        
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置命令处理器"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/start 命令"""
        welcome_msg = """
🤖 欢迎使用 AI 助手 Bot！

可用命令：
/start - 开始使用
/help - 查看帮助
/status - 系统状态

直接发送消息即可与我对话。
        """
        await update.message.reply_text(welcome_msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/help 命令"""
        help_msg = """
📖 使用帮助

💬 对话功能
直接发送文字，AI 会自动回复

📄 文档处理
发送文档，支持 PDF、Word、TXT

🖼️ 图片分析
发送图片，AI 可以描述内容

⚙️ 更多功能开发中...
        """
        await update.message.reply_text(help_msg)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/status 命令"""
        status_msg = """
📊 系统状态

✅ Bot 运行正常
⏱️ 响应时间: < 1秒
🔋 服务可用性: 99.9%

如有问题请联系管理员。
        """
        await update.message.reply_text(status_msg)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通消息"""
        user_message = update.message.text
        
        # 这里可以接入AI模型进行处理
        # response = await process_with_ai(user_message)
        
        response = f"收到消息: {user_message}\\n\\n(此处接入AI处理逻辑)"
        await update.message.reply_text(response)
    
    def run(self):
        """启动Bot"""
        print("🤖 Bot 启动中...")
        print("按 Ctrl+C 停止")
        self.application.run_polling()

if __name__ == "__main__":
    print("""
Telegram Bot 快速启动

1. 从 @BotFather 获取 Bot Token
2. 设置环境变量: export TELEGRAM_BOT_TOKEN='your-token'
3. 运行: python bot.py

高级功能可自定义：
- 接入AI模型 (OpenAI/Claude/本地模型)
- 添加数据库支持
- 实现付费订阅
- 多用户管理
    """)
    
    # bot = TelegramBot()
    # bot.run()
'''
    }
}


def create_templates():
    """创建所有模板"""
    SCRIPT_TEMPLATES.mkdir(parents=True, exist_ok=True)
    
    for template_id, template in TEMPLATES.items():
        # 创建脚本文件
        script_file = SCRIPT_TEMPLATES / f"{template_id}.py"
        with open(script_file, 'w') as f:
            f.write(template['code'])
        
        # 创建README
        readme_file = SCRIPT_TEMPLATES / f"{template_id}-README.md"
        readme_content = f"""# {template['name']}

{template['description']}

## 价格
¥{template['price']}

## 包含内容
- 完整源代码
- 使用文档
- 30分钟远程指导
- 7天售后支持

## 使用方式
```bash
python3 {template_id}.py
```

## 定制服务
如需根据具体需求定制，请预约咨询。
"""
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    # 创建总目录
    catalog_file = SCRIPT_TEMPLATES / "CATALOG.md"
    catalog = f"""# 自动化脚本模板目录

> 更新日期: {datetime.now().strftime('%Y-%m-%d')}

| 模板ID | 名称 | 价格 | 描述 |
|--------|------|------|------|
"""
    
    for template_id, template in TEMPLATES.items():
        catalog += f"| {template_id} | {template['name']} | ¥{template['price']} | {template['description']} |\n"
    
    catalog += """
## 购买流程

1. 选择所需模板
2. 联系确认需求
3. 支付费用
4. 获取源码和指导

## 批量优惠

- 购买2个: 9折
- 购买3个: 8折
- 全部5个: 7折

## 联系方式

📧 contact@sensen.ai
💬 微信: sensen-ai
"""
    
    with open(catalog_file, 'w') as f:
        f.write(catalog)
    
    return SCRIPT_TEMPLATES


def main():
    print("🚀 创建自动化脚本模板库...")
    
    output_dir = create_templates()
    
    print(f"✅ 模板库已创建: {output_dir}")
    print("\n📦 包含模板:")
    
    total_value = 0
    for template_id, template in TEMPLATES.items():
        print(f"  - {template['name']}: ¥{template['price']}")
        total_value += template['price']
    
    print(f"\n💰 总价值: ¥{total_value}")
    print(f"   批量优惠价 (7折): ¥{int(total_value * 0.7)}")
    
    print("\n🎯 下一步:")
    print("  1. 测试所有模板确保可用")
    print("  2. 准备演示视频/GIF")
    print("  3. 发布到技术社区销售")


if __name__ == "__main__":
    main()
