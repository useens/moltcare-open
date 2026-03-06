"""
Polymarket Monitor - 主监控程序
实时监测Polymarket事件概率飙升，记录告警，跟踪结果，统计准确率
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp
import pandas as pd
from dataclasses import dataclass, asdict
import sqlite3
from contextlib import asynccontextmanager
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置参数
CONFIG = {
    'CHECK_INTERVAL': 300,  # 检查间隔（秒）5分钟
    'SPIKE_THRESHOLD': 0.30,  # 概率飙升阈值（30%）
    'VOLUME_THRESHOLD': 1000,  # 成交量阈值（美元）
    'TIME_WINDOW': 3600,  # 时间窗口（秒）1小时
    'ALERT_COOLDOWN': 3600,  # 同一事件告警冷却时间（秒）
}

@dataclass
class MarketSnapshot:
    """市场快照"""
    market_id: str
    title: str
    question: str
    outcome: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    timestamp: datetime
    url: str

@dataclass
class Alert:
    """告警事件"""
    alert_id: str
    market_id: str
    market_title: str
    spike_before: float
    spike_after: float
    spike_percent: float
    triggering_volume: float
    alert_time: datetime
    resolved: bool = False
    final_outcome: Optional[str] = None
    correct: Optional[bool] = None
    
    def to_dict(self):
        return asdict(self)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/polymarket.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 市场快照表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    title TEXT,
                    question TEXT,
                    outcome TEXT,
                    yes_price REAL,
                    no_price REAL,
                    volume_24h REAL,
                    liquidity REAL,
                    timestamp TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 告警表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    market_id TEXT NOT NULL,
                    market_title TEXT,
                    spike_before REAL,
                    spike_after REAL,
                    spike_percent REAL,
                    triggering_volume REAL,
                    alert_time TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    final_outcome TEXT,
                    correct INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_id ON market_snapshots(market_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_time ON alerts(alert_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_id_alerts ON alerts(market_id)")
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def save_snapshot(self, snapshot: MarketSnapshot):
        """保存市场快照"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_snapshots 
                (market_id, title, question, outcome, yes_price, no_price, 
                 volume_24h, liquidity, timestamp, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.market_id, snapshot.title, snapshot.question, snapshot.outcome,
                snapshot.yes_price, snapshot.no_price, snapshot.volume_24h,
                snapshot.liquidity, snapshot.timestamp.isoformat(), snapshot.url
            ))
            conn.commit()
    
    def save_alert(self, alert: Alert):
        """保存告警"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO alerts
                (alert_id, market_id, market_title, spike_before, spike_after,
                 spike_percent, triggering_volume, alert_time, resolved,
                 final_outcome, correct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id, alert.market_id, alert.market_title,
                alert.spike_before, alert.spike_after, alert.spike_percent,
                alert.triggering_volume, alert.alert_time.isoformat(),
                alert.resolved, alert.final_outcome,
                1 if alert.correct else None if alert.correct is None else 0
            ))
            conn.commit()
    
    def get_recent_snapshots(self, market_id: str, hours: int = 1) -> List[MarketSnapshot]:
        """获取最近的市场快照"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM market_snapshots 
                WHERE market_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (market_id, cutoff.isoformat()))
            
            rows = cursor.fetchall()
            snapshots = []
            for row in rows:
                snapshots.append(MarketSnapshot(
                    market_id=row[1],
                    title=row[2],
                    question=row[3],
                    outcome=row[4],
                    yes_price=row[5],
                    no_price=row[6],
                    volume_24h=row[7],
                    liquidity=row[8],
                    timestamp=datetime.fromisoformat(row[9]),
                    url=row[10]
                ))
            return snapshots
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """获取最近的告警"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE alert_time >= ?
                ORDER BY alert_time DESC
            """, (cutoff.isoformat(),))
            
            rows = cursor.fetchall()
            alerts = []
            for row in rows:
                alerts.append(Alert(
                    alert_id=row[0],
                    market_id=row[1],
                    market_title=row[2],
                    spike_before=row[3],
                    spike_after=row[4],
                    spike_percent=row[5],
                    triggering_volume=row[6],
                    alert_time=datetime.fromisoformat(row[7]),
                    resolved=bool(row[8]),
                    final_outcome=row[9],
                    correct=row[10] if row[10] is not None else None
                ))
            return alerts
    
    def update_alert_resolution(self, alert_id: str, final_outcome: str, correct: bool):
        """更新告警的解析结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alerts 
                SET resolved = 1, final_outcome = ?, correct = ?
                WHERE alert_id = ?
            """, (final_outcome, correct, alert_id))
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总告警数
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0]
            
            # 已解析告警数
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 1")
            resolved_alerts = cursor.fetchone()[0]
            
            # 正确告警数
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE correct = 1")
            correct_alerts = cursor.fetchone()[0]
            
            # 准确率
            accuracy = correct_alerts / resolved_alerts if resolved_alerts > 0 else 0
            
            return {
                'total_alerts': total_alerts,
                'resolved_alerts': resolved_alerts,
                'correct_alerts': correct_alerts,
                'accuracy': accuracy * 100,
                'unresolved_alerts': total_alerts - resolved_alerts
            }

