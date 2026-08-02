"""
页面基类
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
        """检测当前是否为此页面"""
        ...