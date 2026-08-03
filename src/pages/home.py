"""
主城页面识别器
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.home")


class HomePage(BasePage):
    """主城页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在主城 — 通过模板匹配"""
        _ = self.recognizer
        # TODO: 截取主城特征图后补匹配逻辑
        # 示例：self.recognizer.match(screenshot, self.recognizer.load_template("home", "templates/home/01.png"))
        return False

    def enter_dungeon(self, clicker):
        """进入副本菜单"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info("主城 → 进入副本菜单")
        # clicker.click(960, 200)