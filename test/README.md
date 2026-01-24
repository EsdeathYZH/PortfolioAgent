# 重构验证测试

本目录包含重构后的代码验证测试，所有测试都不会调用真实API，不会消耗资源。

## 环境准备

### 使用虚拟环境（推荐）

项目已配置虚拟环境，建议使用venv运行测试以确保所有依赖已安装：

```bash
# Windows PowerShell - 方式1：直接使用venv中的python（推荐）
.\venv\Scripts\python.exe test\quick_test.py

# Windows PowerShell - 方式2：激活venv后运行
.\venv\Scripts\Activate.ps1
python test\quick_test.py

# Windows - 使用便捷脚本
test\run_tests.bat

# Linux/Mac
./venv/bin/python test/quick_test.py
# 或
source venv/bin/activate
python test/quick_test.py
```

### 安装依赖

如果还没有安装依赖，请先安装：

```bash
# 创建虚拟环境（如果还没有）
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1  # Windows PowerShell
source venv/bin/activate     # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

详细说明请参考 [SETUP.md](./SETUP.md)

## 测试文件说明

### 1. test_imports.py - 导入测试
验证所有关键模块能否正常导入：
- 原有模块导入（analyzer, notification, search_service）
- 新结构模块导入（core/, infrastructure/）
- 向后兼容性验证
- 类型一致性验证

### 2. test_functionality.py - 功能测试
验证关键功能是否正常（使用Mock避免真实API调用）：
- 通知服务初始化和报告生成
- AI分析器初始化
- 搜索服务初始化
- AnalysisResult方法测试

### 3. test_integration.py - 集成测试
验证关键流程是否正常：
- main.py导入测试
- Pipeline初始化测试
- 通知渠道检测
- 数据类创建和使用

### 4. quick_test.py - 快速验证
一键运行所有测试的便捷脚本。

## 运行测试

### 方式1: 使用venv运行所有测试（推荐）
```bash
# Windows PowerShell
.\venv\Scripts\python.exe test\quick_test.py

# Linux/Mac
./venv/bin/python test/quick_test.py
```

### 方式2: 使用便捷脚本
```bash
# Windows
test\run_tests.bat

# Linux/Mac
chmod +x test/run_tests.sh
./test/run_tests.sh
```

### 方式3: 激活venv后运行
```bash
# 激活虚拟环境
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# 运行测试
cd test
python quick_test.py
```

### 方式4: 分别运行各个测试
```bash
# 使用venv中的python
.\venv\Scripts\python.exe test\test_imports.py
.\venv\Scripts\python.exe test\test_functionality.py
.\venv\Scripts\python.exe test\test_integration.py
```

## 测试原则

1. **不调用真实API**: 所有测试都使用Mock对象，不会消耗AI/数据接口资源
2. **向后兼容**: 验证新结构不影响原有代码
3. **功能完整**: 验证关键功能是否正常工作
4. **结构清晰**: 验证新目录结构是否正确

## 预期结果

所有测试应该通过，表明：
- ✅ 原有代码可以正常使用
- ✅ 新结构可以正常导入和使用
- ✅ 向后兼容性正常
- ✅ 关键功能正常

## 注意事项

- **虚拟环境**: 建议使用venv运行测试，确保所有依赖已安装
- **依赖安装**: 首次运行前必须安装requirements.txt中的所有依赖
- **测试不消耗资源**: 所有测试使用Mock，不会实际发送通知、调用AI或搜索API
- **编码问题**: Windows终端可能无法显示emoji，测试已使用ASCII字符替代

## 常见问题

### Q: 提示"No module named 'tenacity'"
A: 请确保已激活虚拟环境并安装了所有依赖：
```bash
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Q: 如何验证venv是否激活？
A: 命令提示符前会显示`(venv)`，或运行：
```bash
python -c "import sys; print(sys.prefix)"
```
如果显示venv路径，说明已激活。

### Q: 测试失败怎么办？
A:
1. 检查是否在venv环境中运行
2. 检查是否安装了所有依赖
3. 查看错误信息，可能是缺少某些可选依赖
