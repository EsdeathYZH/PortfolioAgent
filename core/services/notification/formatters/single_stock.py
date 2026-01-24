# -*- coding: utf-8 -*-
"""
单股报告格式化器

从notification.py迁移的generate_single_stock_report实现
"""

# 导入AnalysisResult和工具函数
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.domain.analysis import AnalysisResult

from .utils import get_signal_level


class SingleStockFormatter:
    """单股报告格式化器"""

    def format(self, result: AnalysisResult) -> str:
        """
        生成单只股票的分析报告（用于单股推送模式 #55）

        格式精简但信息完整，适合每分析完一只股票立即推送

        Args:
            result: 单只股票的分析结果

        Returns:
            Markdown 格式的单股报告
        """
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        signal_text, signal_emoji, _ = get_signal_level(result)
        dashboard = result.dashboard if hasattr(result, "dashboard") and result.dashboard else {}
        core = dashboard.get("core_conclusion", {}) if dashboard else {}
        battle = dashboard.get("battle_plan", {}) if dashboard else {}
        intel = dashboard.get("intelligence", {}) if dashboard else {}

        # 股票名称
        stock_name = result.name if result.name and not result.name.startswith("股票") else f"股票{result.code}"

        lines = [
            f"## {signal_emoji} {stock_name} ({result.code})",
            "",
            f"> {report_date} | 评分: **{result.sentiment_score}** | {result.trend_prediction}",
            "",
        ]

        # 核心决策（一句话）
        one_sentence = core.get("one_sentence", result.analysis_summary) if core else result.analysis_summary
        if one_sentence:
            lines.extend(
                [
                    "### 📌 核心结论",
                    "",
                    f"**{signal_text}**: {one_sentence}",
                    "",
                ]
            )

        # 重要信息（舆情+基本面）
        info_added = False
        if intel:
            if intel.get("earnings_outlook"):
                if not info_added:
                    lines.append("### 📰 重要信息")
                    lines.append("")
                    info_added = True
                lines.append(f"📊 **业绩预期**: {intel['earnings_outlook'][:100]}")

            if intel.get("sentiment_summary"):
                if not info_added:
                    lines.append("### 📰 重要信息")
                    lines.append("")
                    info_added = True
                lines.append(f"💭 **舆情情绪**: {intel['sentiment_summary'][:80]}")

            # 风险警报
            risks = intel.get("risk_alerts", [])
            if risks:
                if not info_added:
                    lines.append("### 📰 重要信息")
                    lines.append("")
                    info_added = True
                lines.append("")
                lines.append("🚨 **风险警报**:")
                for risk in risks[:3]:
                    lines.append(f"- {risk[:60]}")

            # 利好催化
            catalysts = intel.get("positive_catalysts", [])
            if catalysts:
                lines.append("")
                lines.append("✨ **利好催化**:")
                for cat in catalysts[:3]:
                    lines.append(f"- {cat[:60]}")

        if info_added:
            lines.append("")

        # 狙击点位
        sniper = battle.get("sniper_points", {}) if battle else {}
        if sniper:
            lines.extend(
                [
                    "### 🎯 操作点位",
                    "",
                    "| 买点 | 止损 | 目标 |",
                    "|------|------|------|",
                ]
            )
            ideal_buy = sniper.get("ideal_buy", "-")
            stop_loss = sniper.get("stop_loss", "-")
            take_profit = sniper.get("take_profit", "-")
            lines.append(f"| {ideal_buy} | {stop_loss} | {take_profit} |")
            lines.append("")

        # 持仓建议
        pos_advice = core.get("position_advice", {}) if core else {}
        if pos_advice:
            lines.extend(
                [
                    "### 💼 持仓建议",
                    "",
                    f"- 🆕 **空仓者**: {pos_advice.get('no_position', result.operation_advice)}",
                    f"- 💼 **持仓者**: {pos_advice.get('has_position', '继续持有')}",
                    "",
                ]
            )

        lines.extend(
            [
                "---",
                "*AI生成，仅供参考，不构成投资建议*",
            ]
        )

        return "\n".join(lines)
