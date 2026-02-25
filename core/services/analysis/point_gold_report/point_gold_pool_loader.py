# -*- coding: utf-8 -*-
"""点金术股票池配置加载。"""

import json
from pathlib import Path
from typing import List

from .point_gold_models import PointGoldAsset


class PointGoldPoolLoader:
    """加载策略股票池。"""

    def __init__(self, pool_path: Path | None = None):
        default_path = Path(__file__).parent / "point_gold_pool.json"
        self.pool_path = pool_path or default_path

    def load_assets(self) -> List[PointGoldAsset]:
        if not self.pool_path.exists():
            raise FileNotFoundError(f"点金术股票池配置不存在: {self.pool_path}")

        with open(self.pool_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assets = []
        for item in data.get("assets", []):
            asset = PointGoldAsset(
                name=str(item.get("name", "")).strip(),
                code=str(item.get("code", "")).strip(),
                group=str(item.get("group", "未分组")).strip(),
                enabled=bool(item.get("enabled", True)),
            )
            # 点金术仅纳入A股6位数字代码（不包含港股）
            if asset.name and asset.code and asset.enabled and asset.code.isdigit() and len(asset.code) == 6:
                assets.append(asset)
        return assets
