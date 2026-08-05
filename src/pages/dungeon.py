"""
副本页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.dungeon")


class DungeonSelectPage(BasePage):
    """副本选择页面 — 检测右上角图标行（约2个）"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在副本选择页 — 图标行约2个"""
        _ = self.recognizer
        count = self.recognizer.count_icons_in_row(screenshot)
        return 1 <= count <= 3

    def select_dungeon(self, clicker, target: str = "探险"):
        """选择指定副本"""
        _ = self.recognizer
        logger.info(f"选择副本: {target}")
        # TODO: 填入实际坐标


class ConfirmPage(BasePage):
    """确认进入页面 — TODO: 需要截图"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在确认进入页"""
        _ = self.recognizer
        _ = screenshot
        logger.warning("ConfirmPage.detect 未实现")
        return False

    def confirm(self, clicker):
        """点击确认进入"""
        _ = self.recognizer
        logger.warning("ConfirmPage.confirm 未实现")