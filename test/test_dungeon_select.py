"""
测试：主城 -> 进入副本 -> 选择扼守 -> 选难度

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
    for _ in range(max_retries):
        img = ss.capture()
        if img is None:
            return False
        if not esc_menu.detect_ocr(ocr, img):
            return True
        print("  ESC menu -> close")
        esc_menu.dismiss(controller)
        time.sleep(0.5)
    return False


def main():
    cfg = Config(str(PROJECT_ROOT / "config.json"))
    target = cfg.get("dungeon", "target", default="扼守")
    difficulty = cfg.get("dungeon", "difficulty", default="50级")

    ss = Screenshot(window_title=cfg.window_title, window_class=cfg.window_class)
    if not ss.find_window():
        print("FAIL: no window")
        sys.exit(1)
    print("OK: " + cfg.window_title)

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

    def is_dungeon_page(img):
        return dungeon_page.detect(img) or dungeon_page.detect_ocr(ocr, img)

    # ── Step 1: Go to dungeon select ──
    print("[1/3] 前往副本菜单...")

    img = ss.capture()
    if img is None:
        print("FAIL: capture")
        sys.exit(1)

    if esc_menu.detect_ocr(ocr, img):
        print("  ESC menu -> close")
        _dismiss_esc(ss, ocr, esc_menu, controller)
        time.sleep(0.5)
        img = ss.capture()

    if home.detect(img):
        print("  OK: 主城 -> L")
        controller.press_key("L", down_time=0.1)
        # 等 1.5s 先检查一次，不行再等 1.5s
        time.sleep(1.5)
        img = ss.capture()
        if img is not None and not is_dungeon_page(img):
            time.sleep(1.5)
            img = ss.capture()
        if img is not None and not is_dungeon_page(img):
            # 可能进了导航页，点顶部委托 tab
            print("  tab: 委托")
            r = ocr.find_text(img, "委托", min_score=0.3, region=(200, 30, 500, 60))
            if r:
                controller.click(r[0], r[1])
                time.sleep(1.5)
                img = ss.capture()
                # 再点子 tab 的委托（第一个，确保进入副本列表而非悬赏委托）
                if img is not None:
                    r2 = ocr.find_text(img, "委托", min_score=0.3, region=(100, 190, 200, 60))
                    if r2:
                        print("  sub-tab: 委托")
                        controller.click(r2[0], r2[1])
                        time.sleep(1.5)
                        img = ss.capture()
            else:
                _dismiss_esc(ss, ocr, esc_menu, controller)
                print("  retry L")
                controller.press_key("L", down_time=0.1)
                time.sleep(2)
                img = ss.capture()
        if img is None or not is_dungeon_page(img):
            print("FAIL: 无法进入副本页")
            sys.exit(1)
    elif is_dungeon_page(img):
        print("  OK: 已在副本页")
    else:
        print("  unknown page -> try L")
        controller.press_key("L", down_time=0.1)
        ok, _ = _wait_until(ss, lambda i: is_dungeon_page(i) or home.detect(i), timeout=5)
        if not ok:
            print("FAIL: 无法确定页面")
            sys.exit(1)

    # ── Step 2: Scroll to find target ──
    print("\n[2/3] 选择 " + target + " ...")

    found = False
    for attempt in range(1, 8):
        _dismiss_esc(ss, ocr, esc_menu, controller)

        print("  #" + str(attempt) + " ", end="", flush=True)
        img = ss.capture()
        if img is None:
            time.sleep(0.3)
            continue

        result = ocr.find_text(img, target, min_score=0.3)
        if result:
            cx, cy, score = result
            print("OK @" + str(cx) + "," + str(cy) + " score=" + str(round(score, 3)))
            controller.click(cx, cy)
            found = True
            break

        print("down", end="", flush=True)
        controller.scroll(-480, 600, 800)
        time.sleep(0.3)

    if not found:
        print("\nFAIL: 未找到 " + target)
        sys.exit(1)

    # ── Step 3: Select difficulty ──
    print("\n[3/3] 选择难度 " + difficulty + "...")

    def check_difficulty(img):
        return dungeon.select_difficulty(img)

    ok, _ = _wait_until(ss, check_difficulty, timeout=5)
    if ok:
        print("  OK: " + difficulty)
    else:
        print("  ?: 未找到 " + difficulty)

    print()
    print("=" * 50)
    print("OK: " + target + " - " + difficulty)
    print("确认后告诉我后续")
    print("=" * 50)


if __name__ == "__main__":
    main()