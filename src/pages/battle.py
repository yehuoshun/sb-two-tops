"""
战斗/结算页面识别器

检测战斗中和结算界面状态，并提供对应操作。
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.battle")


class BattlePage(BasePage):
    """战斗页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        # 战斗中特征：血量条、技能图标等
        # 或用 OCR 找"战斗"相关文字
        keywords = ["技能", "生命", "攻击", "连击"]
        for kw in keywords:
            if self.recognizer.ocr_find_text(screenshot, kw):
                return True
        return False

    def use_skill(self, clicker, key_code: int):
        """使用技能（PostMessage 键盘消息）"""
        clicker.press_key(key_code)
        logger.info(f"释放技能 (key={key_code})")


class SettlementPage(BasePage):
    """结算页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        keywords = ["继续挑战", "结算", "完成", "奖励"]
        for kw in keywords:
            if self.recognizer.ocr_find_text(screenshot, kw):
                return True
        return False

    def click_continue(self, clicker) -> bool:
        """点击继续挑战"""
        for kw in ["继续挑战", "再次挑战", "再来一次"]:
            pos = self.recognizer.find_click_point(screenshot, kw)
            if pos:
                clicker.click(pos[0], pos[1])
                logger.info("点击继续挑战")
                return True
        logger.warning("未找到继续挑战按钮")
        return False