"""
战斗/结算页面识别器
"""

import logging
import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.battle")


class BattlePage(BasePage):
    """战斗页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        # TODO: 特征图匹配
        return False

    def use_skill(self, clicker, key_code: int):
        clicker.press_key(key_code)
        logger.info(f"释放技能 (key={key_code})")


class SettlementPage(BasePage):
    """结算页面"""

    def detect(self, screenshot: np.ndarray) -> bool:
        # TODO: 特征图匹配
        return False

    def click_continue(self, clicker):
        """点击继续挑战"""
        # TODO: 填入实际坐标
        logger.info("点击继续挑战")
        # clicker.click(x, y)