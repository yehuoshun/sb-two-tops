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
from src.core.ocr import OCR
from src.pages.home import HomePage
from src.pages.dungeon import DungeonSelectPage, ConfirmPage
from src.pages.battle import BattlePage, SettlementPage

logger = logging.getLogger("sb-two-tops.main")


class PageState(Enum):
    UNKNOWN = auto()
    HOME = auto()
    DUNGEON_SELECT = auto()
    CONFIRM = auto()
    LOADING = auto()
    IN_DUNGEON = auto()
    SETTLEMENT = auto()


VK_Q = 0x51


class SBAuto:
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self._init_logging()
        self._init_modules()
        self.state = PageState.UNKNOWN
        self.run_count = 0
        self.max_runs = self.config.get("dungeon", "max_runs", default=0)
        self.targets = self.config.get("dungeon", "targets", default=["探险"])
        self._start_time = time.time()
        self._loading_start = 0
        self._dungeon_start = 0
        self._unknown_count = 0  # 连续未知状态计数
        self._max_unknown = 10   # 连续未知超过此值则尝试恢复

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
        return img

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

    def _on_state_change(self, new_state: PageState):
        """状态切换回调 — 重置卡死计数器"""
        if new_state != PageState.UNKNOWN:
            self._unknown_count = 0
        if new_state != self.state:
            logger.info(f"状态切换: {self.state.name} → {new_state.name}")
            self.state = new_state

    def _handle_home(self, screenshot):
        logger.info("主城 — 前往副本")
        self.home.enter_dungeon(self.clicker)
        time.sleep(2)

    def _handle_dungeon_select(self, screenshot):
        logger.info(f"副本选择 — 尝试 {len(self.targets)} 个目标")
        ok = self.dungeon_select.select_dungeon(self.ocr, self.clicker, screenshot, self.targets)
        if not ok:
            # 需要滚动后重试，等主循环下次截图
            time.sleep(1.5)

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

    def _handle_unknown(self, screenshot):
        """未知状态处理 — 连续未知超过阈值则尝试恢复"""
        self._unknown_count += 1
        if self._unknown_count >= self._max_unknown:
            logger.warning(f"连续未知 {self._unknown_count} 次，尝试恢复窗口")
            if self.screenshot.reload_window():
                logger.info("窗口重新定位成功")
            else:
                logger.error("无法找到游戏窗口，等待重试")
            self._unknown_count = 0

    def _handle_battle(self, screenshot):
        if self._dungeon_start == 0:
            self._dungeon_start = time.time()
        # 按 Q 大招
        self.clicker.press_key(VK_Q)
        elapsed = time.time() - self._dungeon_start
        logger.info(f"战斗中... ({elapsed:.0f}s) 释放大招 Q")
        time.sleep(2)

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

    def run(self):
        logger.info("=" * 40)
        logger.info("sb-two-tops 启动")
        logger.info(f"目标副本: {', '.join(self.targets)}")
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
        # noinspection PyBroadException
        except Exception:
            logger.exception("运行时异常")
        finally:
            elapsed = time.time() - self._start_time
            logger.info(f"运行结束 — 共 {self.run_count} 次，耗时 {elapsed:.0f}s")


if __name__ == "__main__":
    auto = SBAuto()
    auto.run()