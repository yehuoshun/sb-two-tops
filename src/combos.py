"""
连招/宏指令解析模块

解析 "eee, qaq" 格式的宏指令并执行。
"""

import time
import re
import logging
from typing import List, Tuple

logger = logging.getLogger("sb-two-tops.combos")

# 虚拟键码映射（PostMessage 用）
VK_MAP = {
    'q': 0x51, 'w': 0x57, 'e': 0x45, 'r': 0x52, 't': 0x54,
    'a': 0x41, 's': 0x53, 'd': 0x44, 'f': 0x46, 'g': 0x47,
    '1': 0x30, '2': 0x31, '3': 0x32, '4': 0x33, '5': 0x34,
    'space': 0x20, 'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
    'tab': 0x09, 'enter': 0x0D,
}


def parse(combo_str: str) -> List[Tuple[str, float]]:
    """
    解析宏指令字符串
    "q" → [("key", "q")]
    "eee, qaq" → [("key", "e"), ("key", "e"), ("key", "e"), ("wait", 0.3), ("key", "q"), ("key", "a"), ("key", "q")]
    "q(hold:1.0)" → [("hold", ("q", 1.0))]
    """
    instructions = []
    parts = [p.strip() for p in combo_str.split(",")]
    for i, part in enumerate(parts):
        if not part:
            continue

        # 逗号分隔 = 短停顿
        if i > 0:
            instructions.append(("wait", 0.3))

        hold_match = re.match(r'^(\w)\(hold:([\d.]+)\)$', part)
        if hold_match:
            key = hold_match.group(1).lower()
            duration = float(hold_match.group(2))
            instructions.append(("hold", (key, duration)))
            continue

        for ch in part:
            if ch.isalpha() or ch.isdigit():
                instructions.append(("key", ch.lower()))

    return instructions


def execute(instructions: List[Tuple], clicker, interval: float = 0.05):
    """执行解析后的指令序列"""
    for inst in instructions:
        action = inst[0]
        data = inst[1]

        if action == "key":
            vk = VK_MAP.get(data)
            if vk:
                clicker.press_key(vk)
            time.sleep(interval)
        elif action == "hold":
            key, duration = data
            vk = VK_MAP.get(key)
            if vk:
                # 按住
                clicker.press_key(vk)  # 简单实现：按下释放
                # TODO: 实际需要 KeyDown + sleep + KeyUp
            time.sleep(duration)
        elif action == "wait":
            time.sleep(data)


def run_combo(combo_str: str, clicker):
    """快捷执行连招"""
    if not combo_str:
        return
    insts = parse(combo_str)
    logger.info(f"执行连招: {combo_str} ({len(insts)}步)")
    execute(insts, clicker)