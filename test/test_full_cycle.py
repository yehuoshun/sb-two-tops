"""
测试全自动循环：主城→选扼守→确认→战斗→结算→下一轮

逐步执行，每步截图+日志，卡住也报错不崩溃。

用法:
    python test/test_full_cycle.py
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
from src.pages.battle import BattlePage, SettlementPage
from src.dungeons import get_dungeon

logger = logging.getLogger("sb-two-tops.test.full_cycle")


def _save_debug_screenshot(img, label: str = ""):
    """保存调试截图到 logs/ 目录"""
    import cv2
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    name = f"cycle_{ts}{'_' + label if label else ''}.png"
    path = str(log_dir / name)
    cv2.imwrite(path, img)
    logger.info(f"截图已保存: {name}  ({img.shape[1]}x{img.shape[0]})")


def _wait_until(ss, check_fn, timeout=10, interval=0.2):
    start = time.time()
    last_img = None
    while time.time() - start < timeout:
        img = ss.capture()
        if img is None:
            time.sleep(interval)
            continue
        last_img = img
        if check_fn(img):
            return True, img
        time.sleep(interval)
    return False, last_img


def _diagnose_screenshot(recognizer, img, label: str = "diag"):
    if img is None:
        return {"size": "N/A", "mean": "N/A"}
    stats = {
        "size": f"{img.shape[1]}x{img.shape[0]}",
        "mean": f"{int(img.mean()):d}",
        "icons": recognizer.count_icons_in_row(img),
    }
    mean_val = float(img.mean())
    if mean_val < 10:
        _save_debug_screenshot(img, f"black_{label}")
    elif mean_val > 240:
        _save_debug_screenshot(img, f"white_{label}")
    return stats


def main():
    setup_logging(level="INFO")
    logger.info("=" * 50)
    logger.info("test_full_cycle 启动 — 全自动循环测试")
    logger.info("=" * 50)

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

    # ── 辅助函数 ──

    def is_dungeon_page(img):
        return dungeon_page.detect(img) or dungeon_page.detect_ocr(ocr, img)

    def is_confirm_page(img):
        return dungeon.is_confirm_page(img)

    def is_battle_page(img):
        return dungeon.is_battle_page(img)

    def is_settlement_page(img):
        return dungeon.is_settlement_page(img)

    def is_home_page(img):
        return home.detect(img)

    def get_page_label(img):
        if is_settlement_page(img):
            return "SETTLEMENT"
        if is_confirm_page(img):
            return "CONFIRM"
        if is_dungeon_page(img):
            return "DUNGEON_SELECT"
        if is_battle_page(img):
            return "BATTLE"
        if is_home_page(img):
            return "HOME"
        if img is not None and img.mean() < 30:
            return "LOADING(DARK)"
        return "UNKNOWN"

    # ══════════════════════════════════════════
    # Step 1: 确保在副本选择页
    # ══════════════════════════════════════════
    logger.info("─" * 50)
    logger.info("Step 1/6: 确保在副本选择页")

    # 首次截图，重试直到正常
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

    _diagnose_screenshot(recognizer, img, "step1")
    page = get_page_label(img)
    logger.info(f"当前页面: {page}")

    if page == "DUNGEON_SELECT":
        logger.info("已在副本选择页")
    elif is_home_page(img):
        logger.info("主城 → 按 L 进入副本菜单")
        ss.bring_to_foreground()
        controller.press_key("L", down_time=0.1)
        ok, img = _wait_until(ss, is_dungeon_page, timeout=5)
        if not ok:
            _save_debug_screenshot(img, "step1_fail_not_dungeon")
            logger.error("无法进入副本选择页")
            sys.exit(1)
        logger.info("已进入副本选择页")
    elif page == "CONFIRM":
        logger.info("已在确认页，跳过选择步骤")
    elif page == "BATTLE":
        logger.info("已在战斗中，跳过选择步骤")
    else:
        # 未知页面，试按 L
        logger.info(f"未知页面 ({page})，尝试按 L")
        ss.bring_to_foreground()
        controller.press_key("L", down_time=0.1)
        ok, img = _wait_until(ss, lambda i: is_dungeon_page(i) or is_home_page(i), timeout=5)
        if not ok:
            _save_debug_screenshot(img, "step1_fail_unknown")
            logger.error("无法确定页面")
            sys.exit(1)
        logger.info(f"页面已确定: {get_page_label(img)}")

    # ══════════════════════════════════════════
    # Step 2: 选择副本 (扼守)
    # ══════════════════════════════════════════
    logger.info("─" * 50)
    logger.info(f"Step 2/6: 选择副本 [{target}]")

    # 确保在副本选择页（用 _wait_until 重试，防止页面跳变）
    ok, img = _wait_until(ss, lambda i: is_dungeon_page(i) or is_confirm_page(i), timeout=10)
    if not ok:
        # 可能回了主城，尝试再按 L
        logger.warning("未检测到副本页/确认页，尝试重新按 L")
        ss.bring_to_foreground()
        controller.press_key("L", down_time=0.1)
        ok, img = _wait_until(ss, is_dungeon_page, timeout=10)
        if not ok:
            _save_debug_screenshot(img, "step2_fail_not_dungeon")
            logger.error("无法进入副本选择页")
            sys.exit(1)

    page = get_page_label(img)
    logger.info(f"当前页面: {page}")

    if page == "DUNGEON_SELECT":
        found = False
        for attempt in range(1, dungeon.max_scroll + 1):
            img = ss.capture()
            if img is None:
                time.sleep(0.3)
                continue

            result = ocr.find_text(img, target, min_score=0.3)
            if result:
                cx, cy, score = result
                logger.info(f"找到 [{target}] @ ({cx},{cy}) score={score:.3f} 尝试={attempt}/{dungeon.max_scroll}")
                controller.click(cx, cy)
                found = True
                break

            logger.debug(f"未找到 [{target}]，向下滚动 尝试={attempt}/{dungeon.max_scroll}")
            controller.scroll(-120, 600, 500, times=10)
            time.sleep(0.5)
            _save_debug_screenshot(ss.capture(), f"step2_scroll_{attempt}")

        if not found:
            _save_debug_screenshot(img, "step2_fail_not_found")
            logger.error(f"未找到 [{target}]（已滚动 {dungeon.max_scroll} 次）")
            dump = ocr.read(img)
            logger.info(f"画面 OCR 结果 ({len(dump)} 条):")
            for text, cx, cy, score in dump[:30]:
                logger.info(f"  \"{text}\" @ ({cx},{cy}) score={score:.3f}")
            if len(dump) > 30:
                logger.info(f"  ... 还有 {len(dump)-30} 条")
            sys.exit(1)

        # 点击扼守后等确认页出现
        logger.info(f"[{target}] 已点击，等待确认页")
        ok, confirm_img = _wait_until(ss, is_confirm_page, timeout=15, interval=0.3)
        if ok:
            logger.info("确认页已出现")
            _diagnose_screenshot(recognizer, confirm_img, "step2_after_click")
            # 选难度
            logger.info(f"Step 2b: 选择难度 [{difficulty}]")
            time.sleep(0.5)

            def check_difficulty(img):
                return dungeon.select_difficulty(img)

            ok2, diff_img = _wait_until(ss, check_difficulty, timeout=5)
            if ok2:
                time.sleep(0.5)
                logger.info(f"难度 [{difficulty}] 已选择")
            else:
                if diff_img is not None:
                    _save_debug_screenshot(diff_img, "step2b_fail_difficulty")
                    dump = ocr.read(diff_img)
                    logger.info(f"难度选择后 OCR ({len(dump)} 条):")
                    for text, cx, cy, score in dump[:20]:
                        logger.info(f"  \"{text}\" @ ({cx},{cy}) score={score:.3f}")
                logger.warning(f"未找到难度 [{difficulty}]，可能已选中")
        else:
            logger.warning("点击扼守后未检测到确认页")
            # 诊断：看点击后画面是什么
            diag_img = ss.capture()
            if diag_img is not None:
                _save_debug_screenshot(diag_img, "step2_after_click_no_confirm")
                diag_page = get_page_label(diag_img)
                logger.info(f"点击后页面: {diag_page}")
                dump = ocr.read(diag_img)
                logger.info(f"点击后 OCR ({len(dump)} 条):")
                for text, cx, cy, score in dump[:30]:
                    logger.info(f"  \"{text}\" @ ({cx},{cy}) score={score:.3f}")
                if len(dump) > 30:
                    logger.info(f"  ... 还有 {len(dump)-30} 条")
            else:
                logger.error("点击后截图失败")
            sys.exit(1)

    elif page == "CONFIRM":
        logger.info("已在确认页，跳过选择步骤")
    elif page == "BATTLE":
        logger.info("已在战斗中，跳过选择步骤")
    else:
        logger.warning(f"非预期页面: {page}，尝试继续")

    # ══════════════════════════════════════════
    # Step 3: 点击"开始挑战"确认进入
    # ══════════════════════════════════════════
    logger.info("─" * 50)
    logger.info("Step 3/6: 确认进入 — 点击[开始挑战]")

    img = ss.capture()
    if img is not None:
        _diagnose_screenshot(recognizer, img, "step3_before_confirm")
    page = get_page_label(img)
    logger.info(f"当前页面: {page}")

    if page == "CONFIRM":
        ok, _ = _wait_until(ss, is_confirm_page, timeout=10)
        if ok:
            clicked = dungeon.confirm(img)
            if clicked:
                logger.info("✅ [开始挑战] 已点击")
                time.sleep(1)
                # 保存点击后的截图
                after = ss.capture()
                if after is not None:
                    _save_debug_screenshot(after, "step3_after_confirm")
                    page = get_page_label(after)
                    logger.info(f"点击后页面: {page}")
            else:
                logger.error("confirm() 返回 False")
                _save_debug_screenshot(img, "step3_fail_confirm")
                sys.exit(1)
        else:
            logger.error("确认页超时未出现")
            _save_debug_screenshot(img, "step3_fail_timeout")
            sys.exit(1)
    elif page == "BATTLE":
        logger.info("已在战斗中，跳过确认步骤")
    else:
        logger.warning(f"当前页面不是确认页: {page}")
        # 尝试全屏搜"开始挑战"
        result = ocr.find_text(img, "开始挑战", min_score=0.3)
        if result:
            cx, cy, score = result
            logger.info(f"全屏找到 [开始挑战] @ ({cx},{cy}) score={score:.3f} → 点击")
            controller.click(cx, cy)
            time.sleep(1)
        else:
            logger.warning("全屏也未找到 [开始挑战]")
            _save_debug_screenshot(img, "step3_no_confirm_btn")
            # 继续走，可能已经在加载了

    # ══════════════════════════════════════════
    # Step 4: 等待加载 → 战斗
    # ══════════════════════════════════════════
    logger.info("─" * 50)
    logger.info("Step 4/6: 等待加载进入战斗")

    loading_start = time.time()
    battle_detected = False

    # 等待最多 30 秒进入战斗
    for attempt in range(60):  # 0.5s * 60 = 30s
        img = ss.capture()
        if img is None:
            time.sleep(0.5)
            continue

        page = get_page_label(img)
        elapsed = time.time() - loading_start

        if page == "BATTLE":
            logger.info(f"✅ 战斗已开始 (加载耗时 {elapsed:.1f}s)")
            _save_debug_screenshot(img, "step4_battle_start")
            battle_detected = True
            break
        elif page == "SETTLEMENT":
            logger.warning(f"直接进入结算页 ({elapsed:.1f}s)，可能战斗已结束")
            _save_debug_screenshot(img, "step4_unexpected_settlement")
            break
        elif page == "CONFIRM":
            logger.warning(f"仍在确认页 ({elapsed:.1f}s)，可能未正确点击")
            if elapsed > 5:
                # 重试点击
                dungeon.confirm(img)
                time.sleep(1)
        elif page == "LOADING(DARK)":
            logger.debug(f"加载中... ({elapsed:.1f}s)")
        elif page == "UNKNOWN":
            logger.debug(f"未知页面 ({elapsed:.1f}s)")
        else:
            logger.info(f"检测到 {page} ({elapsed:.1f}s)")

        if elapsed > 30:
            logger.warning(f"加载超时 (30s)")
            _save_debug_screenshot(img, "step4_loading_timeout")
            # dump 全屏 OCR
            dump = ocr.read(img)
            logger.info(f"超时画面 OCR ({len(dump)} 条):")
            for text, cx, cy, score in dump[:20]:
                logger.info(f"  \"{text}\" @ ({cx},{cy}) score={score:.3f}")
            break

        time.sleep(0.5)

    if not battle_detected:
        logger.warning("未检测到战斗开始，尝试继续（可能已经在战斗中）")
        # 用最后一张截图继续

    # ══════════════════════════════════════════
    # Step 5: 战斗循环 + 检测结算
    # ══════════════════════════════════════════
    logger.info("─" * 50)
    logger.info("Step 5/6: 战斗循环 — 每轮截图检测结算")

    battle_start = time.time()
    battle_action_count = 0
    settlement_detected = False

    # 最多战斗 180 秒
    battle_timeout = 180
    save_interval = 30  # 每 30 秒保存一张截图

    while time.time() - battle_start < battle_timeout:
        img = ss.capture()
        if img is None:
            time.sleep(1)
            continue

        elapsed = time.time() - battle_start

        # 检查结算页
        if is_settlement_page(img):
            logger.info(f"✅ 结算页检测到! (战斗耗时 {elapsed:.1f}s)")
            _save_debug_screenshot(img, "step5_settlement")
            settlement_detected = True
            break

        # 检查是否回到了确认页/副本选择页（战斗可能已结束但没检测到结算文字）
        page = get_page_label(img)
        if page in ("CONFIRM", "DUNGEON_SELECT", "HOME"):
            logger.info(f"检测到 {page} (战斗耗时 {elapsed:.1f}s)，战斗可能已结束")
            settlement_detected = True
            break

        # 战斗中：释放技能
        cycle = battle_action_count % 2
        if cycle == 0:
            controller.use_ultimate()
        else:
            controller.ranged_attack()
        battle_action_count += 1
        logger.info(f"战斗中... ({elapsed:.0f}s) action={battle_action_count}")

        # 定期保存截图
        if int(elapsed) % save_interval < 1 and int(elapsed) > 1:
            _save_debug_screenshot(img, f"step5_battle_{int(elapsed)}s")

        if elapsed >= 3 and battle_action_count % 4 == 0:
            # 每 4 个动作保存一次截图用于诊断
            pass

        time.sleep(1.0)

    if not settlement_detected:
        logger.warning(f"战斗超时 ({battle_timeout}s)，未检测到结算")
        img = ss.capture()
        if img is not None:
            _save_debug_screenshot(img, "step5_battle_timeout")

    # ══════════════════════════════════════════
    # Step 6: 结算页 → 点击继续/结算
    # ══════════════════════════════════════════
    logger.info("─" * 50)
    logger.info("Step 6/6: 结算处理")

    if settlement_detected:
        # 等待结算页稳定
        time.sleep(0.5)
        img = ss.capture()
        if img is not None:
            _diagnose_screenshot(recognizer, img, "step6_settlement")

        # 尝试点击结算按钮
        def try_settlement(img):
            return dungeon.settlement(img)

        ok, _ = _wait_until(ss, try_settlement, timeout=15)
        if ok:
            logger.info("✅ 结算按钮已点击")
            time.sleep(1.5)
            after = ss.capture()
            if after is not None:
                _save_debug_screenshot(after, "step6_after_settlement")
                page = get_page_label(after)
                logger.info(f"结算后页面: {page}")
        else:
            logger.warning("结算按钮未找到，尝试全屏搜索")
            img = ss.capture()
            if img is not None:
                # 全屏搜
                for kw in dungeon.settlement_keywords:
                    result = ocr.find_text(img, kw, min_score=0.3)
                    if result:
                        cx, cy, score = result
                        logger.info(f"全屏找到 [{kw}] @ ({cx},{cy}) score={score:.3f} → 点击")
                        controller.click(cx, cy)
                        ok = True
                        break
            if not ok:
                _save_debug_screenshot(img, "step6_no_settlement")
                logger.warning("结算按钮全屏也找不到，手动确认")
    else:
        logger.warning("未检测到结算页，跳过结算步骤")

    # ══════════════════════════════════════════
    # 完成
    # ══════════════════════════════════════════
    logger.info("=" * 50)
    total_elapsed = time.time() - loading_start
    logger.info(f"测试完成 — 共耗时 {total_elapsed:.0f}s")
    logger.info(f"  战斗动作: {battle_action_count} 次")
    logger.info(f"  结算检测: {'✅' if settlement_detected else '❌'}")
    logger.info("")

    # 最后截图
    final = ss.capture()
    if final is not None:
        _save_debug_screenshot(final, "final")
        page = get_page_label(final)
        logger.info(f"最终页面: {page}")
        logger.info(f"  OCR 文字 ({len(ocr.read(final))} 条)")

    logger.info("=" * 50)
    logger.info("检查 logs/ 下的截图确认各个步骤状态")
    logger.info("如有问题，截图发我调")


if __name__ == "__main__":
    main()