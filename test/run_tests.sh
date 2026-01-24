#!/bin/bash
# 使用venv运行测试的便捷脚本（Linux/Mac）

echo "========================================"
echo "重构验证测试 - 使用虚拟环境"
echo "========================================"
echo ""

# 检查venv是否存在
if [ ! -f "venv/bin/python" ]; then
    echo "[错误] 虚拟环境不存在，请先创建："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 使用venv中的python运行测试
echo "[信息] 使用虚拟环境运行测试..."
echo ""

venv/bin/python test/quick_test.py

echo ""
echo "========================================"
echo "测试完成"
echo "========================================"
