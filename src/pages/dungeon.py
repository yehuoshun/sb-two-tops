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

# 未匹配到模板时的回退坐标（有滚动条时不准确，仅作最后手段）
DUNGEON_FALLBACK = {
    "探险": (510, 530),
    "无尽": (510, 530),
    "勘察": (132, 530),
    "避险": (258, 530),
    "驱逐": (384, 530),
    "调停": (636, 530),
}

# 滚动区域中心（卡片区域中间）
SCROLL_CENTER = (384, 500)

# 最大滚动尝试次数
MAX_SCROLL_ATTEMPTS = 5


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

    def select_dungeon(self, clicker, screenshot: np.ndarray, target: str = "探险") -> bool:
        """通过模板匹配定位并点击副本卡片

        匹配逻辑：
        1. 先尝试模板匹配（模板名: dungeon_{target}）
        2. 匹配到 → 点击中心坐标，重置滚动计数
        3. 没匹配到 → 滚动计数+1，滚轮向下 → 返回 False（主循环重新截图再试）
        4. 滚动超过 MAX_SCROLL_ATTEMPTS 次 → 回退硬编码坐标（日志警告）

        Args:
            clicker: Clicker 实例
            screenshot: 当前截图
            target: 目标副本名称（探险/无尽等）

        Returns:
            bool: 是否成功点击
        """
        template_name = f"dungeon_{target}"
        templates = self.config.get("dungeon", "templates", default={})
        template_path = templates.get(target)

        # 加载模板（如果路径存在且未缓存）
        if template_path:
            try:
                self.recognizer.load_template(template_name, template_path)
            except FileNotFoundError:
                logger.warning(f"模板文件不存在: {template_path}")

        # 模板匹配
        result = self.recognizer.locate(screenshot, template_name)
        if result:
            cx, cy, conf = result
            logger.info(f"匹配到 {target} @ ({cx}, {cy}) 置信度={conf:.3f}")
            clicker.click(cx, cy)
            self._scroll_attempt = 0
            return True

        # 没匹配到：滚动再试
        self._scroll_attempt += 1
        if self._scroll_attempt < MAX_SCROLL_ATTEMPTS:
            logger.info(f"未匹配到 {target}，滚动 {self._scroll_attempt}/{MAX_SCROLL_ATTEMPTS}")
            clicker.scroll(-120, SCROLL_CENTER[0], SCROLL_CENTER[1])
            return False  # 主循环重新截图再试

        # 滚动次数耗尽，回退硬编码坐标
        self._scroll_attempt = 0
        fallback = DUNGEON_FALLBACK.get(target)
        if fallback:
            cx, cy = fallback
            logger.warning(f"模板匹配 + 滚动共 {MAX_SCROLL_ATTEMPTS} 次均失败，回退坐标 ({cx}, {cy})")
            clicker.click(cx, cy)
            return True

        logger.error(f"找不到目标副本: {target}")
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