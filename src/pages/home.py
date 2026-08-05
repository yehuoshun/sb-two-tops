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
        """检测是否在主城 — 图标行约8个"""
        _ = self.recognizer
        return self.recognizer.count_icons_in_row(screenshot) >= 6

    def enter_dungeon(self, clicker):
        """进入副本菜单（按 L 键）"""
        _ = self.recognizer
        logger.info("主城 → 按 L 进入副本菜单")
        clicker.press_key("L", down_time=0.1)