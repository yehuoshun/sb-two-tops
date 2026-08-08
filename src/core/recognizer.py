"""
识别模块 - OpenCV 模板匹配

单一职责：仅处理图像识别，不涉及点击或截图管理。
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("sb-two-tops.recognizer")

# 默认检测配置
DETECT_CONFIG = {
    "battle": {
        "features": ["battle_tanxian", "battle_dangqianlunci"],
        "search_box": (0.02, 0.20, 0.30, 0.18),
        "threshold": 170,
        "match_threshold": 0.7,
    },
    "home": {
        "features": ["home_track"],
        "search_box": (0.0, 0.28, 0.15, 0.12),
        "threshold": 170,
        "match_threshold": 0.65,
    },
}


class Recognizer:
    """图像识别器"""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self._template_cache: Dict[str, np.ndarray] = {}

    def load_template(self, name: str, path: str) -> np.ndarray:
        """加载模板图片并缓存"""
        if name in self._template_cache:
            return self._template_cache[name]
        full_path = Path(path)
        if not full_path.is_absolute():
            if not str(full_path).startswith("templates") \
                    and not str(full_path).startswith(str(self.templates_dir)):
                full_path = self.templates_dir / full_path
        if not full_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {full_path}")
        img = cv2.imread(str(full_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"无法读取模板: {full_path}")
        self._template_cache[name] = img
        return img

    def load_all(self, templates_dir: Optional[Path] = None) -> int:
        """批量加载 templates/ 下所有 png 模板

        Args:
            templates_dir: 模板目录，默认 self.templates_dir

        Returns:
            加载的模板数量
        """
        td = templates_dir or self.templates_dir
        count = 0
        if not td.exists():
            return count
        for png in sorted(td.rglob("*.png")):
            name = png.stem
            if name not in self._template_cache:
                img = cv2.imread(str(png), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self._template_cache[name] = img
                    count += 1
        return count

    @staticmethod
    def count_icons_in_row(frame, y_start=0.06, y_end=0.075,
                           x_start=0.65, x_end=0.98,
                           threshold=130) -> int:
        """检测右上角图标行中的图标数量

        用于页面区分：
          主城 ~8 个
          战斗 ~4 个
          副本选择 ~2 个

        不受New标签和红点干扰（只检测图标下半部分）。
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        y1, y2 = int(h * y_start), int(h * y_end)
        x1, x2 = int(w * x_start), int(w * x_end)

        strip = gray[y1:y2, x1:x2]
        _, binary = cv2.threshold(strip, threshold, 255, cv2.THRESH_BINARY)

        v_proj = np.sum(binary > 0, axis=0)
        icon_pos = np.where(v_proj > 3)[0]
        if len(icon_pos) == 0:
            return 0

        gaps = np.diff(icon_pos)
        breaks = np.where(gaps > 5)[0]
        return len(breaks) + 1

    @staticmethod
    def match(
            gray: np.ndarray, template: np.ndarray,
            threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
        """在灰度图中匹配单个模板，返回 (x, y, 置信度) 或 None"""
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            return max_loc[0], max_loc[1], float(max_val)
        return None

    def match_in_region(
            self, gray: np.ndarray, template: np.ndarray,
            region: Tuple[int, int, int, int],
            threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
        """在指定区域内匹配模板，坐标已转换为全图坐标"""
        rx, ry, rw, rh = region
        roi = gray[ry:ry + rh, rx:rx + rw]
        result = self.match(roi, template, threshold)
        if result:
            cx, cy, conf = result
            return cx + rx, cy + ry, conf
        return None

    def detect_page(self, frame: np.ndarray, page_name: str) -> bool:
        """检测指定页面是否匹配当前帧

        Args:
            frame: OpenCV BGR 图像
            page_name: 页面名称 (对应 DETECT_CONFIG 的 key)

        Returns:
            bool: 是否匹配
        """
        config = DETECT_CONFIG.get(page_name)
        if not config:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]

        # 二值化
        _, binary = cv2.threshold(gray, config["threshold"], 255, cv2.THRESH_BINARY)

        # 搜索区域
        sx = int(w * config["search_box"][0])
        sy = int(h * config["search_box"][1])
        sw = int(w * config["search_box"][2])
        sh = int(h * config["search_box"][3])
        search_area = binary[sy:sy + sh, sx:sx + sw]

        for feat_name in config["features"]:
            template = self._template_cache.get(feat_name)
            if template is None:
                return False

            result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val < config["match_threshold"]:
                return False

        return True

    def locate(
            self, screenshot: np.ndarray, template_name: str,
            threshold: float = 0.7
    ) -> Optional[Tuple[int, int, float]]:
        """在截图中定位模板，返回 (中心x, 中心y, 置信度) 或 None

        Args:
            screenshot: 截图（BGR 或灰度）
            template_name: 模板名称（需先 load_template 或 load_all）
            threshold: 匹配阈值，默认 0.7

        Returns:
            (cx, cy, confidence) 或 None
        """
        template = self._template_cache.get(template_name)
        if template is None:
            return None

        if len(screenshot.shape) == 3:
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        else:
            gray = screenshot

        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            return cx, cy, float(max_val)

        return None

    def match_multi(
            self, screenshot: np.ndarray,
            templates: Dict[str, str],
            threshold: float = 0.8
    ) -> Dict[str, Tuple[int, int, float]]:
        """在截图中匹配多个模板，返回 {name: (x, y, 置信度)}"""
        if len(screenshot.shape) == 3:
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        else:
            gray = screenshot

        results = {}
        for name, path in templates.items():
            try:
                tpl = self.load_template(name, path)
                match = self.match(gray, tpl, threshold)
                if match:
                    results[name] = match
            except Exception as e:
                logger.debug(f"模板 {name} 匹配失败: {e}")
        return results