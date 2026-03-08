#!/usr/bin/env python3
"""
MoltCare Shield Service - Agent技能安全扫描服务
MVP版本: 静态代码分析 + 风险评级

检测项:
- 文件系统操作
- 网络请求
- 环境变量访问
- 命令执行
- 已知恶意模式
"""

import os
import sys
import json
import ast
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# 配置
CONFIG = {
    "threat_db": os.getenv("MOLTCARE_THREAT_DB", "data/moltcare/threats.json"),
    "scan_results_dir": os.getenv("MOLTCARE_SCANS", "data/moltcare/scans"),
}

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MoltCare-Shield - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/moltcare-shield.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 危险模式定义
DANGEROUS_PATTERNS = {
    "file_system": {
        "patterns": [
            r"open\s*\(",
            r"os\.path\.",
            r"fs\.",
            r"readFile",
            r"writeFile",
            r"\.read\s*\(",
            r"\.write\s*\(",
        ],
        "severity": "medium",
        "description": "文件系统操作"
    },
    "network": {
        "patterns": [
            r"requests\.",
            r"axios",
            r"fetch\s*\(",
            r"http\.",
            r"https\.",
            r"urllib",
            r"curl",
        ],
        "severity": "high",
        "description": "网络请求"
    },
    "env_access": {
        "patterns": [
            r"process\.env",
            r"os\.environ",
            r"getenv",
            r"\.env",
            r"dotenv",
        ],
        "severity": "high",
        "description": "环境变量访问"
    },
    "command_exec": {
        "patterns": [
            r"os\.system",
            r"subprocess",
            r"exec\s*\(",
            r"eval\s*\(",
            r"spawn",
            r"shelljs",
            r"child_process",
        ],
        "severity": "critical",
        "description": "命令执行"
    },
    "credential_access": {
        "patterns": [
            r"password",
            r"secret",
            r"token",
            r"api_key",
            r"private_key",
            r"\.key",
            r"\.pem",
        ],
        "severity": "medium",
        "description": "凭证访问"
    }
}

# 已知恶意签名
MALWARE_SIGNATURES = [
    {
        "name": "env_stealer",
        "pattern": r"(process\.env|os\.environ).*webhook|http.*post.*env",
        "severity": "critical",
        "description": "窃取环境变量并外传"
    },
    {
        "name": "credential_harvester",
        "pattern": r"(password|secret|token).*send|post.*(password|secret)",
        "severity": "critical",
        "description": "窃取凭证信息"
    },
    {
        "name": "reverse_shell",
        "pattern": r"socket.*connect|net\.createConnection|spawn.*\/bin\/sh",
        "severity": "critical",
        "description": "反向Shell"
    },
    {
        "name": "file_exfiltration",
        "pattern": r"readFile.*(http|post|send)|fs\.read.*axios",
        "severity": "high",
        "description": "文件外泄"
    }
]


