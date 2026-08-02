"""
主入口 - sb-two-tops 自动化脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import logging
from enum import Enum, auto

from src.core.config import Config
from src.core.screenshot import Screenshot
from src.core.recognizer import Recognizer
from src.core.clicker import Clicker
from src.pages.home import HomePage
from src.pages.dungeon import DungeonSelectPage, ConfirmPage
from src.pages.battle import BattlePage, SettlementPage
from src.combos import run_combo

logger = logging.getLogger("sb-two-tops.main")


class PageState(Enum):
    UNKNOWN = auto()
    HOME = auto()
    DUNGEON_SELECT = auto()
    CONFIRM = auto()
    LOADING = auto()
    IN_DUNGEON = auto()
    SETTLEMENT = auto()


class SBAuto:
    """自动化主控制器"""

    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self._init_logging()
        self._init_modules()
        self.state = PageState.UNKNOWN
        self.run_count = 0
        self.max_runs = self.config.get("dungeon", "max_runs", default=0)
        self.target = self.config.get("dungeon", "target", default="探险")
        self.combo = self.config.get("combat", "combo", default="q")
        self.combo_interval = self.config.get("combat", "combo_interval", default=2.0)
        self._start_time = time.time()
        self._loading_start = 0
        self._dungeon_start = 0

    def _init_logging(self):
        level = getattr(logging, self.config.get("log", "level", default="INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )

    def _init_modules(self):
        self.screenshot = Screenshot(
            window_title=self.config.window_title,
            window_class=self.config.window_class,
        )
        if not self.screenshot.find_window():
            logger.error("未找到游戏窗口")
            sys.exit(1)

        self.recognizer = Recognizer()
        self.clicker = Clicker(
            hwnd=self.screenshot.hwnd,
            post_click_wait_ms=self.config.post_click_wait_ms,
        )

        cfg = self.config.data
        self.home = HomePage(self.recognizer, cfg)
        self.dungeon_select = DungeonSelectPage(self.recognizer, cfg)
        self.confirm = ConfirmPage(self.recognizer, cfg)
        self.battle = BattlePage(self.recognizer, cfg)
        self.settlement = SettlementPage(self.recognizer, cfg)

        logger.info("初始化完成")

    def _capture(self):
        img = self.screenshot.capture()
        if img is None:
            return None
        return self.screenshot.to_cv2(img)

    # ==================== 状态识别 ====================

    def _identify(self, screenshot) -> PageState:
        if self.home.detect(screenshot):
            return PageState.HOME
        if self.settlement.detect(screenshot):
            return PageState.SETTLEMENT
        if self.battle.detect(screenshot):
            return PageState.IN_DUNGEON
        if self.confirm.detect(screenshot):
            return PageState.CONFIRM
        if self.dungeon_select.detect(screenshot):
            return PageState.DUNGEON_SELECT
        return PageState.UNKNOWN

    # ==================== 状态处理 ====================

    def _handle_home(self, screenshot):
        logger.info("主城 — 前往副本")
        self.home.enter_dungeon(self.clicker)
        time.sleep(2)

    def _handle_dungeon_select(self, screenshot):
        logger.info(f"副本选择 — 选择 {self.target}")
        self.dungeon_select.select_dungeon(self.clicker, self.target)
        time.sleep(1)

    def _handle_confirm(self, screenshot):
        logger.info("确认进入副本")
        self.confirm.confirm(self.clicker)
        self._loading_start = time.time()
        time.sleep(2)

    def _handle_loading(self):
        elapsed = time.time() - self._loading_start
        if elapsed > 30:
            logger.warning("加载超时")
        else:
            logger.info(f"加载中... ({elapsed:.0f}s)")

    def _handle_battle(self, screenshot):
        if self._dungeon_start == 0:
            self._dungeon_start = time.time()
        run_combo(self.combo, self.clicker)
        elapsed = time.time() - self._dungeon_start
        logger.info(f"战斗中... ({elapsed:.0f}s) 连招: {self.combo}")
        time.sleep(self.combo_interval)

    def _handle_settlement(self, screenshot):
        self._dungeon_start = 0
        self.run_count += 1
        logger.info(f"结算 — 第 {self.run_count} 次完成")
        if self.max_runs > 0 and self.run_count >= self.max_runs:
            logger.info(f"达到最大次数 {self.max_runs}，停止")
            return False
        self.settlement.click_continue(self.clicker)
        time.sleep(2)
        return True

    # ==================== 主循环 ====================

    def run(self):
        logger.info("=" * 40)
        logger.info("sb-two-tops 启动")
        logger.info(f"目标副本: {self.target}")
        logger.info(f"战斗连招: {self.combo}")
        logger.info(f"最大次数: {'无限' if self.max_runs == 0 else self.max_runs}")
        logger.info("=" * 40)

        try:
            while True:
                screenshot = self._capture()
                if screenshot is None:
                    time.sleep(1)
                    continue

                state = self._identify(screenshot)
                if state != self.state:
                    logger.info(f"状态切换: {self.state.name} → {state.name}")
                    self.state = state

                if state == PageState.HOME:
                    self._handle_home(screenshot)
                elif state == PageState.DUNGEON_SELECT:
                    self._handle_dungeon_select(screenshot)
                elif state == PageState.CONFIRM:
                    self._handle_confirm(screenshot)
                elif state == PageState.IN_DUNGEON:
                    self._handle_battle(screenshot)
                elif state == PageState.SETTLEMENT:
                    if not self._handle_settlement(screenshot):
                        break
                elif state == PageState.LOADING:
                    self._handle_loading()
                else:
                    time.sleep(2)

                time.sleep(0.5)

        except KeyboardInterrupt:
            logger.info("用户中断")
        except Exception:
            logger.exception("运行时异常")
        finally:
            elapsed = time.time() - self._start_time
            logger.info(f"运行结束 — 共 {self.run_count} 次，耗时 {elapsed:.0f}s")


if __name__ == "__main__":
    auto = SBAuto()
    auto.run()