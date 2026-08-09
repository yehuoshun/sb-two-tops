"""
OCR 模块 — RapidOCR 识字

基于 rapidocr，轻量 ONNX 推理。
自动处理内存泄漏（bad allocation 时重建引擎）。

依赖: pip install rapidocr onnxruntime
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("sb-two-tops.ocr")


class OCR:
    """RapidOCR 识字包装器"""

    def __init__(self):
        self._engine = self._create_engine()
        self._retries = 0
        self._max_retries = 3

    @staticmethod
    def _create_engine():
        try:
            from rapidocr import RapidOCR
            return RapidOCR()
        except ImportError:
            logger.error("rapidocr 未安装，请执行: pip install rapidocr onnxruntime")
            return None
        except Exception as e:
            logger.error(f"RapidOCR 初始化失败: {e}")
            return None

    def _reinit(self):
        """重建引擎（处理内存泄漏后的 bad allocation）"""
        self._retries += 1
        if self._retries > self._max_retries:
            logger.error(f"OCR 重建超过 {self._max_retries} 次，放弃")
            return False
        logger.info(f"重建 OCR 引擎 ({self._retries}/{self._max_retries})")
        self._engine = self._create_engine()
        return self._engine is not None

    @staticmethod
    def _extract(result):
        """从 RapidOCR 结果中提取文本、坐标、置信度"""
        try:
            texts = result.txts
            boxes = result.boxes
            scores = result.scores
        except AttributeError:
            return None, None, None
        if texts is None:
            return None, None, None
        return texts, boxes, scores

    def read(self, image) -> List[Tuple[str, int, int, float]]:
        if self._engine is None:
            return []

        try:
            result = self._engine(image)
        except Exception as e:
            err_str = str(e)
            logger.error(f"OCR 识别失败: {err_str}")
            if "bad allocation" in err_str:
                if self._reinit():
                    return self.read(image)
            return []

        txts, boxes, scores = self._extract(result)
        if not txts or boxes is None or scores is None:
            return []

        parsed = []
        for text, box, score in zip(txts, boxes, scores):
            if not text or score is None:
                continue
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            cx = int(sum(xs) / len(xs))
            cy = int(sum(ys) / len(ys))
            parsed.append((text.strip(), cx, cy, score))

        parsed.sort(key=lambda x: -x[3])
        return parsed

    def find_text(self, image, target: str, min_score: float = 0.3,
                  region: Optional[Tuple[int, int, int, int]] = None
                  ) -> Optional[Tuple[int, int, float]]:
        rx = ry = 0
        if region:
            rx, ry, rw, rh = region
            h, w = image.shape[:2]
            ry = max(0, ry)
            rx = max(0, rx)
            rh = min(rh, h - ry)
            rw = min(rw, w - rx)
            if rh <= 0 or rw <= 0:
                return None
            image = image[ry:ry + rh, rx:rx + rw].copy()

        results = self.read(image)
        for text, cx, cy, score in results:
            if target in text and score >= min_score:
                if region:
                    cx += rx
                    cy += ry
                return cx, cy, score
        return None