"""
主城页面识别器

检测当前是否在主城界面，并提供进入副本菜单的操作。
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.home")


class HomePage(BasePage):
    """主城页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在主城 — 通过 OCR 查找特征文字"""
        # 特征文字：主城界面上的固定文字
        keywords = ["委托", "挑战", "探索", "活动"]
        for kw in keywords:
            if self.recognizer.ocr_find_text(screenshot, kw):
                return True
        return False

    def enter_dungeon(self, clicker) -> bool:
        """进入副本菜单"""
        # 点击"委托"或"挑战"入口
        # TODO: 用户提供实际坐标或模板
        # clicker.click(960, 200)  # 示例：顶部菜单
        logger.info("主城 → 进入副本菜单")
        return True