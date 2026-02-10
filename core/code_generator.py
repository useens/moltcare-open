#!/usr/bin/env python3
"""
林林v5.0 代码生成器 (Code Generator)
将自然语言需求转化为可执行代码
"""

import re
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class RequirementParser:
    """需求解析器 - 将自然语言转化为技术规格"""
    
    # 指标关键词映射
    METRIC_PATTERNS = {
        'cpu': ['cpu', '处理器', 'cpu使用率', 'cpu load'],
        'memory': ['memory', '内存', 'ram', 'mem'],
        'disk': ['disk', '磁盘', '硬盘', 'storage', '空间'],
        'network': ['network', '网络', '网卡', '流量', 'bandwidth'],
        'process': ['process', '进程', '应用状态'],
        'log': ['log', '日志', 'error', '错误'],
        'port': ['port', '端口', '监听'],
        'service': ['service', '服务状态', 'systemd'],
        'load': ['load', '负载', 'load average'],
    }
    
    # 检查类型模式
    CHECK_PATTERNS = {
        'threshold': ['超过', '大于', '小于', '低于', '高于', '阈值', '>%', '<%', 'threshold'],
        'existence': ['存在', '是否存在', '运行中', '有没有'],
        'count': ['数量', '个数', '计数', '多少'],
        'pattern': ['匹配', '包含', '正则', '查找'],
    }
    
    def parse(self, requirement: str) -> Dict[str, Any]:
        """解析自然语言需求"""
        req_lower = requirement.lower()
        
        spec = {
            'raw_requirement': requirement,
            'metric_type': None,
            'check_type': 'threshold',
            'threshold_value': None,
            'threshold_operator': '>',
            'alert_action': 'print',
            'parsed_at': datetime.now().isoformat()
        }
        
        # 识别指标类型
        for metric, keywords in self.METRIC_PATTERNS.items():
            for kw in keywords:
                if kw in req_lower:
                    spec['metric_type'] = metric
                    break
            if spec['metric_type']:
                break
        
        # 识别检查类型
        for check_type, keywords in self.CHECK_PATTERNS.items():
            for kw in keywords:
                if kw in req_lower:
                    spec['check_type'] = check_type
                    break
        
        # 提取阈值数值
        threshold_match = re.search(r'(\d+(?:\.\d+)?)\s*%?', req_lower)
        if threshold_match:
            spec['threshold_value'] = float(threshold_match.group(1))
        
        # 识别比较运算符
        if any(x in req_lower for x in ['超过', '大于', '高于', '>%']):
            spec['threshold_operator'] = '>'
        elif any(x in req_lower for x in ['低于', '小于', '低于', '<%']):
            spec['threshold_operator'] = '<'
        
        return spec


