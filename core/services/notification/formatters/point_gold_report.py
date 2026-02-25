# -*- coding: utf-8 -*-
"""点金术日报格式化器（独立于现有日报）。"""

from datetime import datetime
from typing import Dict, List, Optional

from core.services.analysis.point_gold_report.point_gold_models import (
    BUY_DIVIDEND_YIELD_THRESHOLD,
    BUY_MA120_BIAS_THRESHOLD,
    BUY_PE_THRESHOLD,
    SELL_MA120_BIAS_THRESHOLD,
    PointGoldSnapshot,
)


class PointGoldReportFormatter:
    """生成点金术 Markdown 报告。"""

    def format(self, grouped: Dict[str, List[PointGoldSnapshot]], report_date: Optional[str] = None) -> str:
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")

        buy = grouped.get("buy_candidates", [])
        sell = grouped.get("sell_candidates", [])
        watch = grouped.get("watch_list", [])
        total = len(buy) + len(sell) + len(watch)

        lines = [
            f"# 点金术报告 - {report_date}",
            "",
            f"> 股票池总数: **{total}** | 买入信号: **{len(buy)}** | 卖出信号: **{len(sell)}** | 观察: **{len(watch)}**",
            "",
            "## 策略参数",
            "",
            f"- 买入条件: 偏离MA120 <= {BUY_MA120_BIAS_THRESHOLD}%, 股息率 > {BUY_DIVIDEND_YIELD_THRESHOLD}%, PE < {BUY_PE_THRESHOLD}",
            f"- 卖出条件: 偏离MA120 >= {SELL_MA120_BIAS_THRESHOLD}%",
            "",
            "## 1) 符合买入信号",
            "",
        ]
        lines.extend(self._render_table(buy))
        lines.extend(["", "## 2) 符合卖出信号", ""])
        lines.extend(self._render_table(sell))
        lines.extend(["", "## 3) 其余标的基本情况", ""])
        lines.extend(self._render_table(watch))

        missing_count = sum(
            1
            for item in (buy + sell + watch)
            if item.dividend_yield is None or item.pe is None or item.bias_ma120_pct is None
        )
        fallback_items = [item for item in (buy + sell + watch) if item.dividend_method == "fallback"]
        lines.extend(
            [
                "",
                "## 数据说明",
                "",
                "- 股息率优先使用实时字段，缺失时自动使用 fallback: 近12个月现金分红/当前价。",
                f"- 使用 fallback 计算股息率: **{len(fallback_items)}** 只"
                + (f"（{', '.join([f'{x.name}({x.code})' for x in fallback_items])}）" if fallback_items else ""),
                f"- 数据缺失标的数: **{missing_count}**",
                f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
        )
        return "\n".join(lines)

    def _render_table(self, items: List[PointGoldSnapshot]) -> List[str]:
        header = [
            "| 名称 | 代码 | 分组 | 现价 | MA120 | 偏离% | PE | 股息率% | 股息率来源 | 信号 | 备注 |",
            "|---|---|---|---:|---:|---:|---:|---:|---|---|---|",
        ]
        if not items:
            return header + ["| - | - | - | - | - | - | - | - | - | - | 无 |"]

        rows = []
        for item in items:
            rows.append(
                "| {name} | {code} | {group} | {price} | {ma120} | {bias} | {pe} | {dividend} | {method} | {signal} | {reason} |".format(
                    name=item.name,
                    code=item.code,
                    group=item.group,
                    price=self._fmt_num(item.price),
                    ma120=self._fmt_num(item.ma120),
                    bias=self._fmt_num(item.bias_ma120_pct),
                    pe=self._fmt_num(item.pe),
                    dividend=self._fmt_num(item.dividend_yield),
                    method=item.dividend_method,
                    signal=item.signal,
                    reason=item.reason.replace("|", "/"),
                )
            )
        return header + rows

    @staticmethod
    def _fmt_num(value: Optional[float]) -> str:
        if value is None:
            return "N/A"
        return f"{value:.2f}"
