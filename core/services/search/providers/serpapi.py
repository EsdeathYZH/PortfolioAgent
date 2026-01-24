# -*- coding: utf-8 -*-
"""
SerpAPI搜索引擎提供者

从search_service.py迁移的SerpAPISearchProvider类
"""

import logging

# 导入基类和数据模型
from typing import List

from ..models import SearchResponse, SearchResult
from .base import BaseSearchProvider

logger = logging.getLogger(__name__)


class SerpAPISearchProvider(BaseSearchProvider):
    """
    SerpAPI 搜索引擎

    特点：
    - 支持 Google、Bing、百度等多种搜索引擎
    - 免费版每月 100 次请求
    - 返回真实的搜索结果

    文档：https://serpapi.com/
    """

    def __init__(self, api_keys: List[str]):
        super().__init__(api_keys, "SerpAPI")

    def _do_search(self, query: str, api_key: str, max_results: int) -> SearchResponse:
        """执行 SerpAPI 搜索"""
        try:
            from serpapi import GoogleSearch
        except ImportError:
            return SearchResponse(
                query=query,
                results=[],
                provider=self.name,
                success=False,
                error_message="google-search-results 未安装，请运行: pip install google-search-results",
            )

        try:
            # 使用百度搜索（对中文股票新闻更友好）
            params = {
                "engine": "baidu",  # 使用百度搜索
                "q": query,
                "api_key": api_key,
            }

            search = GoogleSearch(params)
            response = search.get_dict()

            # 记录原始响应到日志
            logger.debug(f"[SerpAPI] 原始响应 keys: {response.keys()}")

            # 解析结果
            results = []
            organic_results = response.get("organic_results", [])

            for item in organic_results[:max_results]:
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        snippet=item.get("snippet", "")[:500],
                        url=item.get("link", ""),
                        source=item.get("source", self._extract_domain(item.get("link", ""))),
                        published_date=item.get("date"),
                    )
                )

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                success=True,
            )

        except Exception as e:
            error_msg = str(e)
            return SearchResponse(query=query, results=[], provider=self.name, success=False, error_message=error_msg)

    @staticmethod
    def _extract_domain(url: str) -> str:
        """从 URL 提取域名"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "") or "未知来源"
        except:
            return "未知来源"
