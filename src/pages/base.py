"""
页面基类 - 所有页面识别器的抽象基类

单一职责：定义页面识别器的接口，具体的页面识别逻辑由子类实现。
"""

import logging
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger("sb-two-tops.pages")


class BasePage(ABC):
    """页面识别器基类"""

    def __init__(self, recognizer, config: dict):
        self.recognizer = recognizer
        self.config = config

    @abstractmethod
    def detect(self, screenshot: np.ndarray) -> bool:
        """检测当前是否为此页面，返回 True/False"""
        ...

    def get_click_point(self, screenshot: np.ndarray, keyword: str) -> tuple | None:
        """通过 OCR 找到文字点击坐标"""
        return self.recognizer.find_click_point(screenshot, keyword)