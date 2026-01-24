@echo off
REM 使用venv运行测试的便捷脚本（Windows）

echo ========================================
echo 重构验证测试 - 使用虚拟环境
echo ========================================
echo.

REM 检查venv是否存在
if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先创建：
    echo   python -m venv venv
    echo   .\venv\Scripts\Activate.ps1
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM 使用venv中的python运行测试
echo [信息] 使用虚拟环境运行测试...
echo.

venv\Scripts\python.exe test\quick_test.py

echo.
echo ========================================
echo 测试完成
echo ========================================
pause
