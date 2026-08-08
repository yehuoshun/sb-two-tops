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

    # 确认/结算按钮 OCR 搜索区域 (x, y, w, h)
    confirm_region: tuple = (400, 500, 1120, 400)
    settlement_region: tuple = (300, 600, 1320, 420)

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

    def battle(self) -> float:
        """战斗循环

        Returns:
            float: 实际战斗时长（秒）
        """
        import time as _time
        start = _time.time()
        elapsed = 0.0
        while elapsed < self.battle_timeout:
            self.controller.use_ultimate()
            _time.sleep(self.battle_interval * 0.5)
            self.controller.ranged_attack()
            _time.sleep(self.battle_interval * 0.5)
            elapsed = _time.time() - start
            if elapsed >= self.battle_timeout:
                break
            logger.info(f"[{self.name}] 战斗中... ({elapsed:.0f}s)")
        return elapsed

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

    # ── 页面检测（OCR 辅助） ──

    def is_confirm_page(self, screenshot) -> bool:
        """检测是否在确认页"""
        for keyword in self.confirm_keywords:
            if self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                  region=self.confirm_region):
                return True
        return False

    def is_settlement_page(self, screenshot) -> bool:
        """检测是否在结算页"""
        for keyword in self.settlement_keywords:
            if self.ocr.find_text(screenshot, keyword, min_score=0.3,
                                  region=self.settlement_region):
                return True
        return False