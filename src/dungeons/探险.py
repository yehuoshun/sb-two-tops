"""
探险副本 — 专属配置
"""

from src.dungeons.base import BaseDungeon


class Dungeon探险(BaseDungeon):
    name = "探险"
    max_scroll = 3
    scroll_delta = -120
    scroll_center = (384, 500)
    battle_interval = 2.0
    battle_timeout = 180.0