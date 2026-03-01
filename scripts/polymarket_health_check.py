#!/usr/bin/env python3
"""
Polymarket 监测健康检查器
三日志架构：操作日志、错误日志、审计日志
"""

import os
import sys
import sqlite3
import psutil
from datetime import datetime, timedelta

WORKSPACE = "/root/.openclaw/workspace"
DB_PATH = os.path.join(WORKSPACE, "polymarket_monitor.db")
LOG_DIR = os.path.join(WORKSPACE, "logs")
PID_FILE = os.path.join(WORKSPACE, ".polymarket_monitor.pid")


class HealthChecker:
    def __init__(self):
        self.issues = []
        self.recommendations = []
    
    def check_process(self):
        """检查进程状态"""
        if not os.path.exists(PID_FILE):
            self.issues.append("❌ PID文件不存在")
            return False
        
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            
            if not psutil.pid_exists(pid):
                self.issues.append(f"❌ 进程 {pid} 不存在")
                return False
            
            process = psutil.Process(pid)
            if process.status() != psutil.STATUS_RUNNING:
                self.issues.append(f"⚠️ 进程状态异常: {process.status()}")
                return False
            
            # 检查资源使用
            mem_mb = process.memory_info().rss / 1024 / 1024
            if mem_mb > 200:
                self.recommendations.append(f"⚠️ 内存使用较高: {mem_mb:.1f}MB")
            
            return True
            
        except Exception as e:
            self.issues.append(f"❌ 检查进程失败: {e}")
            return False
    
    def check_database(self):
        """检查数据库健康"""
        if not os.path.exists(DB_PATH):
            self.issues.append("❌ 数据库文件不存在")
            return False
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 检查表存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            required = ['events', 'statistics']
            for table in required:
                if table not in tables:
                    self.issues.append(f"❌ 缺失表: {table}")
            
            # 检查数据新鲜度
            cursor.execute("SELECT COUNT(*), MAX(detected_at) FROM events")
            count, last_time = cursor.fetchone()
            
            if count == 0:
                self.recommendations.append("ℹ️ 数据库为空，正在积累历史数据")
            elif last_time:
                last = datetime.fromisoformat(last_time)
                if datetime.now() - last > timedelta(minutes=5):
                    self.issues.append(f"⚠️ 数据超过5分钟未更新")
            
            conn.close()
            return len(self.issues) == 0 or all(not i.startswith("❌") for i in self.issues)
            
        except Exception as e:
            self.issues.append(f"❌ 数据库检查失败: {e}")
            return False
    
    def check_logs(self):
        """检查日志健康"""
        op_log = os.path.join(LOG_DIR, "polymarket_monitor.log")
        error_log = os.path.join(LOG_DIR, "polymarket_error.log")
        audit_log = os.path.join(LOG_DIR, "polymarket_audit.log")
        
        # 检查操作日志
        if os.path.exists(op_log):
            mtime = datetime.fromtimestamp(os.path.getmtime(op_log))
            if datetime.now() - mtime > timedelta(minutes=2):
                self.issues.append("⚠️ 操作日志超过2分钟未更新")
        
        # 检查错误日志
        if os.path.exists(error_log):
            with open(error_log) as f:
                errors = f.readlines()
                recent_errors = [e for e in errors if datetime.now().hour == datetime.now().hour]
                if len(recent_errors) > 10:
                    self.issues.append(f"❌ 近期错误过多: {len(recent_errors)}条")
        
        return True
    
    def check_data_freshness(self):
        """检查数据新鲜度"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 获取最近活跃预警
            cursor.execute('''
                SELECT COUNT(*) FROM events 
                WHERE status = 'active' 
                AND detected_at > datetime('now', '-1 hour')
            ''')
            recent_alerts = cursor.fetchone()[0]
            
            # 获取统计
            cursor.execute("SELECT total_alerts, accuracy_rate FROM statistics WHERE id = 1")
            stats = cursor.fetchone()
            
            conn.close()
            
            return {
                "recent_alerts": recent_alerts,
                "total_alerts": stats[0] if stats else 0,
                "accuracy_rate": stats[1] if stats else 0.0
            }
            
        except Exception as e:
            self.issues.append(f"⚠️ 数据检查失败: {e}")
            return None
    
    def run_all_checks(self):
        """运行所有检查"""
        print("="*60)
        print("🔍 Polymarket 监测健康检查")
        print("="*60)
        
        # 进程检查
        print("\n1️⃣ 进程状态...")
        if self.check_process():
            print("   ✅ 进程运行正常")
        else:
            print("   " + "\n   ".join(self.issues[-1:]))
        
        # 数据库检查
        print("\n2️⃣ 数据库状态...")
        if self.check_database():
            print("   ✅ 数据库正常")
        else:
            for issue in self.issues:
                if "数据库" in issue or "表" in issue or "数据" in issue:
                    print(f"   {issue}")
        
        # 日志检查
        print("\n3️⃣ 日志状态...")
        if self.check_logs():
            print("   ✅ 日志系统正常")
        
        # 数据新鲜度
        print("\n4️⃣ 数据新鲜度...")
        data = self.check_data_freshness()
        if data:
            print(f"   📊 总预警: {data['total_alerts']}")
            print(f"   📈 准确率: {data['accuracy_rate']:.1f}%")
            print(f"   🔔 近1小时预警: {data['recent_alerts']}")
        
        # 建议
        if self.recommendations:
            print("\n💡 建议:")
            for rec in self.recommendations:
                print(f"   {rec}")
        
        print("\n" + "="*60)
        
        # 返回是否健康
        critical_issues = [i for i in self.issues if i.startswith("❌")]
        return len(critical_issues) == 0
    
    def auto_fix(self):
        """自动修复问题"""
        print("\n🔧 尝试自动修复...")
        
        fixed = []
        
        # 重启服务
        if not self.check_process():
            print("   重启监测服务...")
            os.system(f"cd {WORKSPACE} && ./scripts/polymarket_service.sh restart")
            fixed.append("重启服务")
        
        if fixed:
            print(f"   ✅ 已修复: {', '.join(fixed)}")
        else:
            print("   ℹ️ 无需修复")


def main():
    checker = HealthChecker()
    healthy = checker.run_all_checks()
    
    if not healthy:
        checker.auto_fix()
    
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.exit(main())