class ShieldScanner:
    """技能安全扫描器"""
    
    def __init__(self):
        self.results_dir = Path(CONFIG["scan_results_dir"])
        self.results_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Shield Scanner initialized")
    
    def scan_file(self, file_path: str) -> Dict:
        """扫描单个文件"""
        path = Path(file_path)
        
        if not path.exists():
            return {'error': 'File not found'}
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return self.scan_code(content, path.name)
            
        except Exception as e:
            logger.error(f"Scan failed for {file_path}: {e}")
            return {'error': str(e)}
    
    def scan_code(self, code: str, filename: str = "unknown") -> Dict:
        """扫描代码内容"""
        findings = []
        lines = code.split('\n')
        
        # 1. 检测危险模式
        for category, config in DANGEROUS_PATTERNS.items():
            for pattern in config["patterns"]:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            'line': i,
                            'category': category,
                            'severity': config["severity"],
                            'description': config["description"],
                            'pattern': pattern,
                            'code': line.strip()[:100]
                        })
        
        # 2. 检测已知恶意签名
        for sig in MALWARE_SIGNATURES:
            if re.search(sig["pattern"], code, re.IGNORECASE | re.DOTALL):
                findings.append({
                    'line': 0,
                    'category': 'malware_signature',
                    'severity': sig["severity"],
                    'description': sig["description"],
                    'signature': sig["name"],
                    'code': 'Known malicious pattern detected'
                })
        
        # 3. Python AST分析（如果是Python代码）
        if filename.endswith('.py'):
            ast_findings = self._analyze_python_ast(code)
            findings.extend(ast_findings)
        
        # 去重
        unique_findings = self._deduplicate_findings(findings)
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(unique_findings)
        risk_level = self._get_risk_level(risk_score)
        
        result = {
            'filename': filename,
            'scan_time': logging.Formatter().formatTime(logging.LogRecord(
                'shield', logging.INFO, '', 0, '', (), None
            )),
            'lines_of_code': len(lines),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'findings_count': len(unique_findings),
            'findings': unique_findings,
            'summary': self._generate_summary(unique_findings)
        }
        
        return result
    
    def _analyze_python_ast(self, code: str) -> List[Dict]:
        """Python AST深度分析"""
        findings = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检测危险的函数调用
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        dangerous_funcs = ['eval', 'exec', 'compile', '__import__']
                        if func_name in dangerous_funcs:
                            findings.append({
                                'line': getattr(node, 'lineno', 0),
                                'category': 'dangerous_function',
                                'severity': 'critical',
                                'description': f'使用危险函数: {func_name}',
                                'code': func_name
                            })
                
                # 检测导入语句
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    suspicious_modules = ['subprocess', 'os', 'sys', 'socket']
                    for alias in node.names:
                        module = alias.name if isinstance(node, ast.Import) else node.module
                        if module and any(sus in module for sus in suspicious_modules):
                            findings.append({
                                'line': getattr(node, 'lineno', 0),
                                'category': 'suspicious_import',
                                'severity': 'medium',
                                'description': f'导入敏感模块: {module}',
                                'code': f'import {module}'
                            })
        
        except SyntaxError:
            # 代码语法错误，可能是混淆或损坏
            findings.append({
                'line': 0,
                'category': 'syntax_error',
                'severity': 'medium',
                'description': '代码存在语法错误，可能经过混淆',
                'code': 'Syntax error in code'
            })
        
        return findings
    
    def _deduplicate_findings(self, findings: List[Dict]) -> List[Dict]:
        """去重发现"""
        seen = set()
        unique = []
        
        for f in findings:
            key = (f['line'], f['category'], f.get('pattern', f.get('signature', '')))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique
    
    def _calculate_risk_score(self, findings: List[Dict]) -> int:
        """计算风险评分 (0-100)"""
        severity_weights = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 1
        }
        
        score = 0
        for f in findings:
            score += severity_weights.get(f['severity'], 1)
        
        return min(score, 100)
    
    def _get_risk_level(self, score: int) -> str:
        """获取风险等级"""
        if score >= 50:
            return 'DANGER'
        elif score >= 20:
            return 'HIGH'
        elif score >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_summary(self, findings: List[Dict]) -> Dict:
        """生成摘要"""
        summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        categories = set()
        
        for f in findings:
            summary[f.get('severity', 'low')] += 1
            categories.add(f.get('category', 'unknown'))
        
        summary['categories'] = list(categories)
        return summary
    
    def scan_directory(self, dir_path: str) -> Dict:
        """扫描整个目录"""
        path = Path(dir_path)
        
        if not path.exists():
            return {'error': 'Directory not found'}
        
        all_results = []
        files_scanned = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.sh']:
                result = self.scan_file(str(file_path))
                if 'error' not in result:
                    all_results.append(result)
                    files_scanned += 1
        
        # 汇总
        total_findings = sum(r['findings_count'] for r in all_results)
        max_risk = max((r['risk_score'] for r in all_results), default=0)
        
        return {
            'directory': dir_path,
            'files_scanned': files_scanned,
            'total_findings': total_findings,
            'max_risk_score': max_risk,
            'overall_risk': self._get_risk_level(max_risk),
            'file_results': all_results
        }
    
    def save_report(self, result: Dict, agent_id: str = None) -> str:
        """保存扫描报告"""
        timestamp = logging.Formatter().formatTime(logging.LogRecord(
            'shield', logging.INFO, '', 0, '', (), None
        )).replace(' ', '_').replace(':', '-')
        
        if agent_id:
            filename = f"{agent_id}_{timestamp}.json"
        else:
            filename = f"scan_{timestamp}.json"
        
        report_path = self.results_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return str(report_path)
    
    def generate_html_report(self, result: Dict) -> str:
        """生成HTML格式的报告"""
        risk_colors = {
            'DANGER': '#ff4444',
            'HIGH': '#ff8800',
            'MEDIUM': '#ffcc00',
            'LOW': '#00cc00'
        }
        
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MoltCare Shield Scan Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }}
                .header {{ background: {risk_colors.get(result['risk_level'], '#333')}; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .finding {{ background: #16213e; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid; }}
                .critical {{ border-color: #ff4444; }}
                .high {{ border-color: #ff8800; }}
                .medium {{ border-color: #ffcc00; }}
                .low {{ border-color: #00cc00; }}
                .code {{ background: #0f0f23; padding: 10px; border-radius: 3px; font-family: monospace; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ MoltCare Shield 扫描报告</h1>
                <p>文件: {result['filename']}</p>
                <p>风险等级: <strong>{result['risk_level']}</strong> (评分: {result['risk_score']}/100)</p>
                <p>发现问题: {result['findings_count']} 个</p>
            </div>
            
            <h2>详细发现</h2>
        """
        
        for finding in result['findings']:
            icon = severity_icons.get(finding['severity'], '⚪')
            severity_class = finding['severity']
            
            html += f"""
            <div class="finding {severity_class}">
                <h3>{icon} {finding['description']} (第{finding['line']}行)</h3>
                <p><strong>类别:</strong> {finding['category']}</p>
                <p><strong>严重程度:</strong> {finding['severity'].upper()}</p>
                <div class="code">{finding.get('code', 'N/A')}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MoltCare Shield Scanner')
    parser.add_argument('target', help='File or directory to scan')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--agent', help='Agent ID for report naming')
    
    args = parser.parse_args()
    
    scanner = ShieldScanner()
    
    path = Path(args.target)
    
    if path.is_file():
        result = scanner.scan_file(str(path))
    elif path.is_dir():
        result = scanner.scan_directory(str(path))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)
    
    # 打印结果
    print(json.dumps(result, indent=2))
    
    # 保存报告
    if args.save:
        report_path = scanner.save_report(result, args.agent)
        print(f"\nReport saved: {report_path}")
    
    # 生成HTML
    if args.html and 'file_results' not in result:
        html = scanner.generate_html_report(result)
        html_path = Path(CONFIG["scan_results_dir"]) / f"{args.agent or 'scan'}_report.html"
        with open(html_path, 'w') as f:
            f.write(html)
        print(f"\nHTML report: {html_path}")


if __name__ == "__main__":
    main()
