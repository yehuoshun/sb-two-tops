"""
副本页面识别器
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.dungeon")


class DungeonSelectPage(BasePage):
    """副本选择页面"""

    TEMPLATE = "dungeon/panel_title.png"

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在副本选择页"""
        _ = self.recognizer
        try:
            tpl = self.recognizer.load_template("dungeon_panel", self.TEMPLATE)
            match = self.recognizer.match(screenshot, tpl, threshold=0.7)
            return match is not None
        except (FileNotFoundError, ValueError):
            return False

    def select_dungeon(self, clicker, target: str = "探险"):
        """选择指定副本"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info(f"选择副本: {target}")
        # clicker.click(x, y)


class ConfirmPage(BasePage):
    """确认进入页面"""

    TEMPLATE = "confirm/btn_confirm.png"

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在确认进入页"""
        _ = self.recognizer
        try:
            tpl = self.recognizer.load_template("confirm_btn", self.TEMPLATE)
            match = self.recognizer.match(screenshot, tpl, threshold=0.7)
            return match is not None
        except (FileNotFoundError, ValueError):
            return False

    def confirm(self, clicker):
        """点击确认进入"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info("确认进入")
        # clicker.click(x, y)