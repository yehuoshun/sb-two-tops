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
        self._battle_start = 0.0

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

    def _wait_until(self, check_fn, timeout=10, interval=0.3):
        """轮询截图直到条件满足，返回 (ok, last_screenshot)"""
        start = time.time()
        while time.time() - start < timeout:
            img = self._capture()
            if img is None:
                time.sleep(interval)
                continue
            if check_fn(img):
                return True, img
            time.sleep(interval)
        return False, self._capture()

    # ── 页面检测 ──

    def _identify(self, screenshot) -> PageState:
        # 结算页 OCR 优先（最独特，容易误判为其他页）
        if self.dungeon.is_settlement_page(screenshot):
            logger.debug("identify -> SETTLEMENT")
            return PageState.SETTLEMENT

        # 确认页 OCR（"开始挑战" 只在确认页出现）
        if self.dungeon.is_confirm_page(screenshot):
            logger.debug("identify -> CONFIRM")
            return PageState.CONFIRM

        # 副本选择页 OCR（"委托" tab 文字）
        if self.dungeon_select.detect_ocr(self.ocr, screenshot):
            logger.debug("identify -> DUNGEON_SELECT")
            return PageState.DUNGEON_SELECT

        # 战斗页 OCR（"当前轮次" 等战斗文字）
        if self.dungeon.is_battle_page(screenshot):
            logger.debug("identify -> IN_DUNGEON")
            return PageState.IN_DUNGEON

        # 主城（图标计数，放最后避免误判菜单页）
        if self.home.detect(screenshot):
            logger.debug("identify -> HOME")
            return PageState.HOME

        # 画面偏暗 → 可能加载中
        if screenshot is not None and screenshot.mean() < 30:
            logger.debug("identify -> LOADING (dark)")
            return PageState.LOADING

        logger.debug("identify -> UNKNOWN")
        return PageState.UNKNOWN

    def _on_state_change(self, new_state: PageState):
        if new_state != PageState.UNKNOWN:
            self._unknown_count = 0
        if new_state != self.state:
            # 退出战斗状态时重置战斗计时
            if self.state == PageState.IN_DUNGEON:
                self._battle_start = 0.0
            logger.info(f"状态切换: {self.state.name} → {new_state.name}")
            self.state = new_state

    # ── 各状态处理 ──

    def _handle_home(self, screenshot):
        logger.info("主城 → 前往副本")
        self.home.enter_dungeon(self.controller)
        self.dungeon.reset_scroll()

        # 等待副本页出现（最多 5s）
        ok, img = self._wait_until(
            lambda i: self.dungeon_select.detect_ocr(self.ocr, i),
            timeout=5, interval=0.3,
        )
        if ok:
            logger.info("已进入副本选择页")
        else:
            logger.warning("按L后未检测到副本页，可能仍需等待")

    def _handle_dungeon_select(self, screenshot):
        logger.info(f"副本选择 → 选择 [{self.target}]")
        ok = self.dungeon.select(screenshot)
        if ok:
            # 点击扼守后等确认页出现
            logger.info(f"[{self.target}] 已点击，等待确认页")
            ok, _ = self._wait_until(
                lambda i: self.dungeon.is_confirm_page(i),
                timeout=5, interval=0.3,
            )
            if ok:
                logger.info("确认页已出现")
                # 选难度
                self.dungeon.select_difficulty(screenshot)
                time.sleep(0.5)
            else:
                logger.warning("点击扼守后未检测到确认页，继续")
        else:
            # 没找到，下一轮继续滚动
            time.sleep(0.5)

    def _handle_confirm(self, screenshot):
        ok = self.dungeon.confirm(screenshot)
        if ok:
            self._loading_start = time.time()
            logger.info("确认进入，等待加载")
            # 等待画面变化（不再是确认页）
            ok, _ = self._wait_until(
                lambda i: not self.dungeon.is_confirm_page(i),
                timeout=5, interval=0.3,
            )
            if ok:
                logger.info("确认页已消失，进入加载/战斗")
            else:
                logger.warning("确认页未消失，可能没点到")
        else:
            logger.warning("确认按钮未找到，点击画面中央")
            self.controller.click(960, 800)
            self._loading_start = time.time()

    def _handle_loading(self):
        elapsed = time.time() - self._loading_start
        if elapsed > 30:
            logger.warning("加载超时（30s）")
        logger.info(f"加载中... ({elapsed:.0f}s)")

    def _handle_unknown(self, screenshot):
        # 画面偏暗 → 正在加载，不计数
        if screenshot is not None and screenshot.mean() < 30:
            logger.debug("画面偏暗，可能正在加载")
            time.sleep(1)
            return

        self._unknown_count += 1
        if self._unknown_count >= self._max_unknown:
            logger.warning(f"连续未知 {self._unknown_count} 次，尝试恢复窗口")
            if self.screenshot.reload_window():
                logger.info("窗口重新定位成功")
            self._unknown_count = 0

    def _handle_battle(self, screenshot):
        # 检查结算页（战斗结束信号）
        if self.dungeon.is_settlement_page(screenshot):
            logger.info("战斗结束，检测到结算页")
            self._battle_start = 0.0
            return

        # 首次进入战斗
        if self._battle_start == 0.0:
            self._battle_start = time.time()
            logger.info("战斗开始")
            return

        # 战斗循环单次迭代
        elapsed = time.time() - self._battle_start
        self.dungeon.battle_tick(elapsed)

    def _handle_settlement(self, screenshot):
        self.run_count += 1
        elapsed = time.time() - self._start_time
        logger.info(f"🎉 第 {self.run_count} 次完成，已运行 {elapsed:.0f}s")

        if self.max_runs > 0 and self.run_count >= self.max_runs:
            logger.info(f"达到最大次数 {self.max_runs}，停止")
            return False

        ok = self.dungeon.settlement(screenshot)
        if ok:
            logger.info("结算按钮已点击")
            # 等待页面变化（不再是结算页）
            ok, _ = self._wait_until(
                lambda i: not self.dungeon.is_settlement_page(i),
                timeout=5, interval=0.3,
            )
            if ok:
                logger.info("结算页已消失")
            else:
                logger.warning("结算页未消失，可能没点到")
        else:
            logger.warning("结算按钮未找到，尝试点击画面中央")
            self.controller.click(960, 600)
            time.sleep(1)
            self.controller.click(960, 800)
        return True

    # ── 主循环 ──

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