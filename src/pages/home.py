"""
主城页面识别器
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.home")


class HomePage(BasePage):
    """主城页面"""

    TEMPLATE = "home/btn_dungeon.png"

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在主城 — 匹配副本入口按钮"""
        _ = self.recognizer
        try:
            tpl = self.recognizer.load_template("home_btn_dungeon", self.TEMPLATE)
            match = self.recognizer.match(screenshot, tpl, threshold=0.7)
            return match is not None
        except (FileNotFoundError, ValueError):
            return False

    def enter_dungeon(self, clicker):
        """进入副本菜单"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info("主城 → 进入副本菜单")
        # clicker.click(960, 200)