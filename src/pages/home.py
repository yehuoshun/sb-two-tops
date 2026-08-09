"""
主城页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.home")


class HomePage(BasePage):
    """主城页面 — 检测右上角图标行"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在主城 — 不同城市图标行数不同（A城约8个，B城约5个等）"""
        _ = self.recognizer
        count = self.recognizer.count_icons_in_row(screenshot)
        # 阈值设低覆盖所有城市，有图标行就认为是主城
        result = count >= 3
        logger.debug(f"home.detect: icons={count} threshold=3 result={result}")
        return result

    def enter_dungeon(self, clicker):
        """进入副本菜单（按 L 键）"""
        _ = self.recognizer
        logger.info("主城 → 按 L 进入副本菜单")
        clicker.press_key("L", down_time=0.1)