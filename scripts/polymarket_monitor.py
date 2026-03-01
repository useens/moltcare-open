"""
Polymarket 实时概率飙升监测系统
功能：监测Polymarket上概率快速变化的事件，自动报告并跟踪准确率
"""

import requests
import json
import time
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable
from collections import deque
import threading
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MarketEvent:
    """市场事件数据结构"""
    event_id: str
    market_id: str
    title: str
    category: str
    outcome: str
    probability: float
    previous_probability: float
    change_percent: float
    volume: float
    liquidity: float
    end_date: str
    detected_at: datetime
    status: str = "active"  # active, resolved, cancelled
    actual_result: Optional[str] = None
    accuracy: Optional[bool] = None


@dataclass
class AlertConfig:
    """预警配置"""
    min_change_percent: float = 10.0  # 最小变化百分比触发预警
    min_volume: float = 100000  # 最小交易量（USD）
    min_liquidity: float = 50000  # 最小流动性
    check_interval: int = 60  # 检查间隔（秒）
    top_n: int = 10  # 每次报告前N个事件


class PolymarketMonitor:
    """Polymarket 市场监测器"""
    
    GRAPHQL_URL = "https://api.polymarket.com/graphql"
    
    def __init__(self, db_path: str = "polymarket_monitor.db"):
        self.db_path = db_path
        self.config = AlertConfig()
        self.running = False
        self.callbacks: List[Callable[[MarketEvent], None]] = []
        self._market_history: Dict[str, deque] = {}  # 市场历史价格缓存
        
        self._init_database()
        
    def _init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                market_id TEXT NOT NULL,
                title TEXT,
                category TEXT,
                outcome TEXT,
                probability REAL,
                previous_probability REAL,
                change_percent REAL,
                volume REAL,
                liquidity REAL,
                end_date TEXT,
                detected_at TEXT,
                status TEXT DEFAULT 'active',
                actual_result TEXT,
                accuracy INTEGER,
                UNIQUE(event_id, market_id, detected_at)
            )
        ''')
        
        # 统计数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY,
                total_alerts INTEGER DEFAULT 0,
                resolved_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                updated_at TEXT
            )
        ''')
        
        # 初始化统计记录
        cursor.execute('''
            INSERT OR IGNORE INTO statistics (id, updated_at) 
            VALUES (1, ?)
        ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def _fetch_markets(self) -> List[Dict]:
        """从Polymarket获取市场数据"""
        query = """
        query GetActiveMarkets {
          markets(
            where: {active: true, closed: false}
            orderBy: volume
            orderDirection: desc
            first: 100
          ) {
            id
            question
            category
            outcomePrices
            volume
            liquidity
            endDate
            outcomes
            conditionId
          }
        }
        """
        
        try:
            response = requests.post(
                self.GRAPHQL_URL,
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("markets", [])
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return []
    
    def _parse_probability(self, outcome_prices: str) -> Optional[float]:
        """解析概率价格"""
        try:
            prices = json.loads(outcome_prices)
            if isinstance(prices, list) and len(prices) >= 2:
                # 假设第一个价格是"Yes"的概率
                return float(prices[0]) * 100
            return None
        except:
            return None
    
    def _check_significant_change(
        self, 
        market_id: str, 
        current_prob: float,
        volume: float,
        liquidity: float
    ) -> Optional[float]:
        """检查是否有显著变化"""
        # 过滤低流动性市场
        if volume < self.config.min_volume or liquidity < self.config.min_liquidity:
            return None
        
        # 初始化历史记录
        if market_id not in self._market_history:
            self._market_history[market_id] = deque(maxlen=10)
        
        history = self._market_history[market_id]
        
        # 记录当前概率
        history.append({
            "probability": current_prob,
            "timestamp": datetime.now()
        })
        
        # 需要至少2个数据点
        if len(history) < 2:
            return None
        
        # 计算与10分钟前（或最早记录）的变化
        old_record = history[0]
        old_prob = old_record["probability"]
        
        change_percent = abs(current_prob - old_prob)
        
        if change_percent >= self.config.min_change_percent:
            return change_percent
        
        return None
    
    def _save_event(self, event: MarketEvent):
        """保存事件到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO events 
                (event_id, market_id, title, category, outcome, probability,
                 previous_probability, change_percent, volume, liquidity,
                 end_date, detected_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, event.market_id, event.title, event.category,
                event.outcome, event.probability, event.previous_probability,
                event.change_percent, event.volume, event.liquidity,
                event.end_date, event.detected_at.isoformat(), event.status
            ))
            conn.commit()
            
            # 更新统计
            self._update_statistics(cursor, new_alert=True)
            conn.commit()
            
        except Exception as e:
            logger.error(f"保存事件失败: {e}")
        finally:
            conn.close()
    
    def _update_statistics(self, cursor, new_alert: bool = False, resolved: bool = False, correct: bool = False):
        """更新统计数据"""
        cursor.execute("SELECT * FROM statistics WHERE id = 1")
        stats = cursor.fetchone()
        
        if not stats:
            return
        
        total_alerts = stats[1] + (1 if new_alert else 0)
        resolved_preds = stats[2] + (1 if resolved else 0)
        correct_preds = stats[3] + (1 if correct else 0)
        
        accuracy_rate = (correct_preds / resolved_preds * 100) if resolved_preds > 0 else 0.0
        
        cursor.execute('''
            UPDATE statistics SET
                total_alerts = ?,
                resolved_predictions = ?,
                correct_predictions = ?,
                accuracy_rate = ?,
                updated_at = ?
            WHERE id = 1
        ''', (total_alerts, resolved_preds, correct_preds, accuracy_rate, datetime.now().isoformat()))
    
    def scan_once(self) -> List[MarketEvent]:
        """执行一次扫描"""
        markets = self._fetch_markets()
        alerts = []
        
        logger.info(f"获取到 {len(markets)} 个活跃市场")
        
        for market in markets:
            market_id = market.get("id")
            current_prob = self._parse_probability(market.get("outcomePrices", "[]"))
            
            if current_prob is None:
                continue
            
            volume = float(market.get("volume", 0))
            liquidity = float(market.get("liquidity", 0))
            
            change = self._check_significant_change(market_id, current_prob, volume, liquidity)
            
            if change:
                history = self._market_history.get(market_id, deque())
                previous_prob = history[0]["probability"] if len(history) > 1 else current_prob
                
                event = MarketEvent(
                    event_id=market.get("conditionId", market_id),
                    market_id=market_id,
                    title=market.get("question", "Unknown"),
                    category=market.get("category", "Other"),
                    outcome="Yes" if current_prob > previous_prob else "No",
                    probability=current_prob,
                    previous_probability=previous_prob,
                    change_percent=change,
                    volume=volume,
                    liquidity=liquidity,
                    end_date=market.get("endDate", ""),
                    detected_at=datetime.now()
                )
                
                self._save_event(event)
                alerts.append(event)
                
                # 触发回调
                for callback in self.callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"回调执行失败: {e}")
        
        # 按变化幅度排序
        alerts.sort(key=lambda x: x.change_percent, reverse=True)
        
        logger.info(f"检测到 {len(alerts)} 个显著变化事件")
        return alerts[:self.config.top_n]
    
    def start_monitoring(self):
        """开始持续监测"""
        self.running = True
        logger.info(f"开始监测Polymarket (间隔: {self.config.check_interval}秒)")
        
        while self.running:
            try:
                alerts = self.scan_once()
                
                if alerts:
                    self._send_report(alerts)
                
                time.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"监测循环出错: {e}")
                time.sleep(5)
    
    def stop_monitoring(self):
        """停止监测"""
        self.running = False
        logger.info("停止监测")
    
    def _send_report(self, alerts: List[MarketEvent]):
        """发送报告 - 可自定义通知方式"""
        report = self._format_report(alerts)
        logger.info("\n" + "="*60)
        logger.info("🚨 Polymarket 概率飙升预警")
        logger.info("="*60)
        logger.info(report)
        logger.info("="*60)
        
        # 这里可以集成飞书/Discord/邮件等通知
        self._send_to_feishu(report)
    
    def _format_report(self, alerts: List[MarketEvent]) -> str:
        """格式化报告"""
        lines = []
        lines.append(f"📊 检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"📈 发现 {len(alerts)} 个概率显著变化事件\n")
        
        for i, alert in enumerate(alerts, 1):
            direction = "📈 上涨" if alert.probability > alert.previous_probability else "📉 下跌"
            lines.append(f"{i}. {direction} {alert.change_percent:.1f}%")
            lines.append(f"   标题: {alert.title}")
            lines.append(f"   概率: {alert.previous_probability:.1f}% → {alert.probability:.1f}%")
            lines.append(f"   类别: {alert.category}")
            lines.append(f"   交易量: ${alert.volume:,.0f}")
            lines.append(f"   结束时间: {alert.end_date}\n")
        
        # 添加准确率统计
        stats = self.get_statistics()
        lines.append(f"\n📊 累计统计:")
        lines.append(f"   总预警次数: {stats['total_alerts']}")
        lines.append(f"   已解决预测: {stats['resolved_predictions']}")
        lines.append(f"   准确率: {stats['accuracy_rate']:.1f}%")
        
        return "\n".join(lines)
    
    def _send_to_feishu(self, report: str):
        """发送报告到飞书 - 集成飞书消息API"""
        # 实际使用时需要配置飞书webhook或API
        # 这里预留接口
        pass
    
    def on_alert(self, callback: Callable[[MarketEvent], None]):
        """注册预警回调函数"""
        self.callbacks.append(callback)
    
    def get_active_alerts(self) -> List[MarketEvent]:
        """获取当前活跃预警"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM events 
            WHERE status = 'active'
            ORDER BY detected_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append(MarketEvent(
                event_id=row[1],
                market_id=row[2],
                title=row[3],
                category=row[4],
                outcome=row[5],
                probability=row[6],
                previous_probability=row[7],
                change_percent=row[8],
                volume=row[9],
                liquidity=row[10],
                end_date=row[11],
                detected_at=datetime.fromisoformat(row[12]),
                status=row[13],
                actual_result=row[14],
                accuracy=row[15]
            ))
        
        return events
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM statistics WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "total_alerts": row[1],
                "resolved_predictions": row[2],
                "correct_predictions": row[3],
                "accuracy_rate": row[4],
                "updated_at": row[5]
            }
        
        return {
            "total_alerts": 0,
            "resolved_predictions": 0,
            "correct_predictions": 0,
            "accuracy_rate": 0.0,
            "updated_at": None
        }
    
    def resolve_event(self, event_id: str, actual_result: str):
        """标记事件已解决并记录结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取事件信息
        cursor.execute('''
            SELECT * FROM events 
            WHERE event_id = ? AND status = 'active'
            ORDER BY detected_at DESC LIMIT 1
        ''', (event_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            logger.warning(f"未找到事件: {event_id}")
            return
        
        # 判断预测是否准确
        predicted_outcome = row[5]  # outcome
        is_correct = (predicted_outcome.lower() == actual_result.lower())
        
        # 更新事件状态
        cursor.execute('''
            UPDATE events 
            SET status = 'resolved', actual_result = ?, accuracy = ?
            WHERE id = ?
        ''', (actual_result, 1 if is_correct else 0, row[0]))
        
        # 更新统计
        self._update_statistics(cursor, resolved=True, correct=is_correct)
        
        conn.commit()
        conn.close()
        
        logger.info(f"事件已解决: {event_id}, 预测{'准确' if is_correct else '错误'}")
        
        # 发送准确率更新报告
        self._send_accuracy_update(event_id, is_correct)
    
    def _send_accuracy_update(self, event_id: str, is_correct: bool):
        """发送准确率更新通知"""
        stats = self.get_statistics()
        
        msg = f"""
🎯 预测结果更新

事件ID: {event_id}
预测结果: {'✅ 准确' if is_correct else '❌ 错误'}

📊 当前累计准确率: {stats['accuracy_rate']:.1f}%
   已解决: {stats['resolved_predictions']}/{stats['total_alerts']}
        """
        logger.info(msg)


class PolymarketCronJob:
    """Cron定时任务包装器"""
    
    def __init__(self, monitor: PolymarketMonitor):
        self.monitor = monitor
    
    def run_check(self):
        """执行一次检查（供cron调用）"""
        alerts = self.monitor.scan_once()
        return len(alerts)
    
    def run_resolution_check(self):
        """检查已结束市场并更新结果"""
        # 检查哪些市场已经关闭，尝试获取结果
        self._check_closed_markets()
    
    def _check_closed_markets(self):
        """检查已关闭市场"""
        # 获取所有活跃但可能已结束的事件
        conn = sqlite3.connect(self.monitor.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT event_id, market_id, end_date 
            FROM events 
            WHERE status = 'active'
        ''')
        
        active_events = cursor.fetchall()
        conn.close()
        
        now = datetime.now()
        for event_id, market_id, end_date in active_events:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if end < now:
                    # 市场已结束，尝试获取结果
                    self._fetch_market_result(event_id, market_id)
            except:
                pass
    
    def _fetch_market_result(self, event_id: str, market_id: str):
        """获取市场结果"""
        query = """
        query GetMarketResult($id: String!) {
          market(id: $id) {
            id
            resolvedOutcome
            outcomePrices
            closed
          }
        }
        """
        
        try:
            response = requests.post(
                self.monitor.GRAPHQL_URL,
                json={"query": query, "variables": {"id": market_id}},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            data = response.json()
            market = data.get("data", {}).get("market", {})
            
            if market.get("closed") and market.get("resolvedOutcome"):
                actual = market["resolvedOutcome"]
                self.monitor.resolve_event(event_id, actual)
                
        except Exception as e:
            logger.error(f"获取市场结果失败 {market_id}: {e}")


def main():
    """主函数 - 命令行入口"""
    import sys
    
    monitor = PolymarketMonitor()
    
    if len(sys.argv) < 2:
        print("""
Polymarket 概率飙升监测系统

用法:
  python polymarket_monitor.py start     # 启动持续监测
  python polymarket_monitor.py scan      # 执行一次扫描
  python polymarket_monitor.py stats     # 查看统计
  python polymarket_monitor.py list      # 查看活跃预警
  python polymarket_monitor.py resolve <event_id> <result>  # 手动标记结果
        """)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "start":
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    
    elif cmd == "scan":
        alerts = monitor.scan_once()
        if alerts:
            print(f"\n检测到 {len(alerts)} 个概率飙升事件")
        else:
            print("\n暂无显著变化事件")
    
    elif cmd == "stats":
        stats = monitor.get_statistics()
        print(f"""
📊 Polymarket 监测统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总预警次数: {stats['total_alerts']}
已解决预测: {stats['resolved_predictions']}
正确预测:   {stats['correct_predictions']}
累计准确率: {stats['accuracy_rate']:.1f}%
最后更新:   {stats['updated_at']}
        """)
    
    elif cmd == "list":
        events = monitor.get_active_alerts()
        if events:
            print(f"\n📋 当前 {len(events)} 个活跃预警:\n")
            for e in events:
                print(f"  • {e.title[:50]}... ({e.change_percent:.1f}%)")
        else:
            print("\n暂无活跃预警")
    
    elif cmd == "resolve" and len(sys.argv) >= 4:
        event_id = sys.argv[2]
        result = sys.argv[3]
        monitor.resolve_event(event_id, result)
    
    else:
        print("未知命令")


if __name__ == "__main__":
    main()
