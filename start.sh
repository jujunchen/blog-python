#!/bin/bash

echo "========================================"
echo "启动 Blog-Python 博客系统"
echo "========================================"
echo ""

# 激活虚拟环境
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "[错误] 虚拟环境未找到,请先运行 setup.sh 初始化环境"
    exit 1
fi

echo "[信息] 虚拟环境已激活"
echo "[信息] 启动服务器..."
echo "[信息] 访问地址: http://localhost:8000"
echo "[信息] 按 Ctrl+C 停止服务器"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000