"""
测试：主城 → 进入副本 → 选择扼守 → 选难度

验证流程：
1. 检测主城 → 按 L 进入副本菜单
2. 检测副本选择页 → 滚动找扼守 → 点击
3. 检测难度选择页 → 选指定难度 → 停下让你看结果

支持自动关闭 ESC 菜单（误触 ESC 时的恢复）。

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


def _dismiss_esc(ss, ocr, esc_menu, controller, max_retries=3):
    """如果在 ESC 菜单页，按 ESC 关闭"""
    for _ in range(max_retries):
        img = ss.capture()
        if img is None:
            return False
        if not esc_menu.detect_ocr(ocr, img):
            return True  # 不在 ESC 菜单了
        print("⚠️ 检测到 ESC 菜单 → 按 ESC 关闭")
        esc_menu.dismiss(controller)
        time.sleep(1)
    return False


def main():
    cfg = Config(str(PROJECT_ROOT / "config.json"))
    target = cfg.get("dungeon", "target", default="扼守")
    difficulty = cfg.get("dungeon", "difficulty", default="50级")

    # 截图
    ss = Screenshot(window_title=cfg.window_title, window_class=cfg.window_class)
    if not ss.find_window():
        print("❌ 未找到游戏窗口")
        sys.exit(1)
    print(f"✅ 找到窗口: {cfg.window_title}")

    # 模块
    recognizer = Recognizer()
    ocr = OCR()
    mouse = MouseClicker(hwnd=ss.hwnd, post_click_wait_ms=cfg.post_click_wait_ms)
    keyboard = Keyboard(hwnd=ss.hwnd, post_click_wait_ms=cfg.post_click_wait_ms)
    controller = GameController(mouse, keyboard)

    # 页面
    home = HomePage(recognizer, cfg.data)
    dungeon_page = DungeonSelectPage(recognizer, cfg.data)
    esc_menu = EscMenuPage(recognizer, cfg.data)

    # 副本
    DungeonCls = get_dungeon(target)
    dungeon = DungeonCls(ocr, controller)

    print(f"🎯 目标: {target} 难度: {difficulty}")
    print()

    # ── 第一步：检测主城，按 L 进入副本 ──
    print("【1/4】检测主城...")

    # 先检查是否在 ESC 菜单
    img = ss.capture()
    if img is None:
        print("❌ 截图失败")
        sys.exit(1)
    if esc_menu.detect_ocr(ocr, img):
        print("⚠️ 检测到 ESC 菜单，关闭...")
        esc_menu.dismiss(controller)
        time.sleep(1)
        img = ss.capture()

    if home.detect(img):
        print("✅ 当前在主城 → 按 L 进入副本菜单")
        home.enter_dungeon(controller)
        time.sleep(3)

        # 按 L 后可能弹出 ESC 菜单（如果 L 键映射冲突）
        if not _dismiss_esc(ss, ocr, esc_menu, controller):
            pass  # 没有 ESC 菜单最好
    else:
        print("⚠️ 不在主城，跳过（可能已在副本选择页）")

    # ── 第二步：检测副本选择页 ──
    print("\n【2/4】检测副本选择页...")

    # 再次检查 ESC 菜单
    _dismiss_esc(ss, ocr, esc_menu, controller)

    img = ss.capture()
    if img is None:
        print("❌ 截图失败")
        sys.exit(1)

    if dungeon_page.detect(img):
        print("✅ 当前在副本选择页")
    else:
        print("⚠️ 图标行数不符，继续尝试选本...")

    # ── 第三步：选择扼守（自动滚动） ──
    print(f"\n【3/4】选择 {target}（自动滚动）...")
    max_attempts = 6
    for attempt in range(1, max_attempts + 1):
        # 每次截图前检查 ESC 菜单
        _dismiss_esc(ss, ocr, esc_menu, controller)

        img = ss.capture()
        if img is None:
            continue

        print(f"   第 {attempt}/{max_attempts} 次尝试...", end=" ")
        ok = dungeon.select(img)
        if ok:
            print(f"✅ 点击 {target} 成功！")
            break
        print("滚动中...")
        time.sleep(0.5)
    else:
        print(f"\n❌ 滚动 {max_attempts} 次未找到 {target}")
        sys.exit(1)

    time.sleep(2)

    # ── 第四步：选难度 ──
    print(f"\n【4/4】选择难度 {difficulty}...")
    _dismiss_esc(ss, ocr, esc_menu, controller)

    img = ss.capture()
    if img is None:
        print("❌ 截图失败")
        sys.exit(1)

    ok = dungeon.select_difficulty(img)
    if ok:
        print(f"✅ 点击难度 {difficulty} 成功！")
    else:
        print(f"⚠️ 未找到 {difficulty}，可能不在难度选择页")

    # ── 停下 ──
    print()
    print("=" * 50)
    print("✅ 流程完成！")
    print(f"已选择 \"{target}\" — \"{difficulty}\"，请观察画面是否正确。")
    print("确认后告诉我后续逻辑，我继续写。")
    print("=" * 50)


if __name__ == "__main__":
    main()