# -*- coding: utf-8 -*-
"""
命令行参数解析模块

从main.py迁移的parse_arguments函数
"""

import argparse


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="A股自选股智能分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 正常运行
  python main.py --debug            # 调试模式
  python main.py --dry-run          # 仅获取数据，不进行 AI 分析
  python main.py --stocks 600519,000001  # 指定分析特定股票
  python main.py --no-notify        # 不发送推送通知
  python main.py --single-notify    # 启用单股推送模式（每分析完一只立即推送）
  python main.py --schedule         # 启用定时任务模式
  python main.py --market-review    # 仅运行大盘复盘
        """,
    )

    parser.add_argument("--debug", action="store_true", help="启用调试模式，输出详细日志")

    parser.add_argument("--dry-run", action="store_true", help="仅获取数据，不进行 AI 分析")

    parser.add_argument("--stocks", type=str, help="指定要分析的股票代码，逗号分隔（覆盖配置文件）")

    parser.add_argument("--no-notify", action="store_true", help="不发送推送通知")

    parser.add_argument(
        "--single-notify", action="store_true", help="启用单股推送模式：每分析完一只股票立即推送，而不是汇总推送"
    )

    parser.add_argument("--workers", type=int, default=None, help="并发线程数（默认使用配置值）")

    parser.add_argument("--schedule", action="store_true", help="启用定时任务模式，每日定时执行")

    parser.add_argument("--market-review", action="store_true", help="仅运行大盘复盘分析")

    parser.add_argument("--no-market-review", action="store_true", help="跳过大盘复盘分析")

    parser.add_argument("--webui", action="store_true", help="启动本地配置 WebUI")

    parser.add_argument(
        "--webui-only", action="store_true", help="仅启动 WebUI 服务，不自动执行分析（通过 /analysis API 手动触发）"
    )

    return parser.parse_args()
