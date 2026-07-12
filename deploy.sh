#!/bin/bash
# ═══════════════════════════════════════
#  丫丫计时器 — Ubuntu 一键部署脚本
#  用法: sudo bash deploy.sh
# ═══════════════════════════════════════

set -e

APP_DIR="/opt/yaya-timer"
echo "🚀 丫丫计时器 部署开始..."

# ── 1. 安装依赖 ──
echo "📦 安装 Nginx..."
apt-get update -qq && apt-get install -y -qq nginx python3

# ── 2. 创建目录 & 复制文件 ──
echo "📁 部署文件到 $APP_DIR..."
mkdir -p "$APP_DIR"
cp index.html manifest.json data.json server.py "$APP_DIR/"

# ── 3. Python systemd 服务 ──
echo "⚙️ 配置后端服务..."
cat > /etc/systemd/system/yaya-api.service << 'UNIT'
[Unit]
Description=Yaya Timer API Proxy
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/yaya-timer
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable yaya-api --now
echo "✅ 后端服务已启动"

# ── 4. Nginx 配置 ──
echo "🌐 配置 Nginx..."
cp nginx.conf /etc/nginx/sites-available/yaya-timer
ln -sf /etc/nginx/sites-available/yaya-timer /etc/nginx/sites-enabled/

# 删除默认站点
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
echo "✅ Nginx 已配置"

# ── 5. 开放防火墙 ──
if command -v ufw &>/dev/null; then
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    echo "🔓 防火墙已开放 80/443 端口"
fi

# ── 完成 ──
IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo "════════════════════════════════"
echo "  🎉 部署完成！"
echo "  访问: http://$IP"
echo ""
echo "  常用命令:"
echo "  systemctl status yaya-api   # 查看后端状态"
echo "  journalctl -u yaya-api -f   # 查看后端日志"
echo "  nginx -t && nginx -s reload # 重载 Nginx"
echo "════════════════════════════════"
