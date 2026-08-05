"""
主城页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.home")


class HomePage(BasePage):
    """主城页面 — 检测左侧任务面板"追踪任务"文字"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在主城"""
        _ = self.recognizer  # PyCharm: 方法签名保留 self
        return self.recognizer.detect_page(screenshot, "home")

    def enter_dungeon(self, clicker):
        """进入副本菜单"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info("主城 → 进入副本菜单")