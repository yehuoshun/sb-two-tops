"""图像匹配模块 — 基于 OpenCV 模板匹配"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_template(path: str) -> Optional[np.ndarray]:
    """加载模板图像（灰度）"""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return img


def load_templates(template_dir: str) -> Dict[str, List[Tuple[str, np.ndarray]]]:
    """
    从模板目录加载所有模板
    目录结构: templates/<state_name>/<variant>.png
    返回: { "MAIN_CITY": [("variant1", template_arr), ...], ... }
    """
    base = Path(template_dir)
    if not base.exists():
        return {}

    result = {}
    for state_dir in sorted(base.iterdir()):
        if not state_dir.is_dir():
            continue
        state_name = state_dir.name
        templates = []
        for tpl_file in sorted(state_dir.glob("*.png")):
            tpl = load_template(str(tpl_file))
            if tpl is not None:
                templates.append((tpl_file.stem, tpl))
        if templates:
            result[state_name] = templates
    return result


def match_template(
    screenshot: np.ndarray,
    template: np.ndarray,
    threshold: float = 0.8
) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
    """
    在截图中匹配单个模板
    返回: (是否匹配, 置信度, 匹配位置 (x, y))
    """
    if screenshot is None or template is None:
        return False, 0.0, None

    # 转灰度
    if len(screenshot.shape) == 3:
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)
    else:
        gray = screenshot

    # 模板匹配
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        return True, float(max_val), (int(max_loc[0]), int(max_loc[1]))
    return False, float(max_val), None


def best_match(
    screenshot: np.ndarray,
    templates: Dict[str, List[Tuple[str, np.ndarray]]],
    threshold: float = 0.8
) -> Tuple[Optional[str], float, Optional[Tuple[int, int]]]:
    """
    在截图中匹配所有状态模板，返回最佳匹配
    返回: (状态名, 置信度, 位置)
    """
    best_state = None
    best_score = 0.0
    best_pos = None

    for state_name, tpl_list in templates.items():
        for _, tpl in tpl_list:
            matched, score, pos = match_template(screenshot, tpl, threshold)
            if matched and score > best_score:
                best_score = score
                best_state = state_name
                best_pos = pos

    return best_state, best_score, best_pos