"""
Polymarket Monitor Web 仪表板
提供实时监控数据的Web界面
"""

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
DB_PATH = "data/polymarket.db"

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_statistics():
    """获取统计数据"""
    conn = get_db_connection()
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 1")
    resolved = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE correct = 1")
    correct = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 1 AND correct = 0")
    incorrect = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
    pending = cursor.fetchone()[0]
    
    accuracy = (correct / resolved * 100) if resolved > 0 else 0
    
    conn.close()
    
    return {
        'total': total,
        'resolved': resolved,
        'correct': correct,
        'incorrect': incorrect,
        'pending': pending,
        'accuracy': accuracy
    }

def get_recent_alerts(limit=20):
    """获取最近的告警"""
    conn = get_db_connection()
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT alert_id, market_title, spike_before, spike_after, 
               spike_percent, alert_time, resolved, final_outcome, correct
        FROM alerts
        ORDER BY alert_time DESC
        LIMIT ?
    """, (limit,))
    
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            'alert_id': row['alert_id'],
            'market_title': row['market_title'],
            'spike_before': row['spike_before'],
            'spike_after': row['spike_after'],
            'spike_percent': row['spike_percent'],
            'alert_time': row['alert_time'],
            'resolved': row['resolved'],
            'final_outcome': row['final_outcome'],
            'correct': row['correct']
        })
    
    conn.close()
    return alerts

def get_accuracy_timeline(days=30):
    """获取准确率时间线"""
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    timeline = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # 获取当天的解析数据
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct
            FROM alerts
            WHERE DATE(alert_time) = ?
        """, (date,))
        
        row = cursor.fetchone()
        if row['total'] > 0:
            accuracy = (row['correct'] / row['total'] * 100) if row['total'] > 0 else 0
            timeline.append({
                'date': date,
                'total': row['total'],
                'correct': row['correct'],
                'accuracy': accuracy
            })
    
    conn.close()
    return reversed(timeline)

@app.route('/')
def dashboard():
    """主仪表板页面"""
    stats = get_statistics()
    recent_alerts = get_recent_alerts(10)
    timeline = list(get_accuracy_timeline(7))
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         alerts=recent_alerts,
                         timeline=timeline)

@app.route('/api/stats')
def api_stats():
    """API: 获取统计数据"""
    return jsonify(get_statistics())

@app.route('/api/alerts')
def api_alerts():
    """API: 获取告警列表"""
    limit = int(request.args.get('limit', 50))
    return jsonify(get_recent_alerts(limit))

@app.route('/api/timeline')
def api_timeline():
    """API: 获取准确率时间线"""
    days = int(request.args.get('days', 30))
    return jsonify(list(get_accuracy_timeline(days)))

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║         🌐 Polymarket Monitor Web Dashboard                ║
║         访问 http://localhost:5000 查看仪表板             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
