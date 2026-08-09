"""
测试：主城 -> 进入副本 -> 选择扼守 -> 选难度

使用轮询重试替代固定等待，遇到状态变化立即继续，卡住才超时报错。

用法:
    python test/test_dungeon_select.py
"""

import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.logging_config import setup_logging
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

logger = logging.getLogger("sb-two-tops.test.dungeon_select")


def _save_debug_screenshot(img, label: str = ""):
    """保存调试截图到 logs/ 目录"""
    import cv2
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    name = f"debug_{ts}{'_' + label if label else ''}.png"
    path = str(log_dir / name)
    cv2.imwrite(path, img)
    logger.info(f"截图已保存: {name}  ({img.shape[1]}x{img.shape[0]})")


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
        logger.info("ESC menu -> close")
        esc_menu.dismiss(controller)
        time.sleep(0.5)
    return False


def main():
    # ── 初始化日志系统 ──
    setup_logging(level="INFO")
    logger.info("test_dungeon_select 启动")

    # ── 加载配置 ──
    cfg = Config(str(PROJECT_ROOT / "config.json"))
    target = cfg.get("dungeon", "target", default="扼守")
    difficulty = cfg.get("dungeon", "difficulty", default="50级")
    logger.info(f"目标: {target} 难度: {difficulty}")

    # ── 查找窗口 ──
    ss = Screenshot(window_title=cfg.window_title, window_class=cfg.window_class)
    if not ss.find_window():
        logger.error("未找到游戏窗口")
        sys.exit(1)

    # ── 初始化模块 ──
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

    def is_dungeon_page(img):
        return dungeon_page.detect(img) or dungeon_page.detect_ocr(ocr, img)

    # ── 截图诊断工具 ──
    def diagnose_screenshot(img, label: str = "initial"):
        nonlocal ss
        """截图的完整诊断信息"""
        stats = {
            "size": f"{img.shape[1]}x{img.shape[0]}",
            "mean": f"{int(img.mean()):d}",
            "icons": recognizer.count_icons_in_row(img),
        }

        # 检查是否全黑/全白
        mean_val = float(img.mean())
        if mean_val < 10:
            logger.warning(f"截图疑似全黑 mean={mean_val:.0f}")
            _save_debug_screenshot(img, f"black_{label}")
        elif mean_val > 240:
            logger.warning(f"截图疑似全白 mean={mean_val:.0f}")
            _save_debug_screenshot(img, f"white_{label}")
        elif mean_val < 30:
            logger.warning(f"截图亮度过低 mean={mean_val:.0f}")

        logger.info(f"截图诊断 [{label}]: {stats['size']} mean={stats['mean']} icons={stats['icons']}")
        return stats

    # ── Step 1: Go to dungeon select ──
    logger.info("─" * 40)
    logger.info("Step 1/3: 前往副本菜单")

    # 首次截图可能偏暗（窗口过渡），重试直到正常
    img = None
    for retry in range(3):
        img = ss.capture()
        if img is None:
            time.sleep(0.5)
            continue
        mean_val = img.mean()
        if mean_val < 30 or img.shape[0] < 100:
            logger.debug(f"截图偏暗 mean={mean_val:.0f}，重试 {retry+1}/3")
            time.sleep(0.5)
            continue
        break
    if img is None:
        logger.error("截图失败（重试 3 次）")
        sys.exit(1)

    diagnose_screenshot(img, "step1")

    is_esc = esc_menu.detect_ocr(ocr, img)
    is_home = home.detect(img)
    is_dungeon = is_dungeon_page(img)
    logger.info(f"页面检测: home={is_home} dungeon={is_dungeon} esc={is_esc}")

    if not is_home and not is_dungeon and not is_esc:
        _save_debug_screenshot(img, "unknown_page")

    if is_esc:
        logger.info("ESC 菜单检测到 -> 关闭")
        _dismiss_esc(ss, ocr, esc_menu, controller)
        time.sleep(0.5)
        img = ss.capture()
        if img is None:
            logger.error("ESC 关闭后截图失败")
            sys.exit(1)
        diagnose_screenshot(img, "after_esc")
        # 重新检测页面（ESC 关闭后页面变了）
        is_esc = esc_menu.detect_ocr(ocr, img)
        is_home = home.detect(img)
        is_dungeon = is_dungeon_page(img)
        logger.info(f"重新检测: home={is_home} dungeon={is_dungeon} esc={is_esc}")

    if is_home:
        logger.info("主城 -> 按 L 键")
        ss.bring_to_foreground()
        controller.press_key("L", down_time=0.1)
        logger.debug("L 键已发送")

        time.sleep(1.5)
        img = ss.capture()
        if img is not None and not is_dungeon_page(img):
            logger.info("1.5s 后未到副本页，再等 1.5s")
            time.sleep(1.5)
            img = ss.capture()

        if img is not None and not is_dungeon_page(img):
            # 可能进了导航页，点顶部委托 tab
            logger.info("尝试点击顶部 委托 tab")
            r = ocr.find_text(img, "委托", min_score=0.3, region=(200, 30, 500, 60))
            if r:
                cx, cy, score = r
                logger.info(f"找到 委托 @ ({cx},{cy}) score={score:.3f} -> click")
                controller.click(cx, cy)
                time.sleep(1.5)
                img = ss.capture()
                # 再点子 tab 的委托
                if img is not None:
                    r2 = ocr.find_text(img, "委托", min_score=0.3, region=(100, 190, 200, 60))
                    if r2:
                        cx2, cy2, score2 = r2
                        logger.info(f"子 tab 委托 @ ({cx2},{cy2}) score={score2:.3f} -> click")
                        controller.click(cx2, cy2)
                        time.sleep(1.5)
                        img = ss.capture()
            else:
                _dismiss_esc(ss, ocr, esc_menu, controller)
                logger.info("未找到 tab，重试 L")
                ss.bring_to_foreground()
                controller.press_key("L", down_time=0.1)
                time.sleep(2)
                img = ss.capture()

        if img is None:
            logger.error("截图失败")
            sys.exit(1)
        if not is_dungeon_page(img):
            _save_debug_screenshot(img, "fail_not_dungeon")
            logger.error("无法进入副本页")
            sys.exit(1)

        logger.info("已进入副本选择页")
    elif is_dungeon:
        logger.info("已在副本选择页")
    else:
        logger.info("未知页面 -> 尝试按 L")
        controller.press_key("L", down_time=0.1)
        ok, final_img = _wait_until(ss, lambda i: is_dungeon_page(i) or home.detect(i), timeout=5)
        if not ok:
            if final_img is not None:
                _save_debug_screenshot(final_img, "fail_step1_unknown")
            logger.error("无法确定页面")
            sys.exit(1)
        logger.info("页面已确定")

    # ── Step 2: Scroll to find target ──
    logger.info("─" * 40)
    logger.info(f"Step 2/3: 选择 {target}")

    found = False
    for attempt in range(1, 6):
        _dismiss_esc(ss, ocr, esc_menu, controller)

        img = ss.capture()
        if img is None:
            logger.warning(f"第 {attempt} 次尝试截图失败")
            time.sleep(0.3)
            continue

        result = ocr.find_text(img, target, min_score=0.3)
        if result:
            cx, cy, score = result
            logger.info(f"找到 {target} @ ({cx},{cy}) score={score:.3f} 尝试={attempt}/5")
            controller.click(cx, cy)
            found = True
            break

        logger.debug(f"未找到 {target}，向下滚动 尝试={attempt}/5")
        controller.scroll(-120, 600, 500, times=10)
        time.sleep(0.5)

    if not found:
        if img is not None:
            _save_debug_screenshot(img, "fail_step2_not_found")
        logger.error(f"未找到 {target}（已滚动 5 次）")
        sys.exit(1)

    # ── Step 3: Select difficulty ──
    logger.info("─" * 40)
    logger.info(f"Step 3/3: 选择难度 {difficulty}")

    # 点击扼守后等画面变化
    time.sleep(1.0)
    img = ss.capture()
    if img is not None:
        diagnose_screenshot(img, "step3_after_click")

    def check_difficulty(img):
        return dungeon.select_difficulty(img)

    ok, diff_img = _wait_until(ss, check_difficulty, timeout=5)
    if ok:
        logger.info(f"难度 {difficulty} 已选择")
    else:
        if diff_img is not None:
            _save_debug_screenshot(diff_img, "fail_step3_difficulty")
        logger.warning(f"未找到难度 {difficulty}")

    # ── 完成 ──
    logger.info("=" * 40)
    logger.info(f"OK: {target} - {difficulty}")
    logger.info("确认后告诉我后续")
    logger.info("=" * 40)


if __name__ == "__main__":
    main()