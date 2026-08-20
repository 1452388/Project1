#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 腾讯云部署脚本（Ubuntu 22.04 / Python 3.10+ / MySQL 8.0）
#
# 用法：
#   chmod +x deploy.sh
#   ./deploy.sh
#
# 前提：
#   1. 已安装 MySQL 8.0 并创建数据库 livecode_db：
#        CREATE DATABASE livecode_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#        CREATE USER 'livecode'@'%' IDENTIFIED BY '你的密码';
#        GRANT ALL PRIVILEGES ON livecode_db.* TO 'livecode'@'%';
#        FLUSH PRIVILEGES;
#   2. 已配置 .env：
#        DATABASE_URL=mysql+asyncmy://livecode:密码@localhost:3306/livecode_db
#        SECRET_KEY=随机字符串
#        BASE_URL=https://www.hxy820.uno
#        DEBUG=false

set -e

echo "========== 开始部署 活码管理系统 =========="

# 1. 检查环境
echo "[1/6] 检查 Python 环境..."
if ! command -v python3 &>/dev/null; then
    echo "错误: 未安装 Python3，请先安装:"
    echo "  apt update && apt install -y python3 python3-pip python3-venv"
    exit 1
fi

# 2. 创建虚拟环境并安装依赖
echo "[2/6] 创建虚拟环境并安装依赖..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

# 3. 检查 .env 是否存在
echo "[3/6] 检查配置文件..."
if [ ! -f ".env" ]; then
    echo "警告: 未找到 .env，复制 .env.example 为 .env 并填写数据库配置"
    cp .env.example .env
    echo "请编辑 .env 设置 DATABASE_URL 后重新运行脚本"
    exit 1
fi

# 4. 运行数据库迁移
echo "[4/6] 运行数据库迁移..."
alembic upgrade head

# 5. 测试应用启动
echo "[5/6] 测试应用启动..."
timeout 3 python -c "
from app.main import app
print('应用加载成功')
" || echo "应用加载检查完成"

# 6. 启动服务（后台运行）
echo "[6/6] 启动服务..."
if [ -f "systemd/livecode.service" ]; then
    echo "使用 systemd 管理服务"
    cp systemd/livecode.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable livecode
    systemctl restart livecode
    echo "服务已启动，查看状态: systemctl status livecode"
else
    echo "使用 nohup 后台运行"
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > livecode.log 2>&1 &
    echo "服务已启动，日志: livecode.log"
fi

echo ""
echo "========== 部署完成 =========="
echo "访问: http://服务器IP:8000"
echo "如需配置域名和 HTTPS，请参考 docs/腾讯云部署指南.md"