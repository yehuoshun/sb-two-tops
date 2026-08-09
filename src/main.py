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
from src.core.clicker import MouseClicker
from src.core.keyboard import Keyboard
from src.core.ocr import OCR
from src.core.game_controller import GameController
from src.pages.home import HomePage
from src.pages.dungeon import DungeonSelectPage
from src.pages.battle import BattlePage
from src.dungeons import get_dungeon

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
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self._init_logging()
        self._init_modules()
        self.state = PageState.UNKNOWN
        self.run_count = 0
        self.max_runs = self.config.get("dungeon", "max_runs", default=0)
        self.target = self.config.get("dungeon", "target", default="扼守")
        self._start_time = time.time()
        self._loading_start = 0
        self._unknown_count = 0
        self._max_unknown = 10

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
        self.ocr = OCR()

        self.mouse = MouseClicker(hwnd=self.screenshot.hwnd)
        self.keyboard = Keyboard(hwnd=self.screenshot.hwnd)
        self.controller = GameController(self.mouse, self.keyboard)

        cfg = self.config.data
        self.home = HomePage(self.recognizer, cfg)
        self.dungeon_select = DungeonSelectPage(self.recognizer, cfg)
        self.battle = BattlePage(self.recognizer, cfg)

        # 加载目标副本
        DungeonCls = get_dungeon(self.target)
        self.dungeon = DungeonCls(self.ocr, self.controller)
        logger.info(f"目标副本: {self.target}")

        logger.info("初始化完成")

    def _capture(self):
        return self.screenshot.capture()

    def _identify(self, screenshot) -> PageState:
        # 结算页 OCR 优先
        if self.dungeon.is_settlement_page(screenshot):
            logger.debug("identify -> SETTLEMENT")
            return PageState.SETTLEMENT

        if self.home.detect(screenshot):
            logger.debug("identify -> HOME")
            return PageState.HOME

        if self.battle.detect(screenshot):
            logger.debug("identify -> IN_DUNGEON")
            return PageState.IN_DUNGEON

        if self.dungeon.is_confirm_page(screenshot):
            logger.debug("identify -> CONFIRM")
            return PageState.CONFIRM

        if self.dungeon_select.detect(screenshot):
            logger.debug("identify -> DUNGEON_SELECT")
            return PageState.DUNGEON_SELECT

        logger.debug("identify -> UNKNOWN")
        return PageState.UNKNOWN

    def _on_state_change(self, new_state: PageState):
        if new_state != PageState.UNKNOWN:
            self._unknown_count = 0
        if new_state != self.state:
            logger.info(f"状态切换: {self.state.name} → {new_state.name}")
            self.state = new_state

    def _handle_home(self, screenshot):
        logger.info("主城 → 前往副本")
        self.home.enter_dungeon(self.controller)
        self.dungeon.reset_scroll()
        time.sleep(2)

    def _handle_dungeon_select(self, screenshot):
        logger.info(f"副本选择 → 选择 {self.target}")
        ok = self.dungeon.select(screenshot)
        if ok:
            time.sleep(1.5)
        else:
            time.sleep(1.5)

    def _handle_confirm(self, screenshot):
        ok = self.dungeon.confirm(screenshot)
        if ok:
            self._loading_start = time.time()
            logger.info("确认进入，等待加载")
        else:
            logger.warning("确认按钮未找到，点击画面中央")
            self.controller.click(960, 800)
            self._loading_start = time.time()
        time.sleep(2)

    def _handle_loading(self):
        elapsed = time.time() - self._loading_start
        if elapsed > 30:
            logger.warning("加载超时（30s）")
        logger.info(f"加载中... ({elapsed:.0f}s)")

    def _handle_unknown(self, screenshot):
        self._unknown_count += 1
        if self._unknown_count >= self._max_unknown:
            logger.warning(f"连续未知 {self._unknown_count} 次，尝试恢复窗口")
            if self.screenshot.reload_window():
                logger.info("窗口重新定位成功")
            self._unknown_count = 0

    def _handle_battle(self, screenshot):
        logger.info("战斗开始")
        self.dungeon.battle()
        logger.info("战斗结束")

    def _handle_settlement(self, screenshot):
        self.run_count += 1
        elapsed = time.time() - self._start_time
        logger.info(f"🎉 第 {self.run_count} 次完成，已运行 {elapsed:.0f}s")

        if self.max_runs > 0 and self.run_count >= self.max_runs:
            logger.info(f"达到最大次数 {self.max_runs}，停止")
            return False

        ok = self.dungeon.settlement(screenshot)
        if not ok:
            logger.warning("结算按钮未找到，尝试点击画面中央")
            self.controller.click(960, 600)
            time.sleep(1)
            self.controller.click(960, 800)
        time.sleep(2)
        return True

    def run(self):
        logger.info("=" * 40)
        logger.info("sb-two-tops 启动")
        logger.info(f"目标副本: {self.target}")
        logger.info(f"最大次数: {'无限' if self.max_runs == 0 else self.max_runs}")
        logger.info("=" * 40)

        try:
            while True:
                screenshot = self._capture()
                if screenshot is None:
                    time.sleep(1)
                    continue

                state = self._identify(screenshot)
                self._on_state_change(state)

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
                    self._handle_unknown(screenshot)

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