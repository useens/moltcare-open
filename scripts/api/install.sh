#!/bin/bash
# HTTP API通信方案 - 一键安装脚本
# 根据节点角色自动安装相应组件

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WORKSPACE_DIR="/root/.openclaw/workspace"
API_DIR="${WORKSPACE_DIR}/scripts/api"

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 Sensen HTTP API 通信方案 - 安装程序"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用 root 权限运行${NC}"
    exit 1
fi

# 安装依赖
echo -e "${YELLOW}[1/5] 安装Python依赖...${NC}"

# 检测Python版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "  Python版本: $PYTHON_VERSION"

# 安装pip包
echo "  安装flask, requests, psutil..."
pip3 install -q flask requests psutil gunicorn 2>/dev/null || {
    echo "  使用apt安装..."
    apt-get update -qq
    apt-get install -y -qq python3-flask python3-requests python3-psutil 2>/dev/null || true
}

echo -e "${GREEN}✓${NC} 依赖安装完成"

# 创建目录
echo -e "${YELLOW}[2/5] 创建目录结构...${NC}"
mkdir -p "${API_DIR}"
mkdir -p /var/log
touch /var/log/sensen-primary.log
touch /var/log/sensen-standby.log
echo -e "${GREEN}✓${NC} 目录创建完成"

# 询问节点角色
echo ""
echo -e "${BLUE}请选择节点角色:${NC}"
echo "  1) 主节点 (云端，有公网IP)"
echo "  2) 备用节点 (本地，无公网IP)"
echo ""
read -p "选择 [1/2]: " role

case $role in
    1)
        echo -e "\n${YELLOW}[3/5] 配置主节点...${NC}"
        
        # 读取公网IP
        read -p "请输入主节点公网IP或域名: " primary_ip
        
        # 生成随机Token
        TOKEN=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p | head -1)
        
        # 创建环境配置文件
        cat > "${WORKSPACE_DIR}/.api-env" << EOF
# Sensen API配置
SENSEN_API_TOKEN=${TOKEN}
NODE_ID=primary-001
PRIMARY_URL=http://${primary_ip}:2346
EOF
        
        # 安装systemd服务
        cp "${API_DIR}/systemd/sensen-primary.service" /etc/systemd/system/
        sed -i "s/sensen-shared-secret-2024/${TOKEN}/g" /etc/systemd/system/sensen-primary.service
        
        systemctl daemon-reload
        systemctl enable sensen-primary
        
        echo -e "${GREEN}✓${NC} 主节点配置完成"
        echo ""
        echo -e "${CYAN}API Token:${NC} ${TOKEN}"
        echo -e "${CYAN}API地址:${NC} http://${primary_ip}:2346"
        echo ""
        
        # 防火墙提示
        echo -e "${YELLOW}防火墙配置提示:${NC}"
        echo "  ufw allow 2346/tcp"
        echo "  # 或"
        echo "  iptables -A INPUT -p tcp --dport 2346 -j ACCEPT"
        echo ""
        
        # 启动提示
        echo -e "${GREEN}启动命令:${NC}"
        echo "  systemctl start sensen-primary"
        echo "  # 或手动运行:"
        echo "  cd ${WORKSPACE_DIR} && python3 scripts/api/primary_server.py"
        ;;
        
    2)
        echo -e "\n${YELLOW}[3/5] 配置备用节点...${NC}"
        
        # 读取主节点信息
        read -p "请输入主节点公网IP或域名: " primary_ip
        read -p "请输入API Token: " token
        
        # 创建环境配置文件
        cat > "${WORKSPACE_DIR}/.api-env" << EOF
# Sensen API配置
PRIMARY_URL=http://${primary_ip}:2346
SENSEN_API_TOKEN=${token}
NODE_ID=standby-$(hostname)-$(date +%s | tail -c 5)
EOF
        
        # 安装systemd服务
        cp "${API_DIR}/systemd/sensen-standby.service" /etc/systemd/system/
        sed -i "s|http://localhost:2346|http://${primary_ip}:2346|g" /etc/systemd/system/sensen-standby.service
        sed -i "s/sensen-shared-secret-2024/${token}/g" /etc/systemd/system/sensen-standby.service
        
        systemctl daemon-reload
        systemctl enable sensen-standby
        
        echo -e "${GREEN}✓${NC} 备用节点配置完成"
        echo ""
        
        # 测试连接
        echo -e "${YELLOW}[4/5] 测试连接...${NC}"
        if curl -sf "http://${primary_ip}:2346/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} 成功连接到主节点"
        else
            echo -e "${RED}✗${NC} 无法连接到主节点，请检查:"
            echo "  1. 主节点是否已启动"
            echo "  2. IP地址是否正确"
            echo "  3. 防火墙是否开放2346端口"
        fi
        echo ""
        
        # 启动提示
        echo -e "${GREEN}启动命令:${NC}"
        echo "  systemctl start sensen-standby"
        echo "  # 或手动运行:"
        echo "  cd ${WORKSPACE_DIR} && python3 scripts/api/standby_client.py http://${primary_ip}:2346 ${token}"
        ;;
        
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🌲 安装完成${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "查看日志:"
echo "  tail -f /var/log/sensen-*.log"
echo ""
echo "管理服务:"
echo "  systemctl start|stop|restart|status sensen-primary|sensen-standby"
echo ""
