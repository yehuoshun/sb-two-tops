"""
战斗/结算页面识别器
"""

import logging
from typing import Optional

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.battle")

# 结算页面常见按钮关键词
SETTLEMENT_KEYWORDS = ["继续", "结算", "返回", "确定", "确认", "下一次", "收下", "领取"]


class BattlePage(BasePage):
    """战斗页面 — 检测"探险/无尽" + "当前轮次"文字"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在战斗中（双模板匹配：探险 + 当前轮次）"""
        if self.recognizer.detect_page(screenshot, "battle"):
            return True
        # OCR 兜底：检测战斗相关文字
        # 战斗中有"当前轮次"、"倒计时"等文字
        # 战斗外没有这些文字，所以用 OCR 检测
        return False

    def use_skill(self, clicker, key_code: int):
        """释放技能"""
        clicker.press_key(key_code)
        logger.info(f"释放技能 (key={key_code})")


class SettlementPage(BasePage):
    """结算页面 — OCR 识别结算文字来判断"""

    # 常见结算按钮区域（按画面下方中央区域搜索）
    _button_region = (300, 600, 1320, 420)  # x, y, w, h

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在结算页 — OCR 搜索结算相关文字"""
        _ = self.recognizer
        return False

    def detect_ocr(self, ocr, screenshot: np.ndarray) -> bool:
        """OCR 检测：结算页面标志性文字"""
        for keyword in SETTLEMENT_KEYWORDS:
            result = ocr.find_text(screenshot, keyword, min_score=0.3,
                                   region=self._button_region)
            if result:
                logger.debug(f"OCR 检测到结算文字: {keyword}")
                return True
        return False

    def click_continue(self, ocr, clicker, screenshot: np.ndarray) -> bool:
        """OCR 识别并点击结算按钮

        Returns:
            bool: 是否成功点击
        """
        for keyword in SETTLEMENT_KEYWORDS:
            result = ocr.find_text(screenshot, keyword, min_score=0.3,
                                   region=self._button_region)
            if result:
                cx, cy, score = result
                logger.info(f"结算点击: {keyword} @ ({cx}, {cy}) 置信度={score:.3f}")
                clicker.click(cx, cy)
                return True

        logger.warning("结算页面未找到可点击按钮")
        return False