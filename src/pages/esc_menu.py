"""
ESC 菜单页面检测器

按 ESC 会弹出的主菜单界面（半透明黑底 + 左侧导航栏 + 功能网格）。
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.esc_menu")


class EscMenuPage(BasePage):
    """ESC 菜单页面 — 检测左侧导航栏图标列"""

    # 左侧导航栏区域（竖向图标列）
    _sidebar_region = (20, 150, 60, 700)  # x, y, w, h

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在 ESC 菜单页"""
        _ = self.recognizer
        return False

    def detect_ocr(self, ocr, screenshot: np.ndarray) -> bool:
        """OCR 检测中间区域是否有背包或商店"""
        center_region = (400, 150, 500, 200)
        for keyword in ["背包", "商店", "活动"]:
            result = ocr.find_text(screenshot, keyword, min_score=0.3,
                                   region=center_region)
            if result:
                logger.debug(f"OCR 检测到 ESC 菜单: {keyword}")
                return True
        return False

    def dismiss(self, controller):
        """按 ESC 关闭菜单"""
        logger.info("ESC 菜单 -> 按 ESC 关闭")
        controller.press_key("ESC", down_time=0.1)