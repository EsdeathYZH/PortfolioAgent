# -*- coding: utf-8 -*-
"""
日报格式化器

从notification.py迁移的generate_daily_report实现
"""

# 导入AnalysisResult
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.domain.analysis import AnalysisResult


class DailyReportFormatter:
    """日报格式化器"""

    def format(self, results: List[AnalysisResult], report_date: Optional[str] = None) -> str:
        """
        生成 Markdown 格式的日报（详细版）

        Args:
            results: 分析结果列表
            report_date: 报告日期（默认今天）

        Returns:
            Markdown 格式的日报内容
        """
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        # 标题
        report_lines = [
            f"# 📅 {report_date} A股自选股智能分析报告",
            "",
            f"> 共分析 **{len(results)}** 只股票 | 报告生成时间：{datetime.now().strftime('%H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # 按评分排序（高分在前）
        sorted_results = sorted(results, key=lambda x: x.sentiment_score, reverse=True)

        # 统计信息
        buy_count = sum(1 for r in results if r.operation_advice in ["买入", "加仓", "强烈买入"])
        sell_count = sum(1 for r in results if r.operation_advice in ["卖出", "减仓", "强烈卖出"])
        hold_count = sum(1 for r in results if r.operation_advice in ["持有", "观望"])
        avg_score = sum(r.sentiment_score for r in results) / len(results) if results else 0

        report_lines.extend(
            [
                "## 📊 操作建议汇总",
                "",
                f"| 指标 | 数值 |",
                f"|------|------|",
                f"| 🟢 建议买入/加仓 | **{buy_count}** 只 |",
                f"| 🟡 建议持有/观望 | **{hold_count}** 只 |",
                f"| 🔴 建议减仓/卖出 | **{sell_count}** 只 |",
                f"| 📈 平均看多评分 | **{avg_score:.1f}** 分 |",
                "",
                "---",
                "",
                "## 📈 个股详细分析",
                "",
            ]
        )

        # 逐个股票的详细分析
        for result in sorted_results:
            emoji = result.get_emoji()
            confidence_stars = result.get_confidence_stars() if hasattr(result, "get_confidence_stars") else "⭐⭐"

            report_lines.extend(
                [
                    f"### {emoji} {result.name} ({result.code})",
                    "",
                    f"**操作建议：{result.operation_advice}** | **综合评分：{result.sentiment_score}分** | **趋势预测：{result.trend_prediction}** | **置信度：{confidence_stars}**",
                    "",
                ]
            )

            # 核心看点
            if hasattr(result, "key_points") and result.key_points:
                report_lines.extend(
                    [
                        f"**🎯 核心看点**：{result.key_points}",
                        "",
                    ]
                )

            # 买入/卖出理由
            if hasattr(result, "buy_reason") and result.buy_reason:
                report_lines.extend(
                    [
                        f"**💡 操作理由**：{result.buy_reason}",
                        "",
                    ]
                )

            # 走势分析
            if hasattr(result, "trend_analysis") and result.trend_analysis:
                report_lines.extend(
                    [
                        "#### 📉 走势分析",
                        f"{result.trend_analysis}",
                        "",
                    ]
                )

            # 短期/中期展望
            outlook_lines = []
            if hasattr(result, "short_term_outlook") and result.short_term_outlook:
                outlook_lines.append(f"- **短期（1-3日）**：{result.short_term_outlook}")
            if hasattr(result, "medium_term_outlook") and result.medium_term_outlook:
                outlook_lines.append(f"- **中期（1-2周）**：{result.medium_term_outlook}")
            if outlook_lines:
                report_lines.extend(
                    [
                        "#### 🔮 市场展望",
                        *outlook_lines,
                        "",
                    ]
                )

            # 技术面分析
            tech_lines = []
            if result.technical_analysis:
                tech_lines.append(f"**综合**：{result.technical_analysis}")
            if hasattr(result, "ma_analysis") and result.ma_analysis:
                tech_lines.append(f"**均线**：{result.ma_analysis}")
            if hasattr(result, "volume_analysis") and result.volume_analysis:
                tech_lines.append(f"**量能**：{result.volume_analysis}")
            if hasattr(result, "pattern_analysis") and result.pattern_analysis:
                tech_lines.append(f"**形态**：{result.pattern_analysis}")
            if tech_lines:
                report_lines.extend(
                    [
                        "#### 📊 技术面分析",
                        *tech_lines,
                        "",
                    ]
                )

            # 基本面分析
            fund_lines = []
            if hasattr(result, "fundamental_analysis") and result.fundamental_analysis:
                fund_lines.append(result.fundamental_analysis)
            if hasattr(result, "sector_position") and result.sector_position:
                fund_lines.append(f"**板块地位**：{result.sector_position}")
            if hasattr(result, "company_highlights") and result.company_highlights:
                fund_lines.append(f"**公司亮点**：{result.company_highlights}")
            if fund_lines:
                report_lines.extend(
                    [
                        "#### 🏢 基本面分析",
                        *fund_lines,
                        "",
                    ]
                )

            # 消息面/情绪面
            news_lines = []
            if result.news_summary:
                news_lines.append(f"**新闻摘要**：{result.news_summary}")
            if hasattr(result, "market_sentiment") and result.market_sentiment:
                news_lines.append(f"**市场情绪**：{result.market_sentiment}")
            if hasattr(result, "hot_topics") and result.hot_topics:
                news_lines.append(f"**相关热点**：{result.hot_topics}")
            if news_lines:
                report_lines.extend(
                    [
                        "#### 📰 消息面/情绪面",
                        *news_lines,
                        "",
                    ]
                )

            # 综合分析
            if result.analysis_summary:
                report_lines.extend(
                    [
                        "#### 📝 综合分析",
                        result.analysis_summary,
                        "",
                    ]
                )

            # 风险提示
            if hasattr(result, "risk_warning") and result.risk_warning:
                report_lines.extend(
                    [
                        f"⚠️ **风险提示**：{result.risk_warning}",
                        "",
                    ]
                )

            # 数据来源说明
            if hasattr(result, "search_performed") and result.search_performed:
                report_lines.append(f"*🔍 已执行联网搜索*")
            if hasattr(result, "data_sources") and result.data_sources:
                report_lines.append(f"*📋 数据来源：{result.data_sources}*")

            # 错误信息（如果有）
            if not result.success and result.error_message:
                report_lines.extend(
                    [
                        "",
                        f"❌ **分析异常**：{result.error_message[:100]}",
                    ]
                )

            report_lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )

        # 底部信息（去除免责声明）
        report_lines.extend(
            [
                "",
                f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(report_lines)
