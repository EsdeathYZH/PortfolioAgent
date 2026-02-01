# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 主调度程序
===================================

职责：
1. 协调各模块完成股票分析流程
2. 实现低并发的线程池调度
3. 全局异常处理，确保单股失败不影响整体
4. 提供命令行入口

使用方式：
    python main.py              # 正常运行
    python main.py --debug      # 调试模式
    python main.py --dry-run    # 仅获取数据不分析

交易理念（已融入分析）：
- 严进策略：不追高，乖离率 > 5% 不买入
- 趋势交易：只做 MA5>MA10>MA20 多头排列
- 效率优先：关注筹码集中度好的股票
- 买点偏好：缩量回踩 MA5/MA10 支撑
"""
import os

# 代理配置 - 仅在本地环境使用，GitHub Actions 不需要
if os.getenv("GITHUB_ACTIONS") != "true":
    # 本地开发环境，如需代理请取消注释或修改端口
    # os.environ["http_proxy"] = "http://127.0.0.1:10809"
    # os.environ["https_proxy"] = "http://127.0.0.1:10809"
    pass

import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from common.config import Config, get_config
from core.services.analysis import MarketAnalyzer, StockAnalysisPipeline
from core.services.notification import NotificationService
from core.services.search import SearchService
from core.services.user import UserConfigLoader
from infrastructure.ai import GeminiAnalyzer
from infrastructure.external import FeishuDocManager
from presentation.cli import parse_arguments, setup_logging

logger = logging.getLogger(__name__)


def run_market_review(notifier: NotificationService, analyzer=None, search_service=None) -> Optional[str]:
    """
    执行大盘复盘分析

    Args:
        notifier: 通知服务
        analyzer: AI分析器（可选）
        search_service: 搜索服务（可选）

    Returns:
        复盘报告文本
    """
    logger.info("开始执行大盘复盘分析...")

    try:
        market_analyzer = MarketAnalyzer(search_service=search_service, analyzer=analyzer)

        # 执行复盘
        review_report = market_analyzer.run_daily_review()

        if review_report:
            # 保存报告到文件
            date_str = datetime.now().strftime("%Y%m%d")
            report_filename = f"market_review_{date_str}.md"
            filepath = notifier.save_report_to_file(f"# 🎯 大盘复盘\n\n{review_report}", report_filename)
            logger.info(f"大盘复盘报告已保存: {filepath}")

            # 推送通知
            if notifier.is_available():
                # 添加标题
                report_content = f"🎯 大盘复盘\n\n{review_report}"

                success = notifier.send(report_content)
                if success:
                    logger.info("大盘复盘推送成功")
                else:
                    logger.warning("大盘复盘推送失败")

            return review_report

    except Exception as e:
        logger.error(f"大盘复盘分析失败: {e}")

    return None


def run_full_analysis(config: Config, args, stock_codes: Optional[List[str]] = None):
    """
    执行完整的分析流程（多用户模式）

    这是定时任务调用的主函数
    遍历所有用户，为每个用户执行分析并发送通知
    """
    try:
        # 加载用户配置
        config_loader = UserConfigLoader()
        user_configs = config_loader.load_users()

        if not user_configs:
            raise ValueError("未配置用户，请在环境变量中设置 USERS 和 USER_<username>_* 配置")

        # 命令行参数 --single-notify 覆盖配置（#55）
        if getattr(args, "single_notify", False):
            config.single_stock_notify = True

        # 为每个用户执行分析
        for user_config in user_configs:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"===== 开始为用户 {user_config.username} 执行分析 =====")
            logger.info(f"{'=' * 60}")

            if not user_config.stocks:
                logger.warning(f"用户 {user_config.username} 未配置订阅股票，跳过")
                continue

            # 创建分析流程（传入用户配置）
            pipeline = StockAnalysisPipeline(config=config, max_workers=args.workers, user_config=user_config)

            # 确定资产类型过滤
            asset_type_filter = None
            if getattr(args, "commodity_only", False):
                asset_type_filter = "gold"
            elif getattr(args, "asset_type", "all") != "all":
                asset_type_filter = args.asset_type

            # 1. 运行个股分析（使用用户的股票列表）
            user_stocks = stock_codes if stock_codes else user_config.stocks
            results = pipeline.run(
                stock_codes=user_stocks,
                dry_run=args.dry_run,
                send_notification=not args.no_notify,
                asset_type_filter=asset_type_filter,
            )

            # 2. 运行大盘复盘（如果启用且不是仅个股模式）
            market_report = ""
            if config.market_review_enabled and not args.no_market_review:
                # 只调用一次，并获取结果
                review_result = run_market_review(
                    notifier=pipeline.notifier, analyzer=pipeline.analyzer, search_service=pipeline.search_service
                )
                # 如果有结果，赋值给 market_report 用于后续飞书文档生成
                if review_result:
                    market_report = review_result

            # 输出摘要
            if results:
                logger.info(f"\n===== 用户 {user_config.username} 分析结果摘要 =====")
                for r in sorted(results, key=lambda x: x.sentiment_score, reverse=True):
                    emoji = r.get_emoji()
                    logger.info(
                        f"{emoji} {r.name}({r.code}): {r.operation_advice} | "
                        f"评分 {r.sentiment_score} | {r.trend_prediction}"
                    )

            logger.info(f"用户 {user_config.username} 分析完成，共 {len(results)} 只股票")

            # === 生成飞书云文档（如果用户配置了飞书渠道）===
            try:
                feishu_doc = FeishuDocManager()
                if feishu_doc.is_configured() and (results or market_report):
                    logger.info(f"正在为用户 {user_config.username} 创建飞书云文档...")

                    # 1. 准备标题 "01-01 13:01大盘复盘 - 用户xxx"
                    tz_cn = timezone(timedelta(hours=8))
                    now = datetime.now(tz_cn)
                    doc_title = f"{now.strftime('%Y-%m-%d %H:%M')} 大盘复盘 - {user_config.username}"

                    # 2. 准备内容 (拼接个股分析和大盘复盘)
                    full_content = ""

                    # 添加大盘复盘内容（如果有）
                    if market_report:
                        full_content += f"# 📈 大盘复盘\n\n{market_report}\n\n---\n\n"

                    # 添加个股决策仪表盘（使用 NotificationService 生成）
                    if results:
                        dashboard_content = pipeline.notifier.generate_dashboard_report(results)
                        full_content += f"# 🚀 个股决策仪表盘\n\n{dashboard_content}"

                    # 3. 创建文档
                    doc_url = feishu_doc.create_daily_doc(doc_title, full_content)
                    if doc_url:
                        logger.info(f"飞书云文档创建成功: {doc_url}")
                        # 可选：将文档链接也推送到用户的渠道
                        pipeline.notifier.send(f"[{now.strftime('%Y-%m-%d %H:%M')}] 复盘文档创建成功: {doc_url}")

            except Exception as e:
                logger.error(f"用户 {user_config.username} 飞书文档生成失败: {e}")

        logger.info("\n所有用户分析任务执行完成")

    except ValueError as e:
        logger.error(f"配置错误: {e}")
        raise
    except Exception as e:
        logger.exception(f"分析流程执行失败: {e}")


def main() -> int:
    """
    主入口函数

    Returns:
        退出码（0 表示成功）
    """
    # 解析命令行参数
    args = parse_arguments()

    # 加载配置（在设置日志前加载，以获取日志目录）
    config = get_config()

    # 配置日志（输出到控制台和文件）
    setup_logging(debug=args.debug, log_dir=config.log_dir)

    logger.info("=" * 60)
    logger.info("A股自选股智能分析系统 启动")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 验证配置
    warnings = config.validate()
    for warning in warnings:
        logger.warning(warning)

    # 解析股票列表
    stock_codes = None
    if args.stocks:
        stock_codes = [code.strip() for code in args.stocks.split(",") if code.strip()]
        logger.info(f"使用命令行指定的股票列表: {stock_codes}")

    # === 启动 WebUI (如果启用) ===
    # 优先级: 命令行参数 > 配置文件
    start_webui = (args.webui or args.webui_only or config.webui_enabled) and os.getenv("GITHUB_ACTIONS") != "true"

    if start_webui:
        try:
            from presentation.web import run_server_in_thread

            run_server_in_thread(host=config.webui_host, port=config.webui_port)
        except Exception as e:
            logger.error(f"启动 WebUI 失败: {e}")

    # === 仅 WebUI 模式：不自动执行分析 ===
    if args.webui_only:
        logger.info("模式: 仅 WebUI 服务")
        logger.info(f"WebUI 运行中: http://{config.webui_host}:{config.webui_port}")
        logger.info("通过 /analysis?code=xxx 接口手动触发分析")
        logger.info("按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n用户中断，程序退出")
        return 0

    try:
        # 处理资产类型过滤参数
        asset_type_filter = None
        if getattr(args, "commodity_only", False):
            asset_type_filter = "gold"
            logger.info("模式: 仅商品分析（黄金）")
        elif getattr(args, "asset_type", "all") != "all":
            asset_type_filter = args.asset_type
            logger.info(f"模式: 仅分析 {asset_type_filter} 类型资产")

        # 模式1: 仅大盘复盘
        if args.market_review:
            logger.info("模式: 仅大盘复盘")

            # 加载用户配置，为每个用户发送大盘复盘
            config_loader = UserConfigLoader()
            user_configs = config_loader.load_users()

            if not user_configs:
                raise ValueError("未配置用户，请在环境变量中设置 USERS 和 USER_<username>_* 配置")

            # 初始化搜索服务和分析器（如果有配置）
            search_service = None
            analyzer = None

            if config.bocha_api_keys or config.tavily_api_keys or config.serpapi_keys:
                search_service = SearchService(
                    bocha_keys=config.bocha_api_keys,
                    tavily_keys=config.tavily_api_keys,
                    serpapi_keys=config.serpapi_keys,
                )

            if config.gemini_api_key:
                analyzer = GeminiAnalyzer(api_key=config.gemini_api_key)

            # 为每个用户执行大盘复盘
            for user_config in user_configs:
                logger.info(f"为用户 {user_config.username} 执行大盘复盘...")
                notifier = NotificationService(user_config=user_config)
                run_market_review(notifier, analyzer, search_service)

            return 0

        # 模式2: 定时任务模式
        if args.schedule or config.schedule_enabled:
            logger.info("模式: 定时任务")
            logger.info(f"每日执行时间: {config.schedule_time}")

            from presentation.scheduler import run_with_schedule

            def scheduled_task():
                run_full_analysis(config, args, stock_codes)

            run_with_schedule(
                task=scheduled_task, schedule_time=config.schedule_time, run_immediately=True  # 启动时先执行一次
            )
            return 0

        # 模式3: 正常单次运行
        run_full_analysis(config, args, stock_codes)

        logger.info("\n程序执行完成")

        # 如果启用了 WebUI 且是非定时任务模式，保持程序运行以便访问 WebUI
        if start_webui and not (args.schedule or config.schedule_enabled):
            logger.info("WebUI 运行中 (按 Ctrl+C 退出)...")
            try:
                # 简单的保持活跃循环
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

        return 0

    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
        return 130

    except Exception as e:
        logger.exception(f"程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