class CodeTemplateLibrary:
    """代码模板库 - 常用代码模式复用"""
    
    TEMPLATES = {
        'cpu': '''#!/usr/bin/env python3
"""
CPU健康检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys

def check_cpu():
    """检查CPU使用率"""
    cpu_percent = psutil.cpu_percent(interval=1)
    threshold = {threshold}
    operator = '{operator}'
    
    condition_met = cpu_percent > threshold if operator == '>' else cpu_percent < threshold
    
    if condition_met:
        print(f"[WARNING] CPU使用率: {{cpu_percent}}% (阈值: {{operator}}{{threshold}}%)")
        return 1
    else:
        print(f"[OK] CPU使用率: {{cpu_percent}}%")
        return 0

if __name__ == '__main__':
    sys.exit(check_cpu())
''',
        'memory': '''#!/usr/bin/env python3
"""
内存健康检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys

def check_memory():
    """检查内存使用率"""
    mem = psutil.virtual_memory()
    mem_percent = mem.percent
    threshold = {threshold}
    operator = '{operator}'
    
    condition_met = mem_percent > threshold if operator == '>' else mem_percent < threshold
    
    if condition_met:
        print(f"[WARNING] 内存使用率: {{mem_percent}}% (阈值: {{operator}}{{threshold}}%)")
        print(f"  总内存: {{mem.total // (1024**3)}} GB")
        print(f"  可用内存: {{mem.available // (1024**3)}} GB")
        return 1
    else:
        print(f"[OK] 内存使用率: {{mem_percent}}%")
        return 0

if __name__ == '__main__':
    sys.exit(check_memory())
''',
        'disk': '''#!/usr/bin/env python3
"""
磁盘健康检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys

def check_disk(path='/'):
    """检查磁盘使用率"""
    disk = psutil.disk_usage(path)
    disk_percent = disk.percent
    threshold = {threshold}
    operator = '{operator}'
    
    condition_met = disk_percent > threshold if operator == '>' else disk_percent < threshold
    
    if condition_met:
        print(f"[WARNING] 磁盘使用率: {{disk_percent}}% (路径: {{path}})")
        print(f"  总空间: {{disk.total // (1024**3)}} GB")
        print(f"  已用空间: {{disk.used // (1024**3)}} GB")
        print(f"  可用空间: {{disk.free // (1024**3)}} GB")
        return 1
    else:
        print(f"[OK] 磁盘使用率: {{disk_percent}}% (路径: {{path}})")
        return 0

if __name__ == '__main__':
    sys.exit(check_disk())
''',
        'network': '''#!/usr/bin/env python3
"""
网络健康检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys
import socket

def check_network():
    """检查网络状态"""
    stats = psutil.net_io_counters()
    threshold = {threshold}
    operator = '{operator}'
    
    # 获取默认网关连接状态
    try:
        # 测试外部连接
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        network_ok = True
    except:
        network_ok = False
    
    if not network_ok:
        print("[WARNING] 网络连接异常")
        return 1
    
    print(f"[OK] 网络连接正常")
    print(f"  发送: {{stats.bytes_sent // 1024}} KB")
    print(f"  接收: {{stats.bytes_recv // 1024}} KB")
    return 0

if __name__ == '__main__':
    sys.exit(check_network())
''',
        'process': '''#!/usr/bin/env python3
"""
进程健康检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys

def check_process(process_name=None):
    """检查进程状态"""
    if not process_name:
        # 检查所有进程数量
        process_count = len(psutil.pids())
        threshold = {threshold}
        operator = '{operator}'
        
        condition_met = process_count > threshold if operator == '>' else process_count < threshold
        
        if condition_met:
            print(f"[WARNING] 进程数量: {{process_count}} (阈值: {{operator}}{{threshold}})")
            return 1
        else:
            print(f"[OK] 进程数量: {{process_count}}")
            return 0
    else:
        # 检查特定进程是否存在
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                print(f"[OK] 进程 '{{process_name}}' 正在运行")
                return 0
        print(f"[WARNING] 进程 '{{process_name}}' 未找到")
        return 1

if __name__ == '__main__':
    sys.exit(check_process())
''',
        'port': '''#!/usr/bin/env python3
"""
端口健康检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys
import socket

def check_port(port=None):
    """检查端口监听状态"""
    if not port:
        port = 80
    
    # 检查端口是否在监听
    listening = False
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            listening = True
            break
    
    if listening:
        print(f"[OK] 端口 {{port}} 正在监听")
        return 0
    else:
        print(f"[WARNING] 端口 {{port}} 未在监听")
        return 1

if __name__ == '__main__':
    sys.exit(check_port())
''',
        'load': '''#!/usr/bin/env python3
"""
系统负载检查脚本
生成时间: {timestamp}
原始需求: {requirement}
"""

import psutil
import sys
import os

def check_load():
    """检查系统负载"""
    load_avg = os.getloadavg()
    cpu_count = psutil.cpu_count()
    
    # 1分钟负载
    load_1 = load_avg[0]
    threshold = {threshold}
    operator = '{operator}'
    
    condition_met = load_1 > threshold if operator == '>' else load_1 < threshold
    
    if condition_met:
        print(f"[WARNING] 系统负载: {{load_1:.2f}} (阈值: {{operator}}{{threshold}}, CPU核心: {{cpu_count}})")
        print(f"  1分钟负载: {{load_avg[0]:.2f}}")
        print(f"  5分钟负载: {{load_avg[1]:.2f}}")
        print(f"  15分钟负载: {{load_avg[2]:.2f}}")
        return 1
    else:
        print(f"[OK] 系统负载: {{load_1:.2f}}")
        return 0

if __name__ == '__main__':
    sys.exit(check_load())
''',
    }
    
    @classmethod
    def get_template(cls, metric_type: str) -> Optional[str]:
        """获取指定指标类型的模板"""
        return cls.TEMPLATES.get(metric_type)
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """列出所有可用模板"""
        return list(cls.TEMPLATES.keys())


