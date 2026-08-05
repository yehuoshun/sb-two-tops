"""
战斗/结算页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.battle")


class BattlePage(BasePage):
    """战斗页面 — 检测"探险/无尽" + "当前轮次"文字"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在战斗中（双模板匹配：探险 + 当前轮次）"""
        return self.recognizer.detect_page(screenshot, "battle")

    def use_skill(self, clicker, key_code: int):
        """释放技能"""
        clicker.press_key(key_code)
        logger.info(f"释放技能 (key={key_code})")


class SettlementPage(BasePage):
    """结算页面 — TODO: 需要截图裁模板"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在结算页"""
        _ = screenshot
        logger.warning("SettlementPage.detect 未实现")
        return False

    def click_continue(self, clicker):
        """点击继续挑战"""
        _ = clicker
        logger.warning("SettlementPage.click_continue 未实现")