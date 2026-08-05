"""
副本页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.dungeon")

# 副本tab按钮坐标（1920x1080基准）
TAB_BUTTONS = {
    "委托": (80, 200, 120, 45),
    "夜航手册": (182, 200, 120, 45),
    "委托密函": (284, 200, 120, 45),
    "悬赏委托": (386, 200, 120, 45),
}

# 副本名称到位置的映射（TODO: 需要用户确认）
DUNGEON_POSITIONS = {}


class DungeonSelectPage(BasePage):
    """副本选择页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在副本选择页 — 图标行约2个"""
        _ = self.recognizer
        count = self.recognizer.count_icons_in_row(screenshot)
        return 1 <= count <= 3

    def select_tab(self, clicker, tab_name: str = "委托"):
        """点击指定的tab按钮

        Args:
            clicker: Clicker 实例
            tab_name: 按钮名称（委托/夜航手册/委托密函/悬赏委托）
        """
        _ = self.recognizer
        pos = TAB_BUTTONS.get(tab_name)
        if pos:
            x, y, w, h = pos
            cx, cy = x + w // 2, y + h // 2
            logger.info(f"点击tab: {tab_name} ({cx}, {cy})")
            clicker.click(cx, cy)
        else:
            logger.warning(f"未知tab: {tab_name}")

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