#!/usr/bin/env python3
"""
凭证窃取器检测脚本 v1.1
扫描系统中可能的恶意代码和凭证泄露
Signal 10 供应链攻击响应 - eudaemon_0 情报
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# 检测配置
SCAN_CONFIG = {
    "scan_paths": [
        "/root/.openclaw/workspace",
    ],
    "file_extensions": [".py", ".js", ".sh", ".md", ".json", ".yaml", ".yml"],
    "excluded_dirs": [".git", "node_modules", "__pycache__", ".venv", "venv"],
    "output_file": "reports/credential-stealer-scan-report.json"
}

# 可疑模式定义 - 使用原始字符串避免转义问题
SUSPICIOUS_PATTERNS = {
    "env_access": {
        "pattern": r"os\.environ|os\.getenv|process\.env",
        "description": "访问环境变量",
        "severity": "medium"
    },
    "config_file_access": {
        "pattern": r"open\s*\([^)]*\.(env|config|json|yaml|yml|key|pem)",
        "description": "读取配置文件",
        "severity": "medium"
    },
    "network_post": {
        "pattern": r"requests\.(post|put|patch)",
        "description": "网络数据传输(POST/PUT)",
        "severity": "high"
    },
    "network_other": {
        "pattern": r"urllib\.request\.urlopen|fetch\(|axios\.(post|put)",
        "description": "网络请求",
        "severity": "medium"
    },
    "encoding_obfuscation": {
        "pattern": r"base64\.(b64encode|encode)|binascii|hexlify",
        "description": "编码混淆",
        "severity": "medium"
    },
    "hardcoded_api_key": {
        "pattern": r"api[_-]?key\s*=\s*[\"\'][^\"\']{10,}[\"\']",
        "description": "硬编码API密钥",
        "severity": "critical"
    },
    "hardcoded_secret": {
        "pattern": r"secret[_-]?key\s*=\s*[\"\'][^\"\']{10,}[\"\']",
        "description": "硬编码Secret",
        "severity": "critical"
    },
    "hardcoded_password": {
        "pattern": r"password\s*=\s*[\"\'][^\"\']{8,}[\"\']",
        "description": "硬编码密码",
        "severity": "critical"
    },
    "hardcoded_token": {
        "pattern": r"token\s*=\s*[\"\'][^\"\']{10,}[\"\']",
        "description": "硬编码Token",
        "severity": "critical"
    },
    "sk_key_pattern": {
        "pattern": r"sk-[a-zA-Z0-9]{20,}",
        "description": "SK格式密钥",
        "severity": "critical"
    },
    "pk_key_pattern": {
        "pattern": r"pk-[a-zA-Z0-9]{20,}",
        "description": "PK格式密钥",
        "severity": "critical"
    },
    "github_token_pattern": {
        "pattern": r"gh[pousr]_[a-zA-Z0-9]{20,}",
        "description": "GitHub Token格式",
        "severity": "critical"
    },
    "dynamic_execution": {
        "pattern": r"eval\s*\(|exec\s*\(|compile\s*\(|__import__\s*\(",
        "description": "动态代码执行",
        "severity": "high"
    },
    "subprocess_execution": {
        "pattern": r"subprocess\.(call|run|Popen)",
        "description": "子进程执行",
        "severity": "medium"
    },
    "delayed_execution": {
        "pattern": r"setTimeout|setInterval|asyncio\.sleep|time\.sleep",
        "description": "延迟执行",
        "severity": "low"
    },
    "suspicious_domain": {
        "pattern": r"pastebin|ghostbin|hastebin|requestbin|webhook\.site|ngrok",
        "description": "可疑外部服务",
        "severity": "high"
    }
}


class CredentialStealerDetector:
    """凭证窃取器检测器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or SCAN_CONFIG
        self.findings = []
        self.scanned_files = 0
        self.suspicious_files = 0
        
    def scan_directory(self, path: str) -> List[Dict]:
        """扫描目录中的所有文件"""
        findings = []
        scan_path = Path(path)
        
        if not scan_path.exists():
            print(f"[!] 路径不存在: {path}")
            return findings
        
        for file_path in scan_path.rglob("*"):
            # 跳过排除的目录
            skip = False
            for excluded in self.config["excluded_dirs"]:
                if excluded in str(file_path):
                    skip = True
                    break
            if skip:
                continue
            
            # 只扫描指定扩展名
            if file_path.suffix not in self.config["file_extensions"]:
                continue
            
            # 只扫描文件
            if not file_path.is_file():
                continue
            
            file_findings = self.scan_file(file_path)
            if file_findings:
                findings.extend(file_findings)
                self.suspicious_files += 1
            
            self.scanned_files += 1
            
            # 每扫描100个文件输出进度
            if self.scanned_files % 100 == 0:
                print(f"[*] 已扫描 {self.scanned_files} 个文件...")
        
        return findings
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """扫描单个文件"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return findings
        
        # 检查每种可疑模式
        for pattern_name, pattern_info in SUSPICIOUS_PATTERNS.items():
            try:
                matches = list(re.finditer(pattern_info["pattern"], content, re.IGNORECASE))
                
                for match in matches:
                    # 找到行号
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    finding = {
                        "file": str(file_path),
                        "line_number": line_num,
                        "line_content": line_content.strip()[:200],
                        "pattern": pattern_name,
                        "description": pattern_info["description"],
                        "severity": pattern_info["severity"],
                        "matched_text": match.group()[:100],
                        "timestamp": datetime.now().isoformat()
                    }
                    findings.append(finding)
            except re.error as e:
                print(f"[!] 正则表达式错误 {pattern_name}: {e}")
                continue
        
        return findings
    
    def calculate_risk_score(self) -> Tuple[int, str]:
        """计算整体风险评分"""
        if not self.findings:
            return 0, "安全"
        
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1
        }
        
        total_score = sum(
            severity_weights.get(f["severity"], 1) 
            for f in self.findings
        )
        
        # 归一化到0-100
        risk_score = min(total_score * 2, 100)
        
        if risk_score >= 80:
            level = "严重"
        elif risk_score >= 50:
            level = "高"
        elif risk_score >= 20:
            level = "中"
        else:
            level = "低"
        
        return risk_score, level
    
    def generate_report(self) -> Dict:
        """生成扫描报告"""
        risk_score, risk_level = self.calculate_risk_score()
        
        # 按严重程度分组
        severity_groups = {"critical": [], "high": [], "medium": [], "low": []}
        for finding in self.findings:
            severity = finding.get("severity", "low")
            severity_groups[severity].append(finding)
        
        report = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "scanner_version": "1.1",
                "scan_reason": "Signal 10 - eudaemon_0 供应链攻击响应"
            },
            "summary": {
                "total_files_scanned": self.scanned_files,
                "suspicious_files": self.suspicious_files,
                "total_findings": len(self.findings),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "findings_by_severity": {
                    severity: len(findings) 
                    for severity, findings in severity_groups.items()
                }
            },
            "critical_findings": severity_groups["critical"],
            "high_findings": severity_groups["high"],
            "medium_findings": severity_groups["medium"],
            "low_findings": severity_groups["low"],
            "recommendations": self._generate_recommendations(severity_groups)
        }
        
        return report
    
    def _generate_recommendations(self, severity_groups: Dict) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        if severity_groups["critical"]:
            recommendations.append("🔴 立即行动: 存在硬编码密钥，必须立即撤销并轮换")
        
        if severity_groups["high"]:
            recommendations.append("🟠 高优先级: 审查所有网络请求和数据传输代码")
        
        if severity_groups["medium"]:
            recommendations.append("🟡 中优先级: 检查环境变量访问和配置文件读取")
        
        recommendations.extend([
            "实施密钥管理系统 (如 HashiCorp Vault)",
            "启用技能安装前的安全扫描",
            "建立供应链安全验证流程",
            "定期执行安全扫描和渗透测试",
            "启用运行时行为监控"
        ])
        
        return recommendations
    
    def run(self) -> Dict:
        """执行完整扫描流程"""
        print("=" * 60)
        print("🔒 凭证窃取器检测扫描")
        print("Signal 10 - eudaemon_0 供应链攻击响应")
        print("=" * 60)
        print()
        
        # 扫描所有配置的目录
        for scan_path in self.config["scan_paths"]:
            print(f"[*] 正在扫描: {scan_path}")
            findings = self.scan_directory(scan_path)
            self.findings.extend(findings)
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        output_path = Path(self.config["output_file"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 输出摘要
        print()
        print("=" * 60)
        print("📊 扫描结果摘要")
        print("=" * 60)
        print(f"扫描文件数: {report['summary']['total_files_scanned']}")
        print(f"可疑文件数: {report['summary']['suspicious_files']}")
        print(f"发现问题数: {report['summary']['total_findings']}")
        print(f"风险评分: {report['summary']['risk_score']}/100 ({report['summary']['risk_level']})")
        print()
        print("按严重程度分布:")
        for severity, count in report['summary']['findings_by_severity'].items():
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            print(f"  {emoji} {severity.upper()}: {count}")
        print()
        
        # 显示关键发现
        if report['critical_findings']:
            print("🔴 关键发现 (必须立即处理):")
            for finding in report['critical_findings'][:5]:
                print(f"  - {finding['file']}:{finding['line_number']}")
                print(f"    {finding['description']}: {finding['matched_text'][:50]}")
            print()
        
        print(f"📄 完整报告已保存: {output_path}")
        print()
        print("建议行动:")
        for rec in report['recommendations'][:3]:
            print(f"  • {rec}")
        
        return report


def main():
    """主入口函数"""
    detector = CredentialStealerDetector()
    report = detector.run()
    
    # 如果存在关键发现，返回非零退出码
    if report['summary']['risk_level'] in ['严重', '高']:
        print("\n⚠️  发现高风险问题，请立即审查!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
