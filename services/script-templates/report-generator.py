#!/usr/bin/env python3
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
