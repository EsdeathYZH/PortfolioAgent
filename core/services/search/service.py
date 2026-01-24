# -*- coding: utf-8 -*-
"""
搜索服务统一接口

从search_service.py迁移的SearchService类完整实现
"""

import logging

# 导入Provider和数据模型
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from search_service import SearchResponse

from .providers.base import BaseSearchProvider
from .providers.bocha import BochaSearchProvider
from .providers.serpapi import SerpAPISearchProvider
from .providers.tavily import TavilySearchProvider

logger = logging.getLogger(__name__)


class SearchService:
    """
    搜索服务

    功能：
    1. 管理多个搜索引擎
    2. 自动故障转移
    3. 结果聚合和格式化
    """

    def __init__(
        self,
        bocha_keys: Optional[List[str]] = None,
        tavily_keys: Optional[List[str]] = None,
        serpapi_keys: Optional[List[str]] = None,
    ):
        """
        初始化搜索服务

        Args:
            bocha_keys: 博查搜索 API Key 列表
            tavily_keys: Tavily API Key 列表
            serpapi_keys: SerpAPI Key 列表
        """
        self._providers: List[BaseSearchProvider] = []

        # 初始化搜索引擎（按优先级排序）
        # 1. Bocha 优先（中文搜索优化，AI摘要）
        if bocha_keys:
            self._providers.append(BochaSearchProvider(bocha_keys))
            logger.info(f"已配置 Bocha 搜索，共 {len(bocha_keys)} 个 API Key")

        # 2. Tavily（免费额度更多，每月 1000 次）
        if tavily_keys:
            self._providers.append(TavilySearchProvider(tavily_keys))
            logger.info(f"已配置 Tavily 搜索，共 {len(tavily_keys)} 个 API Key")

        # 3. SerpAPI 作为备选（每月 100 次）
        if serpapi_keys:
            self._providers.append(SerpAPISearchProvider(serpapi_keys))
            logger.info(f"已配置 SerpAPI 搜索，共 {len(serpapi_keys)} 个 API Key")

        if not self._providers:
            logger.warning("未配置任何搜索引擎 API Key，新闻搜索功能将不可用")

    @property
    def is_available(self) -> bool:
        """检查是否有可用的搜索引擎"""
        return any(p.is_available for p in self._providers)

    def search_stock_news(
        self, stock_code: str, stock_name: str, max_results: int = 5, focus_keywords: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        搜索股票相关新闻

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            max_results: 最大返回结果数
            focus_keywords: 重点关注的关键词列表

        Returns:
            SearchResponse 对象
        """
        # 默认重点关注关键词（基于交易理念）
        if focus_keywords is None:
            focus_keywords = [
                "年报预告",
                "业绩预告",
                "业绩快报",  # 业绩相关
                "减持",
                "增持",
                "回购",  # 股东动向
                "机构调研",
                "机构评级",  # 机构动向
                "利好",
                "利空",  # 消息面
                "合同",
                "订单",
                "中标",  # 业务进展
            ]

        # 构建搜索查询（优化搜索效果）
        # 主查询：股票名称 + 核心关键词
        query = f"{stock_name} {stock_code} 股票 最新消息"

        logger.info(f"搜索股票新闻: {stock_name}({stock_code})")

        # 依次尝试各个搜索引擎
        for provider in self._providers:
            if not provider.is_available:
                continue

            response = provider.search(query, max_results)

            if response.success and response.results:
                logger.info(f"使用 {provider.name} 搜索成功")
                return response
            else:
                logger.warning(f"{provider.name} 搜索失败: {response.error_message}，尝试下一个引擎")

        # 所有引擎都失败
        return SearchResponse(
            query=query, results=[], provider="None", success=False, error_message="所有搜索引擎都不可用或搜索失败"
        )

    def search_stock_events(
        self, stock_code: str, stock_name: str, event_types: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        搜索股票特定事件（年报预告、减持等）

        专门针对交易决策相关的重要事件进行搜索

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            event_types: 事件类型列表

        Returns:
            SearchResponse 对象
        """
        if event_types is None:
            event_types = ["年报预告", "减持公告", "业绩快报"]

        # 构建针对性查询
        event_query = " OR ".join(event_types)
        query = f"{stock_name} ({event_query})"

        logger.info(f"搜索股票事件: {stock_name}({stock_code}) - {event_types}")

        # 依次尝试各个搜索引擎
        for provider in self._providers:
            if not provider.is_available:
                continue

            response = provider.search(query, max_results=5)

            if response.success:
                return response

        return SearchResponse(query=query, results=[], provider="None", success=False, error_message="事件搜索失败")

    def search_comprehensive_intel(
        self, stock_code: str, stock_name: str, max_searches: int = 3
    ) -> Dict[str, SearchResponse]:
        """
        多维度情报搜索（同时使用多个引擎、多个维度）

        搜索维度：
        1. 最新消息 - 近期新闻动态
        2. 风险排查 - 减持、处罚、利空
        3. 业绩预期 - 年报预告、业绩快报

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            max_searches: 最大搜索次数

        Returns:
            {维度名称: SearchResponse} 字典
        """
        results = {}
        search_count = 0

        # 定义搜索维度
        search_dimensions = [
            {"name": "latest_news", "query": f"{stock_name} {stock_code} 最新 新闻 2026年1月", "desc": "最新消息"},
            {"name": "risk_check", "query": f"{stock_name} 减持 处罚 利空 风险", "desc": "风险排查"},
            {"name": "earnings", "query": f"{stock_name} 年报预告 业绩预告 业绩快报 2025年报", "desc": "业绩预期"},
        ]

        logger.info(f"开始多维度情报搜索: {stock_name}({stock_code})")

        # 轮流使用不同的搜索引擎
        provider_index = 0

        for dim in search_dimensions:
            if search_count >= max_searches:
                break

            # 选择搜索引擎（轮流使用）
            available_providers = [p for p in self._providers if p.is_available]
            if not available_providers:
                break

            provider = available_providers[provider_index % len(available_providers)]
            provider_index += 1

            logger.info(f"[情报搜索] {dim['desc']}: 使用 {provider.name}")

            response = provider.search(dim["query"], max_results=3)
            results[dim["name"]] = response
            search_count += 1

            if response.success:
                logger.info(f"[情报搜索] {dim['desc']}: 获取 {len(response.results)} 条结果")
            else:
                logger.warning(f"[情报搜索] {dim['desc']}: 搜索失败 - {response.error_message}")

            # 短暂延迟避免请求过快
            time.sleep(0.5)

        return results

    def format_intel_report(self, intel_results: Dict[str, SearchResponse], stock_name: str) -> str:
        """
        格式化情报搜索结果为报告

        Args:
            intel_results: 多维度搜索结果
            stock_name: 股票名称

        Returns:
            格式化的情报报告文本
        """
        lines = [f"【{stock_name} 情报搜索结果】"]

        # 最新消息
        if "latest_news" in intel_results:
            resp = intel_results["latest_news"]
            lines.append(f"\n📰 最新消息 (来源: {resp.provider}):")
            if resp.success and resp.results:
                for i, r in enumerate(resp.results[:3], 1):
                    date_str = f" [{r.published_date}]" if r.published_date else ""
                    lines.append(f"  {i}. {r.title}{date_str}")
                    lines.append(f"     {r.snippet[:100]}...")
            else:
                lines.append("  未找到相关消息")

        # 风险排查
        if "risk_check" in intel_results:
            resp = intel_results["risk_check"]
            lines.append(f"\n⚠️ 风险排查 (来源: {resp.provider}):")
            if resp.success and resp.results:
                for i, r in enumerate(resp.results[:3], 1):
                    lines.append(f"  {i}. {r.title}")
                    lines.append(f"     {r.snippet[:100]}...")
            else:
                lines.append("  未发现明显风险信号")

        # 业绩预期
        if "earnings" in intel_results:
            resp = intel_results["earnings"]
            lines.append(f"\n📊 业绩预期 (来源: {resp.provider}):")
            if resp.success and resp.results:
                for i, r in enumerate(resp.results[:3], 1):
                    lines.append(f"  {i}. {r.title}")
                    lines.append(f"     {r.snippet[:100]}...")
            else:
                lines.append("  未找到业绩相关信息")

        return "\n".join(lines)

    def batch_search(
        self, stocks: List[Dict[str, str]], max_results_per_stock: int = 3, delay_between: float = 1.0
    ) -> Dict[str, SearchResponse]:
        """
        批量搜索多只股票新闻

        Args:
            stocks: 股票列表 [{"code": "300389", "name": "艾比森"}, ...]
            max_results_per_stock: 每只股票的最大结果数
            delay_between: 每次搜索之间的延迟（秒）

        Returns:
            {股票代码: SearchResponse} 字典
        """
        results = {}

        for i, stock in enumerate(stocks):
            if i > 0:
                time.sleep(delay_between)

            code = stock.get("code", "")
            name = stock.get("name", "")

            response = self.search_stock_news(code, name, max_results_per_stock)
            results[code] = response

        return results


# === 便捷函数 ===
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """获取搜索服务单例"""
    global _search_service

    if _search_service is None:
        from config import get_config

        config = get_config()
        _search_service = SearchService(
            bocha_keys=config.bocha_api_keys,
            tavily_keys=config.tavily_api_keys,
            serpapi_keys=config.serpapi_keys,
        )

    return _search_service


def reset_search_service() -> None:
    """重置搜索服务单例（用于测试）"""
    global _search_service
    _search_service = None