class PolymarketAPI:
    """Polymarket API 客户端"""
    
    def __init__(self):
        self.base_url = "https://gamma-api.polymarket.com"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_markets(self, limit: int = 100) -> List[Dict]:
        """获取活跃市场列表"""
        try:
            url = f"{self.base_url}/markets"
            params = {
                'limit': limit,
                'active': 'true',
                'order': 'volumeDesc'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"获取市场失败: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"获取市场异常: {e}")
            return []
    
    async def fetch_market_detail(self, market_id: str) -> Optional[Dict]:
        """获取市场详情"""
        try:
            url = f"{self.base_url}/markets/{market_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"获取市场详情失败: {e}")
            return None

class Monitor:
    """主监控器"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.api = PolymarketAPI()
        self.last_seen_prices: Dict[str, float] = {}
        self.report_file = "reports/daily_report.md"
        
        # 创建报告目录
        Path("reports").mkdir(exist_ok=True)
    
    async def check_spike_detection(self, snapshot: MarketSnapshot) -> Optional[Alert]:
        """检测概率飙升"""
        
        prev_snapshots = self.db.get_recent_snapshots(
            snapshot.market_id, 
            hours=CONFIG['TIME_WINDOW'] // 3600
        )
        
        if not prev_snapshots:
            self.last_seen_prices[snapshot.market_id] = snapshot.yes_price
            return None
        
        # 获取最新的上一条记录
        latest_prev = prev_snapshots[0]
        prev_price = latest_prev.yes_price
        
        # 计算变化
        price_change = snapshot.yes_price - prev_price
        price_change_percent = (price_change / prev_price * 100) if prev_price > 0 else 0
        
        # 检查是否超过阈值
        if price_change_percent >= CONFIG['SPIKE_THRESHOLD'] * 100:
            # 检查是否在冷却期内
            recent_alerts = self.db.get_recent_alerts(hours=1)
            recent_market_alerts = [a for a in recent_alerts if a.market_id == snapshot.market_id]
            
            if recent_market_alerts:
                # 最近已经告警过这个市场
                return None
            
            # 创建告警
            alert_id = f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{snapshot.market_id[:8]}"
            
            alert = Alert(
                alert_id=alert_id,
                market_id=snapshot.market_id,
                market_title=snapshot.title,
                spike_before=prev_price,
                spike_after=snapshot.yes_price,
                spike_percent=price_change_percent,
                triggering_volume=snapshot.volume_24h,
                alert_time=datetime.now()
            )
            
            return alert
        
        return None
    
    async def generate_alert_report(self, alert: Alert) -> str:
        """生成告警报告"""
        report = f"""
{'='*60}
⚠️  Polymarket 概率飙升告警
{'='*60}

📊 基本信息
  • 市场标题: {alert.market_title}
  • 市场ID: {alert.market_id}
  • 告警时间: {alert.alert_time.strftime('%Y-%m-%d %H:%M:%S')}

📈 概率变化
  • 飙升前: {alert.spike_before:.2%}
  • 飙升后: {alert.spike_after:.2%}
  • 涨幅: +{alert.spike_percent:.2f}%
  • 触发成交量: ${alert.triggering_volume:,.2f}

💡 建议行动
  1. 验证消息来源: 检查 Twitter/X、Telegram、新闻媒体
  2. 评估可信度: 官方声明 vs 谣言
  3. 考虑交易策略: 探索期 → 信号期 → 确认期
  4. 风险控制: 不All-in，设置止损点

🔗 相关链接
  • Polymarket: https://polymarket.com/event/{alert.market_id}
  • 搜索Twitter: https://twitter.com/search?q={alert.market_title[:30]}

{'='*60}
"""
        return report
    
    async def send_alert(self, alert: Alert):
        """发送告警"""
        report = await self.generate_alert_report(alert)
        
        # 保存到文件
        alert_file = f"reports/alerts/{alert.alert_id}.md"
        Path("reports/alerts").mkdir(exist_ok=True)
        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 输出到控制台和日志
        logger.info(report)
        
        # 这里可以添加其他通知方式（邮件、Telegram、Slack等）
        # 暂时只记录到文件和日志
    
    async def check_and_alert_markets(self):
        """检查市场并发送告警"""
        async with self.api:
            markets = await self.api.fetch_markets(limit=50)
            
            if not markets:
                logger.warning("未获取到市场数据")
                return
            
            for market in markets:
                try:
                    # 解析市场数据
                    market_id = market.get('slug', '')
                    if not market_id:
                        continue
                    
                    title = market.get('title', market.get('question', ''))
                    question = market.get('question', '')
                    
                    # 获取价格数据
                    outcomes = market.get('outcomes', [])
                    if not outcomes:
                        continue
                    
                    # 找到主要结果
                    outcome = outcomes[0] if outcomes else 'yes'
                    yes_price = outcomes[0].get('price', 0) if outcomes else 0
                    no_price = outcomes[1].get('price', 0) if len(outcomes) > 1 else 0
                    
                    volume = market.get('volume', 0)
                    liquidity = market.get('liquidity', 0)
                    
                    # 创建快照
                    snapshot = MarketSnapshot(
                        market_id=market_id,
                        title=title,
                        question=question,
                        outcome=outcome,
                        yes_price=yes_price,
                        no_price=no_price,
                        volume_24h=volume,
                        liquidity=liquidity,
                        timestamp=datetime.now(),
                        url=f"https://polymarket.com/event/{market_id}"
                    )
                    
                    # 保存快照
                    self.db.save_snapshot(snapshot)
                    
                    # 检测飙升
                    alert = await self.check_spike_detection(snapshot)
                    if alert:
                        # 保存告警
                        self.db.save_alert(alert)
                        # 发送告警
                        await self.send_alert(alert)
                
                except Exception as e:
                    logger.error(f"处理市场时出错: {e}, market: {market.get('title', 'unknown')}")
                    continue
    
    def generate_daily_report(self):
        """生成每日统计报告"""
        stats = self.db.get_statistics()
        recent_alerts = self.db.get_recent_alerts(hours=24)
        
        report = f"""
# Polymarket Monitor 每日报告

📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 统计概览

| 指标 | 数值 |
|------|------|
| 总告警数 | {stats['total_alerts']} |
| 已解析告警 | {stats['resolved_alerts']} |
| 正确告警 | {stats['correct_alerts']} |
| 准确率 | {stats['accuracy']:.2f}% ⭐ |
| 待解析告警 | {stats['unresolved_alerts']} |

## ⚠️  最近24小时告警

"""
        
        for i, alert in enumerate(recent_alerts, 1):
            status = "✅ 正确" if alert.correct else "❌ 错误" if alert.correct is not None else "⏳ 待解析"
            
            report += f"""
### {i}. {alert.market_title}

**状态**: {status}
**时间**: {alert.alert_time.strftime('%Y-%m-%d %H:%M:%S')}
**概率变化**: {alert.spike_before:.1%} → {alert.spike_after:.1%} (+{alert.spike_percent:.1f}%)
**成交量**: ${alert.triggering_volume:,.2f}

"""
        
        report += f"""

---

## 📌 配置参数

| 参数 | 当前值 |
|------|--------|
| 检查间隔 | {CONFIG['CHECK_INTERVAL']} 秒 |
| 概率飙升阈值 | {CONFIG['SPIKE_THRESHOLD']*100}% |
| 成交量阈值 | ${CONFIG['VOLUME_THRESHOLD']:,.2f} |
| 时间窗口 | {CONFIG['TIME_WINDOW']} 秒 |
| 告警冷却 | {CONFIG['ALERT_COOLDOWN']} 秒 |

---

*本报告由 Polymarket Monitor 自动生成*
"""
        return report
    
    def save_daily_report(self):
        """保存每日报告"""
        report = self.generate_daily_report()
        
        # 生成文件名（按日期）
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"reports/daily_{date_str}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 同时更新最新报告
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"每日报告已保存: {filename}")
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.db.get_statistics()
        
        print("\n" + "="*60)
        print("📊 Polymarket Monitor 统计信息")
        print("="*60)
        print(f"总告警数: {stats['total_alerts']}")
        print(f"已解析: {stats['resolved_alerts']}")
        print(f"正确: {stats['correct_alerts']}")
        print(f"准确率: {stats['accuracy']:.2f}%")
        print(f"待解析: {stats['unresolved_alerts']}")
        print("="*60 + "\n")

async def monitor_loop():
    """监控主循环"""
    monitor = Monitor()
    
    logger.info("🚀 Polymarket Monitor 启动")
    logger.info(f"配置: 检查间隔={CONFIG['CHECK_INTERVAL']}秒, 飙升阈值={CONFIG['SPIKE_THRESHOLD']*100}%")
    
    try:
        while True:
            logger.info(f"🔍 开始检查市场...")
            start_time = time.time()
            
            # 检查市场
            await monitor.check_and_alert_markets()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ 检查完成，耗时: {elapsed:.2f}秒")
            
            # 保存每日报告（每小时更新一次）
            if datetime.now().minute < 5:  # 整点附近
                monitor.save_daily_report()
                monitor.print_statistics()
            
            # 等待下一次检查
            logger.info(f"⏳ 等待 {CONFIG['CHECK_INTERVAL']} 秒后下次检查...")
            await asyncio.sleep(CONFIG['CHECK_INTERVAL'])
    
    except KeyboardInterrupt:
        logger.info("🛑 监控器停止（用户中断）")
    except Exception as e:
        logger.error(f"❌ 监控器异常: {e}")
    finally:
        # 最后保存一次报告
        monitor.save_daily_report()
        monitor.print_statistics()

def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════╗
║            📊 Polymarket Monitor v1.0                     ║
║     实时监测概率飙升 · 跟踪结果 · 统计准确率              ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 启动监控
    asyncio.run(monitor_loop())

if __name__ == "__main__":
    main()
