# 备用节点AI客户端 - 快速部署指南

## 一键部署命令

```bash
# 1. 下载AI客户端代码
cd /root/.openclaw/workspace/scripts
curl -o standby-ai-client.py \
  https://raw.githubusercontent.com/useens/linlin-backup/master/scripts/standby-ai-client.py

# 2. 停止旧客户端
sudo systemctl stop sensen-websocket-v2

# 3. 测试新客户端（前台运行，按Ctrl+C停止）
python3 standby-ai-client.py

# 4. 如果测试正常，更新systemd服务
sudo tee /etc/systemd/system/sensen-websocket-v2.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Sensen Standby AI Client
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/scripts/standby-ai-client.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# 5. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable sensen-websocket-v2
sudo systemctl start sensen-websocket-v2

# 6. 验证状态
sudo systemctl status sensen-websocket-v2
```

## 部署验证

部署成功后，本地大脑将：
- ✅ 自动参与融合会议
- ✅ 生成技术分析报告
- ✅ 智能回复消息
- ✅ 独立思考和执行任务

## 部署后通知

部署完成后，请通知云端大脑：
"本地大脑AI客户端已部署完成"

然后召开真正的双节点融合会议！
