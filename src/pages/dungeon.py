"""
副本页面识别器
"""

import logging

import numpy as np
from src.pages.base import BasePage

logger = logging.getLogger("sb-two-tops.pages.dungeon")

# 副本tab按钮坐标（1920x1080基准）
TAB_BUTTONS = {
    "委托": (148, 218),
    "夜航手册": (248, 218),
    "委托密函": (348, 218),
    "悬赏委托": (448, 218),
}

# 滚动区域中心（卡片区域中间）
SCROLL_CENTER = (384, 500)

# 最大滚动尝试次数
MAX_SCROLL_ATTEMPTS = 5

# 委托/灾厄模式切换按钮（底部圆形星标）
MODE_TOGGLE = (75, 875)


class DungeonSelectPage(BasePage):
    """副本选择页面"""

    def __init__(self, recognizer, config: dict):
        super().__init__(recognizer, config)
        self._scroll_attempt = 0

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在副本选择页 — 图标行约2个"""
        count = self.recognizer.count_icons_in_row(screenshot)
        return 1 <= count <= 3

    def select_tab(self, clicker, tab_name: str = "委托"):
        """点击指定的tab按钮

        Args:
            clicker: Clicker 实例
            tab_name: 按钮名称（委托/夜航手册/委托密函/悬赏委托）
        """
        pos = TAB_BUTTONS.get(tab_name)
        if pos:
            cx, cy = pos
            logger.info(f"点击tab: {tab_name} ({cx}, {cy})")
            clicker.click(cx, cy)
        else:
            logger.warning(f"未知tab: {tab_name}")

    def _ensure_commission_mode(self, ocr, clicker, screenshot: np.ndarray):
        """确保在委托模式，如果是灾厄模式则切换回来

        只在底部按钮区域 OCR 搜索"委托"文字，避免误匹配顶部导航。
        有 → 已在委托模式
        没有 → 点击底部切换按钮切回委托
        """
        # 底部按钮区域 (x, y, w, h)
        btn_region = (50, 855, 100, 45)
        result = ocr.find_text(screenshot, "委托", min_score=0.3, region=btn_region)
        if result:
            logger.debug(f"OCR 检测到委托模式 @ ({result[0]}, {result[1]}) 置信度={result[2]:.3f}")
            return False

        logger.info("OCR 未检测到委托，切换回委托模式")
        clicker.click(MODE_TOGGLE[0], MODE_TOGGLE[1])
        return True

    def select_dungeon(self, ocr, clicker, screenshot: np.ndarray, target: str = "探险") -> bool:
        """通过 OCR 定位并点击副本卡片

        匹配逻辑：
        1. 先确保在委托模式
        2. OCR 识别全图，找目标副本名
        3. 找到 → 点击文字中心，重置滚动计数
        4. 没找到 → 滚动计数+1，滚轮向下 → 返回 False（主循环重新截图再试）
        5. 滚动超过 MAX_SCROLL_ATTEMPTS 次 → 放弃

        Args:
            ocr: OCR 实例
            clicker: Clicker 实例
            screenshot: 当前截图
            target: 目标副本名称（探险/无尽等）

        Returns:
            bool: 是否成功点击
        """
        # 确保在委托模式
        self._ensure_commission_mode(ocr, clicker, screenshot)

        # OCR 识别目标文字
        result = ocr.find_text(screenshot, target, min_score=0.3)
        if result:
            cx, cy, score = result
            logger.info(f"OCR 找到 {target} @ ({cx}, {cy}) 置信度={score:.3f}")
            clicker.click(cx, cy)
            self._scroll_attempt = 0
            return True

        # 没找到：滚动再试
        self._scroll_attempt += 1
        if self._scroll_attempt < MAX_SCROLL_ATTEMPTS:
            logger.info(f"OCR 未找到 {target}，滚动 {self._scroll_attempt}/{MAX_SCROLL_ATTEMPTS}")
            clicker.scroll(-120, SCROLL_CENTER[0], SCROLL_CENTER[1])
            return False  # 主循环重新截图再试

        # 滚动次数耗尽，放弃
        self._scroll_attempt = 0
        logger.error(f"OCR 找不到目标副本: {target}（已滚动 {MAX_SCROLL_ATTEMPTS} 次）")
        return False


class ConfirmPage(BasePage):
    """确认进入页面 — TODO: 需要截图"""

    def detect(self, screenshot: np.ndarray) -> bool:
        """检测是否在确认进入页"""
        _ = screenshot
        logger.warning("ConfirmPage.detect 未实现")
        return False

    def confirm(self, clicker):
        """点击确认进入"""
        logger.warning("ConfirmPage.confirm 未实现")