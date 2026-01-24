# -*- coding: utf-8 -*-
"""
快速验证脚本 - 一键运行所有测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("重构验证测试 - 快速验证")
    print("=" * 70)
    print("\n注意: 所有测试都不会调用真实API，不会消耗资源")
    print("=" * 70)

    all_passed = True

    # 1. 导入测试
    print("\n" + "=" * 70)
    print("阶段1: 导入测试")
    print("=" * 70)
    try:
        from test_imports import main as test_imports_main

        all_passed = test_imports_main() and all_passed
    except Exception as e:
        print(f"[FAIL] 导入测试执行失败: {e}")
        all_passed = False

    # 2. 功能测试
    print("\n" + "=" * 70)
    print("阶段2: 功能测试")
    print("=" * 70)
    try:
        from test_functionality import main as test_functionality_main

        all_passed = test_functionality_main() and all_passed
    except Exception as e:
        print(f"[FAIL] 功能测试执行失败: {e}")
        all_passed = False

    # 3. 集成测试
    print("\n" + "=" * 70)
    print("阶段3: 集成测试")
    print("=" * 70)
    try:
        from test_integration import main as test_integration_main

        all_passed = test_integration_main() and all_passed
    except Exception as e:
        print(f"[FAIL] 集成测试执行失败: {e}")
        all_passed = False

    # 总结
    print("\n" + "=" * 70)
    print("最终结果")
    print("=" * 70)
    if all_passed:
        print("[PASS] 所有测试通过！重构验证成功")
        print("\n重构后的代码结构:")
        print("  - core/services/notification/    通知服务")
        print("  - infrastructure/ai/            AI模块")
        print("  - core/services/search/         搜索服务")
        print("  - core/domain/                  领域模型")
        print("\n所有新结构都保持向后兼容，原有代码无需修改即可使用。")
    else:
        print("[FAIL] 部分测试失败，请检查错误信息")
        print("\n建议:")
        print("  1. 检查导入路径是否正确")
        print("  2. 检查是否有循环依赖")
        print("  3. 检查新结构中的向后兼容实现")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
