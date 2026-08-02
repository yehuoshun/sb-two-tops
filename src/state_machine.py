"""状态机引擎 — 副本自动流程核心"""

import time
import logging
from enum import Enum, auto
from typing import Dict, Optional, Callable

logger = logging.getLogger("sb-two-tops")


class GameState(Enum):
    """游戏页面状态"""
    UNKNOWN = auto()        # 未识别
    MAIN_CITY = auto()      # 主城
    DUNGEON_MENU = auto()   # 副本菜单
    DUNGEON_SELECT = auto() # 副本选择
    CONFIRM_ENTER = auto()  # 确认进入
    LOADING = auto()        # 加载中
    IN_DUNGEON = auto()     # 战斗中
    SETTLEMENT = auto()     # 结算界面
    CONTINUE_CONFIRM = auto()  # 继续挑战确认
    ERROR = auto()          # 异常状态


class StateMachine:
    """状态机 — 管理页面流转、截图识别、操作执行"""

    def __init__(self, config: dict):
        self.config = config
        self.current_state = GameState.UNKNOWN
        self.last_state = GameState.UNKNOWN
        self.state_start_time = time.time()
        self.run_count = 0
        self.max_runs = config.get("dungeon", {}).get("max_runs", 0)
        self.loop = config.get("dungeon", {}).get("loop", True)

        # 状态停留计时（防止卡死）
        self.state_timeouts = {
            GameState.LOADING: 30,       # 加载最多等30秒
            GameState.IN_DUNGEON: 600,   # 战斗最多等10分钟
            GameState.SETTLEMENT: 15,    # 结算最多等15秒
        }

        # 状态处理器注册
        self.handlers: Dict[GameState, Callable] = {}

    def register(self, state: GameState, handler: Callable):
        """注册指定状态的处理函数"""
        self.handlers[state] = handler

    def tick(self, screenshot, identified_state: GameState, confidence: float):
        """执行一轮状态机"""
        self.last_state = self.current_state
        self.current_state = identified_state

        # 状态切换时重置计时
        if self.current_state != self.last_state:
            self.state_start_time = time.time()
            logger.info(f"状态切换: {self.last_state.name} → {self.current_state.name} (置信度: {confidence:.2f})")

        # 检查超时
        if self._is_timeout():
            logger.warning(f"状态 {self.current_state.name} 超时，进入 ERROR")
            self.current_state = GameState.ERROR

        # 执行处理器
        handler = self.handlers.get(self.current_state)
        if handler:
            handler(screenshot, self)
        else:
            logger.debug(f"状态 {self.current_state.name} 无处理器，跳过")

    def _is_timeout(self) -> bool:
        """检查当前状态是否超时"""
        timeout = self.state_timeouts.get(self.current_state)
        if timeout is None:
            return False
        elapsed = time.time() - self.state_start_time
        return elapsed > timeout

    def should_stop(self) -> bool:
        """是否应该停止"""
        if self.max_runs > 0 and self.run_count >= self.max_runs:
            logger.info(f"达到最大运行次数 {self.max_runs}，停止")
            return True
        return False

    def increment_runs(self):
        self.run_count += 1
        logger.info(f"已完成 {self.run_count} 次")