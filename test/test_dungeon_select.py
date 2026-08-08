"""
测试：主城 → 进入副本 → 选择扼守 → 选难度

使用轮询重试替代固定等待，遇到状态变化立即继续，卡住才超时报错。

用法:
    python test/test_dungeon_select.py
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import Config
from src.core.screenshot import Screenshot
from src.core.recognizer import Recognizer
from src.core.clicker import MouseClicker
from src.core.keyboard import Keyboard
from src.core.ocr import OCR
from src.core.game_controller import GameController
from src.pages.home import HomePage
from src.pages.dungeon import DungeonSelectPage
from src.pages.esc_menu import EscMenuPage
from src.dungeons import get_dungeon


def _wait_until(ss, check_fn, timeout=10, interval=0.2):
    """轮询等待，直到 check_fn 返回 True 或超时"""
    start = time.time()
    while time.time() - start < timeout:
        img = ss.capture()
        if img is None:
            time.sleep(interval)
            continue
        if check_fn(img):
            return True, img
        time.sleep(interval)
    return False, None


def _dismiss_esc(ss, ocr, esc_menu, controller, max_retries=3):
    """如果在 ESC 菜单页，按 ESC 关闭"""
    for _ in range(max_retries):
        img = ss.capture()
        if img is None:
            return False
        if not esc_menu.detect_ocr(ocr, img):
            return True
        print("  \u26a0 ESC 菜单 -> 按 ESC 关闭")
        esc_menu.dismiss(controller)
        time.sleep(0.5)
    return False


def main():
    cfg = Config(str(PROJECT_ROOT / "config.json"))
    target = cfg.get("dungeon", "target", default="扼守")
    difficulty = cfg.get("dungeon", "difficulty", default="50级")

    # 模块
    ss = Screenshot(window_title=cfg.window_title, window_class=cfg.window_class)
    if not ss.find_window():
        print("FAIL 未找到游戏窗口")
        sys.exit(1)
    print("OK 找到窗口: " + cfg.window_title)

    recognizer = Recognizer()
    ocr = OCR()
    mouse = MouseClicker(hwnd=ss.hwnd)
    keyboard = Keyboard(hwnd=ss.hwnd)
    controller = GameController(mouse, keyboard)

    home = HomePage(recognizer, cfg.data)
    dungeon_page = DungeonSelectPage(recognizer, cfg.data)
    esc_menu = EscMenuPage(recognizer, cfg.data)

    DungeonCls = get_dungeon(target)
    dungeon = DungeonCls(ocr, controller)

    print("Target: " + target + " Difficulty: " + difficulty)
    print()

    # ── 第一步：识别当前页面，前往副本菜单 ──
    print("[1/3] 前往副本菜单...")

    # 先看当前是什么页面
    img = ss.capture()
    if img is None:
        print("FAIL 截图失败")
        sys.exit(1)

    if esc_menu.detect_ocr(ocr, img):
        print("  \u26a0 当前在 ESC 菜单 -> 关闭")
        _dismiss_esc(ss, ocr, esc_menu, controller)
        time.sleep(0.5)
        img = ss.capture()

    if home.detect(img):
        print("  OK 当前在主城 -> 按 L")
        controller.press_key("L", down_time=0.1)
        # 等进入副本页
        ok, _ = _wait_until(ss, lambda i: dungeon_page.detect(i), timeout=5)
        if not ok:
            # 可能弹了 ESC 菜单
            _dismiss_esc(ss, ocr, esc_menu, controller)
            print("  \u26a0 按 L 后未到副本页，再按一次")
            controller.press_key("L", down_time=0.1)
            ok, _ = _wait_until(ss, lambda i: dungeon_page.detect(i), timeout=5)
            if not ok:
                print("FAIL 无法进入副本选择页")
                sys.exit(1)
    elif dungeon_page.detect(img):
        print("  OK 已在副本选择页")
    else:
        print("  \u26a0 未知页面，尝试直接按 L")
        controller.press_key("L", down_time=0.1)
        ok, _ = _wait_until(ss, lambda i: dungeon_page.detect(i) or home.detect(i), timeout=5)
        if not ok:
            print("FAIL 无法确定当前页面状态")
            sys.exit(1)

    # ── 第二步：滚动找扼守 ──
    print("\n[2/3] 选择 " + target + " (自动滚动)...")

    found = False
    for attempt in range(1, 8):
        _dismiss_esc(ss, ocr, esc_menu, controller)

        print("  #" + str(attempt) + " ", end="", flush=True)
        ok, img = _wait_until(ss, lambda i: True, timeout=3)
        if not ok:
            continue

        result = ocr.find_text(img, target, min_score=0.3)
        if result:
            cx, cy, score = result
            print("OK 找到 " + target + " @ (" + str(cx) + ", " + str(cy) + ") score=" + str(round(score, 3)))
            controller.click(cx, cy)
            found = True
            break

        print("down", end="", flush=True)
        controller.scroll(-120, 384, 500)
        time.sleep(0.3)

    if not found:
        print("\nFAIL 未找到 " + target)
        sys.exit(1)

    # ── 第三步：选难度 ──
    print("\n[3/3] 选择难度 " + difficulty + "...")

    def check_difficulty(img):
        return dungeon.select_difficulty(img)

    ok, _ = _wait_until(ss, check_difficulty, timeout=5)
    if ok:
        print("  OK 点击难度 " + difficulty)
    else:
        print("  \u26a0 未找到 " + difficulty + " (可能不在难度选择页)")

    # ── 停下 ──
    print()
    print("=" * 50)
    print("OK 流程完成!")
    print("已选择: " + target + " - " + difficulty)
    print("确认后告诉我后续逻辑")
    print("=" * 50)


if __name__ == "__main__":
    main()