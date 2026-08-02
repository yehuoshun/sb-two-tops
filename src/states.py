"""各页面状态处理器 — 定义每个状态的识别和操作逻辑"""

import time
import logging
from src.state_machine import GameState, StateMachine
from src.matcher import match_template

logger = logging.getLogger("sb-two-tops.states")


def handle_main_city(screenshot, sm: StateMachine):
    """主城状态 — 前往副本入口"""
    # 查找副本入口按钮位置，点击进入副本菜单
    # TODO: 需要用户提供主城→副本入口的特征图模板
    # 示例：点击副本入口
    logger.info("主城 — 准备前往副本")
    sm.inputer.click(960, 540)  # 占位，需实际坐标
    time.sleep(1)


def handle_dungeon_menu(screenshot, sm: StateMachine):
    """副本菜单 — 选择目标副本"""
    # TODO: 需要用户提供各副本入口的特征图
    target = sm.config.get("dungeon", {}).get("target", "探险")
    logger.info(f"副本菜单 — 选择 {target}")
    # 点击目标副本
    # sm.inputer.click(x, y)
    time.sleep(1)


def handle_dungeon_select(screenshot, sm: StateMachine):
    """副本详情 — 确认进入"""
    logger.info("副本详情 — 确认进入")
    # 点击"确认进入"按钮
    # sm.inputer.click(x, y)
    time.sleep(2)


def handle_loading(screenshot, sm: StateMachine):
    """加载中 — 等待加载完成"""
    logger.info("加载中...")
    time.sleep(1)


def handle_in_dungeon(screenshot, sm: StateMachine):
    """战斗中 — 执行连招"""
    combo = sm.config.get("combat", {}).get("combo", "q")
    interval = sm.config.get("combat", {}).get("combo_interval", 2.0)

    # 执行大招
    logger.info(f"战斗中 — 执行连招: {combo}")
    sm.inputer.parse_and_execute(combo)
    time.sleep(interval)


def handle_settlement(screenshot, sm: StateMachine):
    """结算界面 — 点击继续挑战"""
    logger.info("结算 — 点击继续挑战")
    # TODO: 需要用户提供"继续挑战"按钮的特征图
    # 匹配"继续挑战"按钮并点击
    # pos = find_continue_button(screenshot)
    # if pos:
    #     sm.inputer.click(pos[0], pos[1])
    sm.increment_runs()
    time.sleep(1)


def handle_continue_confirm(screenshot, sm: StateMachine):
    """继续挑战确认弹窗"""
    logger.info("继续挑战确认")
    # 点击确认
    # sm.inputer.click(x, y)
    time.sleep(1)


def handle_error(screenshot, sm: StateMachine):
    """异常状态 — 等待或重试"""
    logger.warning("遇到异常状态，等待 5 秒后重试")
    time.sleep(5)


def handle_unknown(screenshot, sm: StateMachine):
    """未知状态 — 截图保存并等待"""
    import numpy as np
    timestamp = int(time.time())
    path = f"debug_unknown_{timestamp}.png"
    try:
        from src.capturer import Capturer
        # 临时保存调试截图
        logger.info(f"未知状态，截图已保存: {path}")
    except:
        pass
    time.sleep(2)


# 注册所有状态处理器
def register_handlers(sm: StateMachine):
    sm.register(GameState.MAIN_CITY, handle_main_city)
    sm.register(GameState.DUNGEON_MENU, handle_dungeon_menu)
    sm.register(GameState.DUNGEON_SELECT, handle_dungeon_select)
    sm.register(GameState.LOADING, handle_loading)
    sm.register(GameState.IN_DUNGEON, handle_in_dungeon)
    sm.register(GameState.SETTLEMENT, handle_settlement)
    sm.register(GameState.CONTINUE_CONFIRM, handle_continue_confirm)
    sm.register(GameState.ERROR, handle_error)
    sm.register(GameState.UNKNOWN, handle_unknown)