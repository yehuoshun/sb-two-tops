"""
副本页面识别器

检测副本选择、确认进入、结算等页面状态。
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.dungeon")


class DungeonSelectPage(BasePage):
    """副本选择页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        keywords = ["探险", "皎皎", "勘探", "材料", "挑战"]
        for kw in keywords:
            if self.recognizer.ocr_find_text(screenshot, kw):
                return True
        return False

    def select_dungeon(self, clicker, target: str = "探险") -> bool:
        """选择指定副本"""
        # 先用 OCR 找文字，点击对应按钮
        pos = self.recognizer.find_click_point(screenshot, target)
        if pos:
            clicker.click(pos[0], pos[1])
            return True
        logger.warning(f"未找到副本入口: {target}")
        return False


class ConfirmPage(BasePage):
    """确认进入页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        keywords = ["确认", "进入", "开始挑战"]
        for kw in keywords:
            if self.recognizer.ocr_find_text(screenshot, kw):
                return True
        return False

    def confirm(self, clicker) -> bool:
        """点击确认进入"""
        pos = self.recognizer.find_click_point(screenshot, "确认")
        if pos:
            clicker.click(pos[0], pos[1])
            return True
        pos = self.recognizer.find_click_point(screenshot, "进入")
        if pos:
            clicker.click(pos[0], pos[1])
            return True
        return False