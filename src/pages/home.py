"""
主城页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.home")


class HomePage(BasePage):
    """主城页面 — 检测右上角图标行"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在主城 — 基于右上角图标行数量

        主城约8个图标，战斗页约4个。
        检测图标下半部分，不受New标签和红点干扰。
        """
        _ = self.recognizer  # PyCharm: 方法签名保留 self
        return self.recognizer.count_icons_in_row(screenshot)

    def enter_dungeon(self, clicker):
        """进入副本菜单"""
        _ = self.recognizer
        # TODO: 填入实际坐标
        logger.info("主城 → 进入副本菜单")