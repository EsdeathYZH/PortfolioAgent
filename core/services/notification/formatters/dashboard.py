# -*- coding: utf-8 -*-
"""
决策仪表盘格式化器

从notification.py迁移的generate_dashboard_report实现
"""

# 导入AnalysisResult和工具函数
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.domain.analysis import AnalysisResult

from .utils import get_signal_level


class DashboardFormatter:
    """决策仪表盘格式化器"""

    def format(self, results: List[AnalysisResult], report_date: Optional[str] = None) -> str:
        """
        生成决策仪表盘格式的日报（详细版）

        格式：市场概览 + 重要信息 + 核心结论 + 数据透视 + 作战计划

        Args:
            results: 分析结果列表
            report_date: 报告日期（默认今天）

        Returns:
            Markdown 格式的决策仪表盘日报
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        # 按评分排序（高分在前）
        sorted_results = sorted(results, key=lambda x: x.sentiment_score, reverse=True)

        # 统计信息
        buy_count = sum(1 for r in results if r.operation_advice in ["买入", "加仓", "强烈买入"])
        sell_count = sum(1 for r in results if r.operation_advice in ["卖出", "减仓", "强烈卖出"])
        hold_count = sum(1 for r in results if r.operation_advice in ["持有", "观望"])

        report_lines = [
            f"# 🎯 {report_date} 决策仪表盘",
            "",
            f"> 共分析 **{len(results)}** 只股票 | 🟢买入:{buy_count} 🟡观望:{hold_count} 🔴卖出:{sell_count}",
            "",
            "---",
            "",
        ]

        # 逐个股票的决策仪表盘
        for result in sorted_results:
            signal_text, signal_emoji, signal_tag = get_signal_level(result)
            dashboard = result.dashboard if hasattr(result, "dashboard") and result.dashboard else {}

            # 股票名称（优先使用 dashboard 或 result 中的名称）
            stock_name = result.name if result.name and not result.name.startswith("股票") else f"股票{result.code}"

            report_lines.extend(
                [
                    f"## {signal_emoji} {stock_name} ({result.code})",
                    "",
                ]
            )

            # ========== 舆情与基本面概览（放在最前面）==========
            intel = dashboard.get("intelligence", {}) if dashboard else {}
            if intel:
                report_lines.extend(
                    [
                        "### 📰 重要信息速览",
                        "",
                    ]
                )

                # 舆情情绪总结
                if intel.get("sentiment_summary"):
                    report_lines.append(f"**💭 舆情情绪**: {intel['sentiment_summary']}")

                # 业绩预期
                if intel.get("earnings_outlook"):
                    report_lines.append(f"**📊 业绩预期**: {intel['earnings_outlook']}")

                # 风险警报（醒目显示）
                risk_alerts = intel.get("risk_alerts", [])
                if risk_alerts:
                    report_lines.append("")
                    report_lines.append("**🚨 风险警报**:")
                    for alert in risk_alerts:
                        report_lines.append(f"- {alert}")

                # 利好催化
                catalysts = intel.get("positive_catalysts", [])
                if catalysts:
                    report_lines.append("")
                    report_lines.append("**✨ 利好催化**:")
                    for cat in catalysts:
                        report_lines.append(f"- {cat}")

                # 最新消息
                if intel.get("latest_news"):
                    report_lines.append("")
                    report_lines.append(f"**📢 最新动态**: {intel['latest_news']}")

                report_lines.append("")

            # ========== 核心结论 ==========
            core = dashboard.get("core_conclusion", {}) if dashboard else {}
            one_sentence = core.get("one_sentence", result.analysis_summary) if core else result.analysis_summary
            time_sense = core.get("time_sensitivity", "本周内") if core else "本周内"
            pos_advice = core.get("position_advice", {}) if core else {}

            report_lines.extend(
                [
                    "### 📌 核心结论",
                    "",
                    f"**{signal_emoji} {signal_text}** | {result.trend_prediction}",
                    "",
                    f"> **一句话决策**: {one_sentence}",
                    "",
                    f"⏰ **时效性**: {time_sense}",
                    "",
                ]
            )

            # 持仓分类建议
            if pos_advice:
                report_lines.extend(
                    [
                        "| 持仓情况 | 操作建议 |",
                        "|---------|---------|",
                        f"| 🆕 **空仓者** | {pos_advice.get('no_position', result.operation_advice)} |",
                        f"| 💼 **持仓者** | {pos_advice.get('has_position', '继续持有')} |",
                        "",
                    ]
                )

            # ========== 数据透视 ==========
            data_persp = dashboard.get("data_perspective", {}) if dashboard else {}
            if data_persp:
                trend_data = data_persp.get("trend_status", {})
                price_data = data_persp.get("price_position", {})
                vol_data = data_persp.get("volume_analysis", {})
                chip_data = data_persp.get("chip_structure", {})

                report_lines.extend(
                    [
                        "### 📊 数据透视",
                        "",
                    ]
                )

                # 趋势状态
                if trend_data:
                    is_bullish = "✅ 是" if trend_data.get("is_bullish", False) else "❌ 否"
                    report_lines.extend(
                        [
                            f"**均线排列**: {trend_data.get('ma_alignment', 'N/A')} | 多头排列: {is_bullish} | 趋势强度: {trend_data.get('trend_score', 'N/A')}/100",
                            "",
                        ]
                    )

                # 价格位置
                if price_data:
                    bias_status = price_data.get("bias_status", "N/A")
                    bias_emoji = "✅" if bias_status == "安全" else ("⚠️" if bias_status == "警戒" else "🚨")
                    report_lines.extend(
                        [
                            "| 价格指标 | 数值 |",
                            "|---------|------|",
                            f"| 当前价 | {price_data.get('current_price', 'N/A')} |",
                            f"| MA5 | {price_data.get('ma5', 'N/A')} |",
                            f"| MA10 | {price_data.get('ma10', 'N/A')} |",
                            f"| MA20 | {price_data.get('ma20', 'N/A')} |",
                            f"| 乖离率(MA5) | {price_data.get('bias_ma5', 'N/A')}% {bias_emoji}{bias_status} |",
                            f"| 支撑位 | {price_data.get('support_level', 'N/A')} |",
                            f"| 压力位 | {price_data.get('resistance_level', 'N/A')} |",
                            "",
                        ]
                    )

                # 量能分析
                if vol_data:
                    report_lines.extend(
                        [
                            f"**量能**: 量比 {vol_data.get('volume_ratio', 'N/A')} ({vol_data.get('volume_status', '')}) | 换手率 {vol_data.get('turnover_rate', 'N/A')}%",
                            f"💡 *{vol_data.get('volume_meaning', '')}*",
                            "",
                        ]
                    )

                # 筹码结构
                if chip_data:
                    chip_health = chip_data.get("chip_health", "N/A")
                    chip_emoji = "✅" if chip_health == "健康" else ("⚠️" if chip_health == "一般" else "🚨")
                    report_lines.extend(
                        [
                            f"**筹码**: 获利比例 {chip_data.get('profit_ratio', 'N/A')} | 平均成本 {chip_data.get('avg_cost', 'N/A')} | 集中度 {chip_data.get('concentration', 'N/A')} {chip_emoji}{chip_health}",
                            "",
                        ]
                    )

            # ========== 作战计划 ==========
            battle = dashboard.get("battle_plan", {}) if dashboard else {}
            if battle:
                report_lines.extend(
                    [
                        "### 🎯 作战计划",
                        "",
                    ]
                )

                # 狙击点位
                sniper = battle.get("sniper_points", {})
                if sniper:
                    report_lines.extend(
                        [
                            "**📍 狙击点位**",
                            "",
                            "| 点位类型 | 价格 |",
                            "|---------|------|",
                            f"| 🎯 理想买入点 | {sniper.get('ideal_buy', 'N/A')} |",
                            f"| 🔵 次优买入点 | {sniper.get('secondary_buy', 'N/A')} |",
                            f"| 🛑 止损位 | {sniper.get('stop_loss', 'N/A')} |",
                            f"| 🎊 目标位 | {sniper.get('take_profit', 'N/A')} |",
                            "",
                        ]
                    )

                # 仓位策略
                position = battle.get("position_strategy", {})
                if position:
                    report_lines.extend(
                        [
                            f"**💰 仓位建议**: {position.get('suggested_position', 'N/A')}",
                            f"- 建仓策略: {position.get('entry_plan', 'N/A')}",
                            f"- 风控策略: {position.get('risk_control', 'N/A')}",
                            "",
                        ]
                    )

                # 检查清单
                checklist = battle.get("action_checklist", [])
                if checklist:
                    report_lines.extend(
                        [
                            "**✅ 检查清单**",
                            "",
                        ]
                    )
                    for item in checklist:
                        report_lines.append(f"- {item}")
                    report_lines.append("")

            # 如果没有 dashboard，显示传统格式
            if not dashboard:
                # 操作理由
                if hasattr(result, "buy_reason") and result.buy_reason:
                    report_lines.extend(
                        [
                            f"**💡 操作理由**: {result.buy_reason}",
                            "",
                        ]
                    )

                # 风险提示
                if hasattr(result, "risk_warning") and result.risk_warning:
                    report_lines.extend(
                        [
                            f"**⚠️ 风险提示**: {result.risk_warning}",
                            "",
                        ]
                    )

                # 技术面分析
                if (hasattr(result, "ma_analysis") and result.ma_analysis) or (
                    hasattr(result, "volume_analysis") and result.volume_analysis
                ):
                    report_lines.extend(
                        [
                            "### 📊 技术面",
                            "",
                        ]
                    )
                    if hasattr(result, "ma_analysis") and result.ma_analysis:
                        report_lines.append(f"**均线**: {result.ma_analysis}")
                    if hasattr(result, "volume_analysis") and result.volume_analysis:
                        report_lines.append(f"**量能**: {result.volume_analysis}")
                    report_lines.append("")

                # 消息面
                if result.news_summary:
                    report_lines.extend(
                        [
                            "### 📰 消息面",
                            f"{result.news_summary}",
                            "",
                        ]
                    )

            report_lines.extend(
                [
                    "---",
                    "",
                ]
            )

        # 底部（去除免责声明）
        report_lines.extend(
            [
                "",
                f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(report_lines)
