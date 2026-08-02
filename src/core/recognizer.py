"""
识别模块 - OpenCV 模板匹配 + PaddleOCR 文字识别

单一职责：仅处理图像识别，不涉及点击或截图管理。
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("sb-two-tops.recognizer")

# PaddleOCR 延迟加载
_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_engine = PaddleOCR(lang='ch')
            logger.info("PaddleOCR 引擎初始化完成")
        except ImportError:
            logger.warning("PaddleOCR 未安装，文字识别不可用")
            return None
    return _ocr_engine


class Recognizer:
    """图像识别器"""

    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._template_cache: Dict[str, np.ndarray] = {}

    # ==================== 模板匹配 ====================

    def load_template(self, name: str, path: str) -> np.ndarray:
        """加载模板图片并缓存"""
        if name not in self._template_cache:
            full_path = Path(path)
            if not full_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {full_path}")
            img = cv2.imread(str(full_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"无法读取模板: {full_path}")
            self._template_cache[name] = img
        return self._template_cache[name]

    def match(self, screenshot: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> Optional[Tuple[int, int, float]]:
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
        return None

    def match_multi(self, screenshot: np.ndarray, templates: Dict[str, str], threshold: float = 0.8) -> Dict[str, Tuple[int, int, float]]:
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

    # ==================== OCR 文字识别 ====================

    def ocr(self, screenshot: np.ndarray) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
        """识别截图中的文字，返回 [(文字, (x1,y1,x2,y2), 置信度)]"""
        ocr = _get_ocr()
        if ocr is None:
            return []
        result = ocr.ocr(screenshot, cls=False)
        texts = []
        for line in result:
            if line is None:
                continue
            for item in line:
                box = item[0]
                text = item[1][0]
                confidence = item[1][1]
                x1 = min(p[0] for p in box)
                y1 = min(p[1] for p in box)
                x2 = max(p[0] for p in box)
                y2 = max(p[1] for p in box)
                texts.append((text, (int(x1), int(y1), int(x2), int(y2)), confidence))
        return texts

    def ocr_find_text(self, screenshot: np.ndarray, keyword: str, threshold: float = 0.5) -> Optional[Tuple[int, int, int, int]]:
        """在截图中查找指定关键词，返回 (x1,y1,x2,y2) 或 None"""
        texts = self.ocr(screenshot)
        for text, box, conf in texts:
            if keyword in text and conf >= threshold:
                return box
        return None

    def find_click_point(self, screenshot: np.ndarray, keyword: str, threshold: float = 0.5) -> Optional[Tuple[int, int]]:
        """通过 OCR 找到文字的中心点击坐标"""
        box = self.ocr_find_text(screenshot, keyword, threshold)
        if box:
            cx = (box[0] + box[2]) // 2
            cy = (box[1] + box[3]) // 2
            return (cx, cy)
        return None