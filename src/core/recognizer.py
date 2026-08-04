"""
识别模块 - OpenCV 模板匹配

单一职责：仅处理图像识别，不涉及点击或截图管理。
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger("sb-two-tops.recognizer")


class Recognizer:
    """图像识别器"""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._template_cache: Dict[str, np.ndarray] = {}

    def load_template(self, name: str, path: str) -> np.ndarray:
        """加载模板图片并缓存

        Args:
            name: 缓存键名
            path: 模板文件路径。如果以 templates/ 开头，相对于项目根目录；
                  否则相对于 templates_dir
        """
        if name not in self._template_cache:
            full_path = Path(path)
            if not full_path.is_absolute():
                # 如果路径以 templates/ 开头，直接使用；否则拼到 templates_dir 下
                if not str(full_path).startswith("templates") \
                        and not str(full_path).startswith(str(self.templates_dir)):
                    full_path = self.templates_dir / full_path
            if not full_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {full_path}")
            img = cv2.imread(str(full_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"无法读取模板: {full_path}")
            self._template_cache[name] = img
        return self._template_cache[name]

    @staticmethod
    def match(
            screenshot: np.ndarray, template: np.ndarray,
            threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
        """在截图中匹配单个模板，返回 (x, y, 置信度) 或 None"""
        if len(screenshot.shape) == 3:
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        else:
            gray = screenshot

        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            cx = max_loc[0] + template.shape[1] // 2
            cy = max_loc[1] + template.shape[0] // 2
            return (cx, cy, float(max_val))

    @staticmethod
    def match_in_region(
            screenshot: np.ndarray, template: np.ndarray,
            region: Tuple[int, int, int, int],
            threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
        """在截图的指定区域内匹配模板

        Args:
            screenshot: 全屏截图
            template: 模板图片
            region: (x, y, w, h) 搜索区域（相对于截图左上角）
            threshold: 匹配阈值

        Returns:
            (x, y, 置信度) — 坐标已转换为全屏坐标
        """
        rx, ry, rw, rh = region
        roi = screenshot[ry:ry + rh, rx:rx + rw]
        result = Recognizer.match(roi, template, threshold)
        if result:
            cx, cy, conf = result
            return (cx + rx, cy + ry, conf)
        return None

    def match_multi(
            self, screenshot: np.ndarray,
            templates: Dict[str, str],
            threshold: float = 0.8
    ) -> Dict[str, Tuple[int, int, float]]:
        """在截图中匹配多个模板，返回 {name: (x, y, 置信度)}"""
        results = {}
        for name, path in templates.items():
            try:
                tpl = self.load_template(name, path)
                match = self.match(screenshot, tpl, threshold)
                if match:
                    results[name] = match
            except Exception as e:
                logger.debug(f"模板 {name} 匹配失败: {e}")
        return results