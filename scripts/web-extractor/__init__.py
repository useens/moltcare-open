"""
Web Extractor - 通用网页提取器框架

包含:
- base_extractor.py: 基础类，可继承扩展
- moltbook_extractor.py: Moltbook 专用提取器
- generic_extractor.py: 通用配置版提取器
- configs/: 配置文件目录

使用示例:
    # 方法1: 使用专用提取器
    from moltbook_extractor import MoltbookExtractor
    extractor = MoltbookExtractor()
    await extractor.extract_hot()
    
    # 方法2: 使用通用配置版
    from generic_extractor import GenericExtractor
    extractor = GenericExtractor('configs/any_site.json')
    await extractor.run()
    
    # 方法3: 继承基础类自定义
    from base_extractor import BaseWebExtractor
    class MyExtractor(BaseWebExtractor):
        def get_selectors(self): ...
        async def parse_item(self, element, page): ...
"""

__version__ = "1.0.0"
__all__ = ['BaseWebExtractor', 'MoltbookExtractor', 'GenericExtractor']
