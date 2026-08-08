"""
扼守副本 — 专属配置

继承 BaseDungeon，只需配置参数，无需重写逻辑。
"""

from src.dungeons.base import BaseDungeon


class Dungeon扼守(BaseDungeon):
    name = "扼守"
    max_scroll = 5
    scroll_delta = -120
    scroll_center = (384, 500)
    battle_interval = 2.0
    battle_timeout = 180.0