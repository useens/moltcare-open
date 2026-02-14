# 给主节点的启动指令

## 第一步：启动API服务

在**主节点**的终端执行以下命令：

```bash
# 1. 进入API目录
cd /root/.openclaw/workspace/scripts/api

# 2. 设置环境变量
export SENSEN_API_TOKEN="sensen-shared-2024"
export NODE_ID="primary-001"

# 3. 安装依赖（如果还没安装）
pip3 install flask requests psutil -q

# 4. 启动API服务（后台运行）
nohup python3 primary_server.py > /var/log/sensen-api.log 2>&1 &

# 5. 确认启动成功
echo "等待服务启动..."
sleep 2
curl -s http://localhost:2346/health | cat

# 6. 开放防火墙端口
ufw allow 2346/tcp
# 或者如果使用iptables:
# iptables -A INPUT -p tcp --dport 2346 -j ACCEPT

echo "API服务已启动"
```

## 第二步：获取公网IP

```bash
# 查看公网IP
curl -s https://api.ipify.org
echo ""
```

**把这个IP地址告诉备用节点（森森）**

## 第三步：确认服务运行

```bash
# 查看进程
ps aux | grep primary_server

# 查看日志
tail -f /var/log/sensen-api.log

# 测试API
curl http://localhost:2346/api/nodes/primary/status \
  -H "Authorization: Bearer sensen-shared-2024"
```

## 防火墙配置（如果需要）

```bash
# Ubuntu/Debian
ufw status
ufw allow 2346/tcp
ufw reload

# CentOS/RHEL
firewall-cmd --permanent --add-port=2346/tcp
firewall-cmd --reload
```

## 常见问题

### 端口被占用
```bash
# 检查端口占用
lsof -i :2346

# 如果被占用，杀掉进程
kill -9 <PID>
```

### 服务无法启动
```bash
# 前台运行查看错误
python3 primary_server.py
```

### Python依赖缺失
```bash
pip3 install flask requests psutil gunicorn
```

---

**完成以上步骤后，告诉备用节点（森森）你的公网IP，就可以开始通信了。**
