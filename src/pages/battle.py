"""
战斗/结算页面识别器
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.battle")


class BattlePage(BasePage):
    """战斗页面"""

    TEMPLATE = "battle/btn_exit.png"

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在战斗中 — 匹配左上角退出按钮"""
        _ = self.recognizer
        try:
            tpl = self.recognizer.load_template("battle_exit", self.TEMPLATE)
            match = self.recognizer.match(screenshot, tpl, threshold=0.7)
            return match is not None
        except (FileNotFoundError, ValueError):
            return False

    def use_skill(self, clicker, key_code: int):
        """释放技能"""
        _ = self.recognizer
        clicker.press_key(key_code)
        logger.info(f"释放技能 (key={key_code})")


class SettlementPage(BasePage):
    """结算页面"""

    TEMPLATE = "settlement/btn_continue.png"

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在结算页"""
        _ = self.recognizer
        try:
            tpl = self.recognizer.load_template("settlement_continue", self.TEMPLATE)
            match = self.recognizer.match(screenshot, tpl, threshold=0.7)
            return match is not None
        except (FileNotFoundError, ValueError):
            return False

    def click_continue(self, clicker):
        """点击继续挑战"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info("点击继续挑战")
        # clicker.click(x, y)