"""
模板匹配测试 — 验证模板能否在截图中正确匹配
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np


def main():
    # 加载全屏截图
    screenshot = cv2.imread("test_capture.png")
    if screenshot is None:
        print("❌ 无法读取 test_capture.png")
        return

    h, w = screenshot.shape[:2]
    print(f"截图: {w}x{h}")

    # 加载模板
    template_path = "templates/battle/btn_exit_v2.png"
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"❌ 无法读取 {template_path}")
        return

    th, tw = template.shape
    print(f"模板: {tw}x{th}")

    # 全图匹配
    gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    print(f"\n全图匹配: 最高置信度={max_val:.4f} 位置=({max_loc[0]}, {max_loc[1]})")

    # 限定区域匹配（右上角 400x200）
    roi = gray[0:200, w-400:w]
    result_roi = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    _, max_val2, _, max_loc2 = cv2.minMaxLoc(result_roi)
    real_x = (w - 400) + max_loc2[0]
    print(f"右上角区域匹配: 最高置信度={max_val2:.4f} 位置=({real_x}, {max_loc2[1]})")

    # 也试试底部区域
    roi3 = gray[h-200:h, w-400:w]
    result3 = cv2.matchTemplate(roi3, template, cv2.TM_CCOEFF_NORMED)
    _, max_val3, _, max_loc3 = cv2.minMaxLoc(result3)
    real_x3 = (w - 400) + max_loc3[0]
    print(f"右下角区域匹配: 最高置信度={max_val3:.4f} 位置=({real_x3}, {max_loc3[1] + h - 200})")

    # 不同阈值测试
    for threshold in [0.8, 0.7, 0.6, 0.5]:
        loc = np.where(result >= threshold)
        count = len(loc[0])
        print(f"\n阈值={threshold:.1f}: 匹配到 {count} 个位置")
        if count > 0 and count < 10:
            for pt in zip(*loc[:5]):
                print(f"  ({pt[1]}, {pt[0]}) 置信度={result[pt[0], pt[1]]:.4f}")


if __name__ == "__main__":
    main()