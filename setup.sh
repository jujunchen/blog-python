#!/bin/bash

echo "========================================"
echo "Blog-Python 项目环境初始化"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3,请先安装 Python 3.11+"
    exit 1
fi

echo "[1/4] 检查 Python 版本..."
python3 --version

echo ""
echo "[2/4] 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在,跳过创建"
fi

echo ""
echo "[3/4] 激活虚拟环境..."
source .venv/bin/activate

echo ""
echo "[4/4] 升级 pip 并安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================"
echo "环境初始化完成!"
echo "========================================"
echo ""
echo "后续使用请运行: ./start.sh"
echo ""