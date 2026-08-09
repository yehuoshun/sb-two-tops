"""
副本基类 — 定义刷本流程模板

每个副本只需继承 BaseDungeon 并配置参数即可。
"""

import time
import logging
from typing import Optional

from src.core.ocr import OCR
from src.core.game_controller import GameController

logger = logging.getLogger("sb-two-tops.dungeon")


class BaseDungeon:
    """副本基类

    子类只需覆盖：
    - name: 副本名（如 "扼守"）
    - max_scroll: 最大滚动次数
    - scroll_delta: 每次滚动量
    - scroll_center: 滚动中心坐标
    - confirm_keywords: 确认按钮文字列表
    - settlement_keywords: 结算按钮文字列表
    - battle_interval: 战斗中技能释放间隔
    - battle_timeout: 战斗超时秒数
    """

    name: str = ""
    max_scroll: int = 5
    scroll_delta: int = -120
    scroll_center: tuple = (384, 500)
    confirm_keywords: list = ["确认", "开始", "挑战", "进入", "启程"]
    settlement_keywords: list = ["继续", "结算", "返回", "确定", "下一次", "收下", "领取"]
    battle_interval: float = 2.0
    battle_timeout: float = 180.0

    # 难度选择（默认 50级，可改）
    difficulty: str = "50级"

    # 难度按钮 OCR 搜索区域 (x, y, w, h) — 全屏搜索
    difficulty_region: tuple = (0, 0, 1920, 1080)

    # 确认/结算按钮 OCR 搜索区域 (x, y, w, h)
    confirm_region: tuple = (400, 500, 1120, 400)
    settlement_region: tuple = (300, 600, 1320, 420)

    # 战斗 OCR 检测关键词
    battle_keywords: list = ["当前轮次", "轮次", "倒计时", "战斗"]

    def __init__(self, ocr: OCR, controller: GameController):
        self.ocr = ocr
        self.controller = controller
        self._scroll_attempt = 0

    # ── 副本选择 ──

    def select(self, screenshot) -> bool:
        """在当前画面中查找并点击本副本

        Returns:
            bool: 是否成功点击
        """
        result = self.ocr.find_text(screenshot, self.name, min_score=0.3)
        if result:
            cx, cy, score = result
            logger.info(f"[{self.name}] OCR 找到 @ ({cx}, {cy}) 置信度={score:.3f}")
            self.controller.click(cx, cy)
            self._scroll_attempt = 0
            return True

        self._scroll_attempt += 1
        if self._scroll_attempt < self.max_scroll:
            logger.info(f"[{self.name}] 未找到，滚动 {self._scroll_attempt}/{self.max_scroll}")
            sx, sy = self.scroll_center
            self.controller.scroll(self.scroll_delta, sx, sy)
            return False

        self._scroll_attempt = 0
        logger.error(f"[{self.name}] 滚动 {self.max_scroll} 次未找到")
        return False

    def reset_scroll(self):
        self._scroll_attempt = 0

    # ── 难度选择 ──

    def select_difficulty(self, screenshot) -> bool:
        """OCR 搜索并点击左侧难度按钮

        Returns:
            bool: 是否成功点击
        """
        # 尝试多种难度关键词（不同 UI 可能显示不同）
        keywords = [self.difficulty, "50", "Lv.50", "Level 50"]
        for keyword in keywords:
            result = self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                        region=self.difficulty_region)
            if result:
                cx, cy, score = result
                logger.info(f"[{self.name}] 难度: {keyword} @ ({cx}, {cy}) 置信度={score:.3f}")
                self.controller.click(cx, cy)
                return True

        logger.warning(f"[{self.name}] 难度按钮未找到: {self.difficulty}")
        return False

    # ── 确认进入 ──

    def confirm(self, screenshot) -> bool:
        """点击确认进入按钮

        Returns:
            bool: 是否成功点击
        """
        for keyword in self.confirm_keywords:
            result = self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                        region=self.confirm_region)
            if result:
                cx, cy, score = result
                logger.info(f"[{self.name}] 确认: {keyword} @ ({cx}, {cy}) 置信度={score:.3f}")
                self.controller.click(cx, cy)
                return True

        logger.warning(f"[{self.name}] 确认按钮未找到")
        return False

    # ── 战斗 ──

    def battle_tick(self, elapsed: float) -> bool:
        """战斗循环单次迭代

        每次调用做一轮技能操作，由主循环驱动。

        Args:
            elapsed: 已战斗时长（秒）

        Returns:
            bool: True=战斗中，False=超时
        """
        if elapsed >= self.battle_timeout:
            logger.warning(f"[{self.name}] 战斗超时 ({self.battle_timeout:.0f}s)")
            return False

        # 交替放技能
        cycle = int(elapsed / self.battle_interval)
        if cycle % 2 == 0:
            self.controller.use_ultimate()
        else:
            self.controller.ranged_attack()

        logger.info(f"[{self.name}] 战斗中... ({elapsed:.0f}s)")
        return True

    def is_battle_page(self, screenshot) -> bool:
        """OCR 检测是否在战斗中

        搜索战斗相关文字，不依赖模板匹配。
        """
        for keyword in self.battle_keywords:
            result = self.ocr.find_text(screenshot, keyword, min_score=0.3)
            if result:
                logger.debug(f"[{self.name}] 战斗页检测: {keyword} score={result[2]:.3f}")
                return True
        return False

    # ── 结算 ──

    def settlement(self, screenshot) -> bool:
        """点击结算按钮

        Returns:
            bool: 是否成功点击
        """
        for keyword in self.settlement_keywords:
            result = self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                        region=self.settlement_region)
            if result:
                cx, cy, score = result
                logger.info(f"[{self.name}] 结算: {keyword} @ ({cx}, {cy}) 置信度={score:.3f}")
                self.controller.click(cx, cy)
                return True

        logger.warning(f"[{self.name}] 结算按钮未找到")
        return False

    def is_settlement_page(self, screenshot) -> bool:
        """检测是否在结算页"""
        for keyword in self.settlement_keywords:
            if self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                  region=self.settlement_region):
                return True
        return False

    # ── 页面检测（OCR 辅助） ──

    def is_confirm_page(self, screenshot) -> bool:
        """检测是否在确认页"""
        for keyword in self.confirm_keywords:
            if self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                  region=self.confirm_region):
                return True
        return False