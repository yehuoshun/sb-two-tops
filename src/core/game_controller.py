"""
游戏动作控制器 — 组合 MouseClicker + Keyboard 实现游戏内高级操作

每个游戏可以有独立的 GameController 子类。
与 PostMessage 底层解耦，方便替换实现。
"""

import logging
import time
from typing import Tuple

from src.core.clicker import MouseClicker
from src.core.keyboard import Keyboard

logger = logging.getLogger("sb-two-tops.game_controller")


class GameController:
    """游戏内高级动作控制器

    组合鼠标点击 + 键盘操作，提供游戏语义化的动作接口。
    """

    def __init__(self, clicker: MouseClicker, keyboard: Keyboard):
        self.clicker = clicker
        self.keyboard = keyboard

    # ── 鼠标动作 ──

    def click(self, x: int, y: int, button: str = "left"):
        self.clicker.click(x, y, button)

    def scroll(self, delta: int = -120, x: int = 0, y: int = 0):
        self.clicker.scroll(delta, x, y)

    def attack(self):
        """攻击（左键单击）"""
        self.clicker.mouse_down("left")
        time.sleep(0.03)
        self.clicker.mouse_up("left")
        time.sleep(0.5)

    def attack_heavy(self, duration: float = 0.5):
        """重击/特殊攻击（按住左键）"""
        self.clicker.mouse_down("left")
        time.sleep(duration)
        self.clicker.mouse_up("left")
        time.sleep(0.5)

    def ranged_attack(self):
        """远程武器攻击（右键单击）"""
        self.clicker.mouse_down("right")
        time.sleep(0.03)
        self.clicker.mouse_up("right")
        time.sleep(0.5)

    def ranged_attack_hold(self, duration: float):
        """远程武器按住攻击"""
        self.clicker.mouse_down("right")
        time.sleep(duration)
        self.clicker.mouse_up("right")

    def lock_target(self):
        """锁定目标（中键单击）"""
        self.clicker.mouse_down("middle")
        time.sleep(0.03)
        self.clicker.mouse_up("middle")
        time.sleep(0.5)

    # ── 键盘动作 ──

    def press_key(self, key, down_time: float = 0.05):
        self.keyboard.press_key(key, down_time)

    def hold_key(self, key, duration: float):
        self.keyboard.hold_key(key, duration)

    def use_skill(self):
        """小技能 E"""
        self.keyboard.press_key("E", down_time=0.03)

    def use_ultimate(self):
        """大招 Q"""
        self.keyboard.press_key("Q", down_time=0.03)

    def use_geniemon(self):
        """魔灵技能 Z"""
        self.keyboard.press_key("Z", down_time=0.03)

    def helix_leap(self):
        """螺旋飞跃 4"""
        self.keyboard.press_key("4", down_time=0.03)

    def dodge(self):
        """闪避 SHIFT"""
        self.keyboard.press_key("SHIFT", down_time=0.05)

    def jump(self):
        """跳跃 SPACE"""
        self.keyboard.press_key("SPACE", down_time=0.03)

    def reload(self):
        """换弹 R"""
        self.keyboard.press_key("R", down_time=0.03)

    def move_forward(self, duration: float):
        """向前移动"""
        self.keyboard.hold_key("W", duration)

    def move_back(self, duration: float):
        """向后移动"""
        self.keyboard.hold_key("S", duration)

    def move_left(self, duration: float):
        """向左移动"""
        self.keyboard.hold_key("A", duration)

    def move_right(self, duration: float):
        """向右移动"""
        self.keyboard.hold_key("D", duration)

    # ── 战斗策略 ──

    def battle_loop(self, max_duration: float = 180, interval: float = 2.0):
        """通用战斗循环：每 interval 秒按 Q，持续 max_duration 秒

        Args:
            max_duration: 最大战斗时长（秒）
            interval: 技能释放间隔（秒）

        Returns:
            bool: 是否正常结束（未超时）
        """
        import time as _time
        start = _time.time()
        while _time.time() - start < max_duration:
            self.use_ultimate()
            _time.sleep(interval)
            if _time.time() - start >= max_duration:
                break
            self.ranged_attack()
            _time.sleep(interval)
        return True