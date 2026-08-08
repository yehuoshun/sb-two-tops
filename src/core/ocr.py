"""
OCR 模块 — EasyOCR 识字

基于 easyocr，Python 3.13 友好，中文识别率高。

依赖: pip install easyocr

API:
    ocr = OCR()
    results = ocr.read(screenshot)
    # results: [(text, (cx, cy), confidence), ...]
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("sb-two-tops.ocr")


class OCR:
    """EasyOCR 识字包装器"""

    def __init__(self):
        self._reader = None

    def _lazy_init(self) -> bool:
        """延迟初始化，只在首次调用时加载"""
        if self._reader is not None:
            return True
        try:
            import easyocr
            # 只加载中英文模型
            self._reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
            logger.info("EasyOCR 初始化成功")
            return True
        except ImportError:
            logger.error("easyocr 未安装，请执行: pip install easyocr")
            return False
        except Exception as e:
            logger.error(f"EasyOCR 初始化失败: {e}")
            return False

    def read(self, image) -> List[Tuple[str, int, int, float]]:
        """对图片进行 OCR，返回识别结果列表

        Args:
            image: numpy array (H, W, 3) BGR 或文件路径

        Returns:
            [(text, cx, cy, confidence), ...] 按置信度降序排列
            失败返回空列表
        """
        if not self._lazy_init():
            return []

        try:
            results = self._reader.readtext(image)
        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return []

        if not results:
            return []

        parsed = []
        for bbox, text, score in results:
            if not text:
                continue
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            cx = int(sum(xs) / len(xs))
            cy = int(sum(ys) / len(ys))
            parsed.append((text.strip(), cx, cy, float(score)))

        parsed.sort(key=lambda x: -x[3])
        return parsed

    def find_text(self, image, target: str, min_score: float = 0.3,
                  region: Optional[Tuple[int, int, int, int]] = None
                  ) -> Optional[Tuple[int, int, float]]:
        """在图片中查找指定文字，返回 (cx, cy, confidence)

        Args:
            image: BGR numpy array
            target: 要查找的文字（如"委托"、"探险"）
            min_score: 最低置信度，默认 0.3
            region: 搜索区域 (x, y, w, h)，不传则搜全图

        Returns:
            (cx, cy, confidence) 或 None
        """
        if region:
            rx, ry, rw, rh = region
            image = image[ry:ry + rh, rx:rx + rw].copy()

        results = self.read(image)
        for text, cx, cy, score in results:
            if target in text and score >= min_score:
                if region:
                    cx += rx
                    cy += ry
                return cx, cy, score
        return None