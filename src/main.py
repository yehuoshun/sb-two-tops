"""sb-two-tops 入口 — 副本自动刷取主循环"""

import time
import yaml
import logging
import sys
from pathlib import Path

from src.state_machine import GameState, StateMachine
from src.states import register_handlers
from src.matcher import load_templates, best_match

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sb-two-tops")


def load_config(path: str = "config.yaml") -> dict:
    """加载配置"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    # 加载配置
    config = load_config()
    threshold = config.get("templates", {}).get("threshold", 0.8)
    template_dir = config.get("templates", {}).get("dir", "./templates")

    # 初始化截图
    try:
        from src.capturer import Capturer
        cap = Capturer(config.get("game", {}).get("window_title", "二重螺旋"))
        if not cap.find_game_window():
            logger.error("未找到游戏窗口，请确保游戏正在运行")
            sys.exit(1)
        logger.info(f"已找到游戏窗口")
    except ImportError:
        logger.error("capturer 模块需要 Windows 环境 (pywin32)")
        sys.exit(1)

    # 初始化输入
    from src.inputer import Inputer
    inputer = Inputer(config.get("input", {}).get("method", "sendinput"))

    # 加载模板
    templates = load_templates(template_dir)
    if not templates:
        logger.warning(f"未找到模板文件，请先运行 collect_templates 采集模板")
        logger.info("进入演示模式：仅截图识别，不执行操作")

    # 状态机
    sm = StateMachine(config)
    sm.inputer = inputer
    register_handlers(sm)

    logger.info("=" * 40)
    logger.info("sb-two-tops 启动")
    logger.info(f"目标副本: {config.get('dungeon', {}).get('target', '未设置')}")
    logger.info(f"战斗连招: {config.get('combat', {}).get('combo', 'q')}")
    logger.info(f"循环刷: {'是' if config.get('dungeon', {}).get('loop', True) else '否'}")
    logger.info("=" * 40)

    # 主循环
    try:
        while not sm.should_stop():
            # 截图
            screenshot = cap.capture()
            if screenshot is None:
                logger.warning("截图失败，重试...")
                time.sleep(1)
                continue

            # 识别状态
            if templates:
                state_name, confidence, pos = best_match(screenshot, templates, threshold)
                if state_name:
                    identified = GameState[state_name]
                else:
                    identified = GameState.UNKNOWN
            else:
                identified = GameState.UNKNOWN
                confidence = 0.0

            # 执行状态机
            sm.tick(screenshot, identified, confidence)

            # 每秒检测一次
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        cap.close()
        logger.info("sb-two-tops 已停止")


if __name__ == "__main__":
    main()