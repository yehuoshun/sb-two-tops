"""
Guard — 扼守 dungeon config

Inherits BaseDungeon, only needs params, no logic overrides.
"""

from src.dungeons.base import BaseDungeon


class DungeonGuard(BaseDungeon):
    name = "扼守"
    max_scroll = 5
    scroll_delta = -480  # 4 格，滚动幅度大一些
    scroll_center = (600, 800)  # 卡片区域中心，光标移过去再滚
    battle_interval = 2.0
    battle_timeout = 180.0

    # 确认页："开始挑战"按钮在右下角 (~1500, ~950)
    confirm_region = (1200, 800, 700, 250)  # x, y, w, h
    confirm_keywords = ["开始挑战", "开始", "挑战", "确认", "进入", "启程"]

    # 结算页："继续挑战"按钮在画面中央偏下
    settlement_region = (300, 600, 1320, 420)
    settlement_keywords = ["继续挑战", "继续", "结算", "返回", "确定", "下一次", "收下", "领取"]