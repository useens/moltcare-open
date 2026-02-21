#!/usr/bin/env python3
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