class CodeGenerator:
    """代码生成器主类"""
    
    # 危险操作黑名单
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'rm\s+-f\s+/',
        r'mkfs',
        r'dd\s+if=.*of=/dev/',
        r':\(\)\{\s*:\|:&\s*\};:',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'os\.system\s*\(',
        r'subprocess\.call\s*\([^)]*shell\s*=\s*True',
        r'__import__\s*\(\s*[\'"]os[\'"]\s*\)\.system',
    ]
    
    def __init__(self):
        self.parser = RequirementParser()
        self.template_lib = CodeTemplateLibrary()
        self.generated_codes = []
    
    def check_safety(self, code: str) -> tuple[bool, List[str]]:
        """检查代码安全性"""
        violations = []
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"发现危险模式: {pattern}")
        
        return len(violations) == 0, violations
    
    def generate(self, requirement: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        根据需求生成代码
        
        Args:
            requirement: 自然语言需求
            output_path: 输出文件路径 (可选)
            
        Returns:
            包含生成结果的字典
        """
        # 1. 解析需求
        spec = self.parser.parse(requirement)
        
        if not spec['metric_type']:
            return {
                'success': False,
                'error': '无法识别检查指标类型',
                'spec': spec
            }
        
        # 2. 获取模板
        template = self.template_lib.get_template(spec['metric_type'])
        if not template:
            return {
                'success': False,
                'error': f"未找到指标类型 '{spec['metric_type']}' 的模板",
                'spec': spec
            }
        
        # 3. 填充模板
        threshold = spec.get('threshold_value') or 80
        operator = spec.get('threshold_operator') or '>'
        
        code = template.format(
            timestamp=datetime.now().isoformat(),
            requirement=requirement,
            threshold=threshold,
            operator=operator
        )
        
        # 4. 安全检查
        is_safe, violations = self.check_safety(code)
        if not is_safe:
            return {
                'success': False,
                'error': '代码安全检查失败',
                'violations': violations,
                'spec': spec
            }
        
        # 5. 保存文件
        if output_path:
            with open(output_path, 'w') as f:
                f.write(code)
            os.chmod(output_path, 0o755)
        
        result = {
            'success': True,
            'code': code,
            'spec': spec,
            'output_path': output_path,
            'metric_type': spec['metric_type']
        }
        
        self.generated_codes.append(result)
        return result
    
    def generate_batch(self, requirements: List[str], output_dir: str) -> List[Dict[str, Any]]:
        """批量生成代码"""
        results = []
        for i, req in enumerate(requirements):
            output_path = os.path.join(output_dir, f'check_{i+1}_{self.parser.parse(req)["metric_type"]}.py')
            result = self.generate(req, output_path)
            results.append(result)
        return results
    
    def get_generation_history(self) -> List[Dict[str, Any]]:
        """获取生成历史"""
        return self.generated_codes


if __name__ == '__main__':
    # 示例用法
    generator = CodeGenerator()
    
    print("=" * 60)
    print("林林v5.0 代码生成器")
    print("=" * 60)
    print(f"\n可用模板: {generator.template_lib.list_templates()}")
    
    # 示例生成
    test_requirements = [
        "检查CPU使用率是否超过80%",
        "检查内存使用率是否超过90%",
        "检查磁盘空间是否超过85%",
    ]
    
    print("\n示例生成:")
    for req in test_requirements:
        print(f"\n需求: {req}")
        result = generator.generate(req)
        if result['success']:
            print(f"✓ 生成成功 (类型: {result['metric_type']})")
            print(f"  代码长度: {len(result['code'])} 字符")
        else:
            print(f"✗ 生成失败: {result.get('error')}")
