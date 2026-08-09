"""
配置模块 - JSON 配置文件加载，坐标自动缩放
"""

import json
from pathlib import Path
from typing import Any, Optional, cast
import logging

logger = logging.getLogger("sb-two-tops.config")


class Config:
    """配置管理器"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.data: dict[str, Any] = {}
        self._base_width = 1920
        self._base_height = 1080
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self._base_width = self.data.get("game", {}).get("screen_width", 1920)
        self._base_height = self.data.get("game", {}).get("screen_height", 1080)
        logger.info(f"配置加载成功 (基准分辨率 {self._base_width}x{self._base_height})")

    def save(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get(self, *keys, default=None):
        """安全获取嵌套配置值"""
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
                if val is None:
                    return default
            else:
                return default
        return val if val is not None else default

    @property
    def window_title(self) -> str:
        return cast(str, self.get("game", "window_title", default="二重螺旋"))

    @property
    def window_class(self) -> Optional[str]:
        return self.get("game", "window_class", default=None)

    @property
    def scale(self):
        return self._base_width, self._base_height

    @property
    def post_click_wait_ms(self) -> int:
        return self.get("game", "post_click_wait_ms", default=500)