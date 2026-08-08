"""
OCR 模块 — RapidOCR 识字

基于 rapidocr，轻量 ONNX 推理。

依赖: pip install rapidocr onnxruntime

API:
    ocr = OCR()
    results = ocr.read(screenshot)
    # results: [(text, (cx, cy), confidence), ...]
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("sb-two-tops.ocr")


class OCR:
    """RapidOCR 识字包装器"""

    def __init__(self):
        self._engine = None

    def _lazy_init(self) -> bool:
        if self._engine is not None:
            return True
        try:
            from rapidocr import RapidOCR
            self._engine = RapidOCR()
            logger.info("RapidOCR 初始化成功")
            return True
        except ImportError:
            logger.error("rapidocr 未安装，请执行: pip install rapidocr onnxruntime")
            return False
        except Exception as e:
            logger.error(f"RapidOCR 初始化失败: {e}")
            return False

    def read(self, image) -> List[Tuple[str, int, int, float]]:
        if not self._lazy_init():
            return []

        try:
            result, _ = self._engine(image)
        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return []

        if not result:
            return []

        parsed = []
        for box, text, score in result:
            if not text or score is None:
                continue
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            cx = int(sum(xs) / len(xs))
            cy = int(sum(ys) / len(ys))
            parsed.append((text.strip(), cx, cy, float(score)))

        parsed.sort(key=lambda x: -x[3])
        return parsed

    def find_text(self, image, target: str, min_score: float = 0.3,
                  region: Optional[Tuple[int, int, int, int]] = None
                  ) -> Optional[Tuple[int, int, float]]:
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